"""
MCP Registry Control Plane + Policy Gateway

- Registry APIs: catalog, connector detail, health
- Gateway APIs: policy evaluate, invoke (stub), approvals, budgets, audit
- Dashboard: catalog / lab / ops / audit pages
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .adapters import github_write
from .approvals import ApprovalService
from .audit import AuditStore
from .auth import Principal, get_principal, idp, require_roles
from .control_plane import ControlPlaneStore
from .db import db
from .models import ApprovalCreateRequest, ApprovalDecision, InvokeRequest, PolicyDecision
from .otel_setup import configure_telemetry, record_invoke, record_policy, span_ctx
from .policy import PolicyEngine
from .registry import Registry
from .security import BudgetTracker, args_hash, new_correlation_id, redact_payload

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "dashboard"

app = FastAPI(
    title="Agent-Ops MCP Registry Gateway",
    version="0.5.0",
    description="Control plane (registry) + policy gateway for certified MCP connectors.",
)

registry = Registry()
approvals = ApprovalService()
audit = AuditStore()
budgets = BudgetTracker()
control_plane = ControlPlaneStore()
policy = PolicyEngine(registry, approvals, control_plane)

configure_telemetry(app)

if (DASHBOARD / "static").exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD / "static")), name="static")
templates = Jinja2Templates(directory=str(DASHBOARD / "templates"))


@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "connectors": len(registry.connectors),
        "audit_events": len(audit.events),
        "auth_mode": idp.mode,
        "database_rls": db.enabled,
        "persistence": "postgres" if db.enabled else "memory",
        "mcp_endpoint": "/mcp",
        "mcp_transport": "streamable_http",
        "version": app.version,
    }


@app.get("/api/v1/auth/config")
def auth_config():
    """Public auth metadata (no secrets)."""
    return idp.public_config()


@app.get("/api/v1/auth/whoami")
def whoami(principal: Principal = Depends(get_principal)):
    return {
        "subject": principal.subject,
        "org_id": principal.org_id,
        "tenant_id": principal.tenant_id,
        "roles": principal.roles,
        "email": principal.email,
    }


@app.post("/api/v1/auth/dev-token")
def issue_dev_token(body: dict):
    """Issue a short-lived HS256 token for AUTH_MODE=dev. Disabled in oidc mode."""
    if idp.mode == "oidc":
        raise HTTPException(403, "dev tokens disabled in oidc mode")
    token = idp.issue_dev_token(
        subject=body.get("subject", "user:dev"),
        org_id=body.get("org_id", "org_local"),
        tenant_id=body.get("tenant_id", "tenant_local"),
        roles=body.get("roles", ["operator", "approver"]),
        email=body.get("email"),
        ttl_seconds=int(body.get("ttl_seconds", 3600)),
    )
    return {"access_token": token, "token_type": "bearer"}


# ── Spec aliases: gateway service-to-service API (§5.6) ───────────────────


@app.post("/gateway/v1/tools/authorize")
def gateway_authorize(req: InvokeRequest, principal: Principal = Depends(get_principal)):
    """Authorize a prospective tool call without executing the connector."""
    req.actor = req.actor or principal.subject
    req.org_id = principal.org_id
    req.tenant_id = principal.tenant_id
    result = policy.evaluate(req)
    return {
        "allow": result.decision == PolicyDecision.allow,
        "decision": result.decision.value,
        "reason": result.reason,
        "correlation_id": result.correlation_id,
        "args_hash": result.args_hash,
        "approval_required": result.decision == PolicyDecision.require_approval,
    }


@app.post("/gateway/v1/tools/invoke")
def gateway_invoke(req: InvokeRequest, principal: Principal = Depends(get_principal)):
    """Alias of /api/v1/gateway/invoke — never accepts raw connector URLs from clients."""
    return invoke(req, principal)


@app.post("/gateway/v1/redact")
def gateway_redact(body: dict):
    payload = body.get("payload", body)
    safe, count = redact_payload(payload)
    return {"payload": safe, "redaction_count": count}


@app.post("/gateway/v1/egress/check")
def gateway_egress_check(body: dict):
    """Allow only domains present on the connector allowlist (or empty = deny live egress)."""
    url = str(body.get("url") or "")
    allowlist = body.get("allowlist") or []
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    if not host:
        return {"allow": False, "reason": "missing host"}
    if host in {"127.0.0.1", "localhost", "metadata.google.internal"} or host.startswith("169.254."):
        return {"allow": False, "reason": "blocked private/metadata host"}
    if allowlist and host not in [str(d).lower() for d in allowlist]:
        return {"allow": False, "reason": "host not on egress allowlist"}
    if not allowlist:
        return {"allow": False, "reason": "empty allowlist fails closed for live egress"}
    return {"allow": True, "host": host}


@app.get("/api/v1/catalog/views")
def catalog_saved_views():
    """Built-in saved catalog views (spec §2.2)."""
    return {
        "views": [
            {
                "id": "certified-readonly-prod",
                "label": "Certified, read-only, production-active",
                "query": "operation=read&trustTier=3,4&environment=production&health=healthy,degraded",
            },
            {
                "id": "write-requires-approval",
                "label": "Write-capable connectors requiring approval",
                "query": "operation=write,delete,external_communication",
            },
            {
                "id": "quarantined",
                "label": "Quarantined/revoked versions",
                "query": "certification_state=quarantined",
            },
            {
                "id": "staging-candidates",
                "label": "Staging candidates",
                "query": "trustTier=2,3&environment=staging",
            },
            {
                "id": "cert-expiring",
                "label": "Production connectors with certification pressure",
                "query": "trustTier=3,4&environment=production&sort=rank",
            },
        ]
    }


@app.post("/api/v1/policy/simulate")
def policy_simulate(req: InvokeRequest, principal: Principal = Depends(get_principal)):
    """Evaluate proposed invocation without executing (spec §5.2)."""
    return evaluate_policy(req, principal)


@app.post("/api/v1/approvals/{request_id}/consume")
def consume_approval(request_id: str, body: dict, principal: Principal = Depends(require_roles("admin", "operator"))):
    """Gateway-only atomic consume of an approved grant (spec §7.3)."""
    try:
        return approvals.consume(
            request_id,
            args_hash=body["args_hash"],
            idempotency_key=body["idempotency_key"],
        )
    except KeyError:
        raise HTTPException(404, "not found") from None
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


# ── Registry (control plane) ─────────────────────────────────────────────


@app.get("/api/v1/connectors")
def list_connectors(
    category: str | None = None,
    trust_tier: str | None = None,
    trustTier: str | None = None,
    capability: str | None = None,
    operation: str | None = None,
    environment: str | None = None,
    certification_state: str | None = None,
    transport: str | None = None,
    data_classification: str | None = None,
    health: str | None = None,
    owner: str | None = None,
    q: str | None = None,
    sort: str | None = None,
    view: str | None = Query(None, description="table|cards — advisory for UI clients"),
    limit: int = Query(100, ge=1, le=500),
    cursor: str | None = Query(None, description="pagination cursor (last slug from prior page)"),
):
    """Multi-filter catalog for 100+ connectors. Cursor-paginated; comma-separated multi-value filters supported."""
    items = registry.list(
        category=category,
        trust_tier=trust_tier or trustTier,
        capability=capability,
        operation=operation,
        environment=environment,
        certification_state=certification_state,
        transport=transport,
        data_classification=data_classification,
        health=health,
        owner=owner,
        q=q,
        sort=sort,
    )
    start = 0
    if cursor:
        for i, c in enumerate(items):
            if c.slug == cursor:
                start = i + 1
                break
    page = items[start : start + limit]
    next_cursor = page[-1].slug if start + limit < len(items) and page else None
    return {
        "count": len(items),
        "returned": len(page),
        "limit": limit,
        "next_cursor": next_cursor,
        "view": view or "table",
        "filters": {
            "category": category,
            "trust_tier": trust_tier or trustTier,
            "operation": operation or capability,
            "environment": environment,
            "health": health,
            "sort": sort or "rank",
        },
        "connectors": [c.model_dump() for c in page],
    }


@app.get("/api/v1/connectors/{slug}")
def get_connector(slug: str):
    conn = registry.get(slug)
    if not conn:
        raise HTTPException(404, "connector not found")
    return conn.model_dump()


@app.post("/api/v1/connectors/reload")
def reload_connectors():
    registry.reload()
    return {"reloaded": len(registry.connectors)}


@app.get("/api/v1/connectors/{slug}/versions/{version}")
def get_connector_version(slug: str, version: str):
    conn = registry.get(slug)
    if not conn or conn.version != version:
        raise HTTPException(404, "connector version not found")
    data = conn.model_dump()
    data["quarantined"] = control_plane.is_quarantined(slug, version)
    data["activations"] = [
        a for a in control_plane.list_activations() if a["slug"] == slug and a["version"] == version
    ]
    return data


@app.post("/api/v1/connectors/{slug}/versions/{version}/test-runs")
def create_test_run(slug: str, version: str, suite: str = "full", org_id: str = "org_local"):
    conn = registry.get(slug)
    if not conn or conn.version != version:
        raise HTTPException(404, "connector version not found")
    return control_plane.create_test_run(slug, version, suite, org_id)


@app.post("/api/v1/connectors/{slug}/versions/{version}/lab-runs")
def create_ephemeral_lab_run(slug: str, version: str, suite: str = "full"):
    """Spin ephemeral sandbox via Node runner; return HMAC-signed evidence paths."""
    import subprocess
    from pathlib import Path

    conn = registry.get(slug)
    if not conn or conn.version != version:
        raise HTTPException(404, "connector version not found")
    script = Path(__file__).resolve().parents[2] / "scripts" / "ephemeral-lab-runner.mjs"
    proc = subprocess.run(
        ["node", str(script), slug, suite],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 2):
        raise HTTPException(500, f"lab runner failed: {proc.stderr or proc.stdout}")
    try:
        summary = __import__("json").loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"invalid lab runner output: {proc.stdout}") from exc
    # Also record in control-plane test runs
    record = control_plane.create_test_run(slug, version, suite)
    record["ephemeral"] = summary
    record["status"] = "passed" if summary.get("ok") else "failed"
    return record


@app.get("/api/v1/test-runs/{run_id}")
def get_test_run(run_id: str):
    run = control_plane.get_test_run(run_id)
    if not run:
        raise HTTPException(404, "test run not found")
    return run


@app.post("/api/v1/activations")
def create_activation(body: dict):
    required = ["slug", "version", "project_id", "environment"]
    for key in required:
        if key not in body:
            raise HTTPException(400, f"missing {key}")
    conn = registry.get(body["slug"])
    if not conn or conn.version != body["version"]:
        raise HTTPException(404, "connector version not found")
    if control_plane.is_quarantined(body["slug"], body["version"]):
        raise HTTPException(409, "connector version is quarantined")
    if conn.certification_state not in {"certified", "in_lab", "reviewed"} and body["environment"] == "production":
        raise HTTPException(400, "production activation requires certified connector")
    return control_plane.request_activation(body)


@app.post("/api/v1/activations/{activation_id}/approve")
def approve_activation(activation_id: str, body: dict):
    try:
        return control_plane.approve_activation(
            activation_id,
            approver=body.get("approver", "user:approver"),
            approve=body.get("approve", True),
        )
    except KeyError:
        raise HTTPException(404, "activation not found") from None
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/v1/activations")
def list_activations(project_id: str | None = None):
    return {"activations": control_plane.list_activations(project_id)}


@app.post("/api/v1/activations/{activation_id}/disable")
def disable_activation(activation_id: str, body: dict, principal: Principal = Depends(require_roles("admin", "approver", "operator"))):
    try:
        return control_plane.disable_activation(
            activation_id,
            actor=body.get("actor") or principal.subject,
            reason=body.get("reason", "disabled by operator"),
        )
    except KeyError:
        raise HTTPException(404, "activation not found") from None


@app.post("/api/v1/activations/{activation_id}/renew")
def renew_activation(activation_id: str, body: dict, principal: Principal = Depends(require_roles("admin", "approver", "operator"))):
    try:
        return control_plane.renew_activation(
            activation_id,
            actor=body.get("actor") or principal.subject,
            days=int(body.get("days", 90)),
        )
    except KeyError:
        raise HTTPException(404, "activation not found") from None
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/v1/connectors/{slug}/quarantine")
def quarantine_connector(slug: str, body: dict):
    conn = registry.get(slug)
    if not conn:
        raise HTTPException(404, "connector not found")
    version = body.get("version", conn.version)
    reason = body.get("reason", "emergency quarantine")
    actor = body.get("actor", "user:secops")
    record = control_plane.quarantine(slug, version, reason, actor)
    # Reflect in in-memory manifest certification state for catalog UX
    conn.certification_state = "quarantined"
    return record


@app.post("/api/v1/connectors/{slug}/versions/{version}/unquarantine")
@app.post("/api/v1/connectors/{slug}/unquarantine")
def unquarantine_connector(slug: str, body: dict, version: str | None = None):
    """Lift quarantine with recorded reason (spec §5.1)."""
    conn = registry.get(slug)
    if not conn:
        raise HTTPException(404, "connector not found")
    ver = version or body.get("version") or conn.version
    reason = body.get("reason", "quarantine lifted after review")
    actor = body.get("actor", "user:secops")
    try:
        record = control_plane.unquarantine(slug, ver, reason, actor)
    except KeyError:
        raise HTTPException(404, "active quarantine not found") from None
    # Restore certification state from last cert decision or reviewed default
    decisions = control_plane.list_certification_decisions(slug)
    last = next((d for d in decisions if d["version"] == ver), None)
    if last and last["decision"] == "certify":
        conn.certification_state = "certified"
    elif last and last["decision"] == "fail":
        conn.certification_state = "failed"
    else:
        conn.certification_state = "reviewed"
    return record


@app.get("/api/v1/quarantines")
def list_quarantines(active_only: bool = True):
    return {"quarantines": control_plane.list_quarantines(active_only=active_only)}


@app.get("/api/v1/metrics/connectors")
def metrics_connectors():
    summary = ops_summary()
    by_connector: dict[str, dict] = {}
    for event in audit.events:
        slug = event.get("connector_slug") or "unknown"
        bucket = by_connector.setdefault(
            slug,
            {"calls": 0, "allow": 0, "deny": 0, "require_approval": 0, "latencies": []},
        )
        bucket["calls"] += 1
        decision = event.get("policy_decision")
        if decision in bucket:
            bucket[decision] += 1
        if event.get("latency_ms") is not None:
            bucket["latencies"].append(event["latency_ms"])
    metrics = []
    for slug, bucket in by_connector.items():
        lats = sorted(bucket["latencies"])
        p95 = lats[int(len(lats) * 0.95)] if lats else 0
        metrics.append(
            {
                "slug": slug,
                "calls": bucket["calls"],
                "allow": bucket["allow"],
                "deny": bucket["deny"],
                "require_approval": bucket["require_approval"],
                "p95_latency_ms": p95,
                "quarantined": control_plane.is_quarantined(
                    slug, registry.get(slug).version if registry.get(slug) else ""
                ),
            }
        )
    return {"summary": summary, "connectors": metrics}


@app.get("/api/v1/audit/invocations")
def audit_invocations(limit: int = Query(100, ge=1, le=1000), correlation_id: str | None = None):
    return {"invocations": audit.list(limit=limit, correlation_id=correlation_id)}


@app.get("/api/v1/policies/{policy_key}/decisions")
def policy_decisions(policy_key: str):
    return {"policy_key": policy_key, "decisions": control_plane.list_policy_decisions(policy_key)}


# ── Gateway (enforcement) ────────────────────────────────────────────────


@app.post("/api/v1/policy/evaluate")
def evaluate_policy(req: InvokeRequest, principal: Principal = Depends(get_principal)):
    req.actor = req.actor or principal.subject
    req.org_id = principal.org_id
    req.tenant_id = principal.tenant_id
    with span_ctx("policy.evaluate", connector=req.connector_slug, tool=req.tool_name):
        result = policy.evaluate(req)
    record_policy(result.decision.value, req.connector_slug, req.tool_name)
    control_plane.log_policy_decision(
        policy_key=f"{req.connector_slug}.{req.tool_name}",
        decision=result.decision.value,
        correlation_id=result.correlation_id,
        reason=result.reason,
        input_data={
            "actor": req.actor,
            "org_id": principal.org_id,
            "environment": req.environment.value,
            "args_hash": result.args_hash,
        },
    )
    audit.append(
        {
            "correlation_id": result.correlation_id,
            "actor_id": req.actor,
            "organization": req.org_id,
            "tenant": req.tenant_id,
            "project": req.project_id,
            "environment": req.environment.value,
            "connector_slug": req.connector_slug,
            "tool_name": req.tool_name,
            "normalized_arguments_hash": result.args_hash,
            "policy_decision": result.decision.value,
            "approval_id": None,
            "idempotency_key": req.idempotency_key,
            "latency_ms": 0,
            "outcome": result.reason,
            "response_hash": None,
            "evidence_uri": None,
            "redaction_count": 0,
        }
    )
    return result.model_dump()


@app.post("/api/v1/gateway/invoke")
def invoke(req: InvokeRequest, principal: Principal = Depends(get_principal)):
    """Evaluate policy, optionally require grant, invoke adapter, redact, audit."""
    started = time.time()
    req.actor = req.actor or principal.subject
    req.org_id = principal.org_id
    req.tenant_id = principal.tenant_id
    run_id = budgets.begin(req.run_id)
    ok, budget_msg = budgets.charge(run_id)
    if not ok:
        raise HTTPException(429, budget_msg)

    with span_ctx("gateway.invoke", connector=req.connector_slug, tool=req.tool_name, org=principal.org_id):
        result = policy.evaluate(req)
        record_policy(result.decision.value, req.connector_slug, req.tool_name)
        if result.decision == PolicyDecision.require_approval:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "approval_required",
                    "policy": result.model_dump(),
                    "hint": "Create an approval request, obtain a signed grant, retry with approval_grant.",
                },
            )
        if result.decision != PolicyDecision.allow:
            latency_ms = int((time.time() - started) * 1000)
            record_invoke(req.connector_slug, req.tool_name, "deny", latency_ms)
            audit.append(
                {
                    "correlation_id": result.correlation_id,
                    "actor_id": req.actor,
                    "organization": req.org_id,
                    "tenant": req.tenant_id,
                    "project": req.project_id,
                    "environment": req.environment.value,
                    "connector_slug": req.connector_slug,
                    "connector_version": registry.get(req.connector_slug).version if registry.get(req.connector_slug) else None,
                    "tool_name": req.tool_name,
                    "normalized_arguments_hash": result.args_hash,
                    "policy_decision": result.decision.value,
                    "approval_id": None,
                    "idempotency_key": req.idempotency_key,
                    "latency_ms": latency_ms,
                    "outcome": result.reason,
                    "response_hash": None,
                    "evidence_uri": None,
                    "redaction_count": 0,
                }
            )
            raise HTTPException(403, result.reason)

        try:
            if req.connector_slug == github_write.SLUG and req.tool_name == github_write.TOOL_NAME:
                raw = github_write.create_pull_request(
                    arguments=req.arguments,
                    environment=req.environment.value,
                )
            else:
                raw = {
                    "ok": True,
                    "connector": req.connector_slug,
                    "tool": req.tool_name,
                    "echo_args": req.arguments,
                    "note": "stub invoke — replace with certified connector adapter",
                }
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(400, str(exc)) from exc

        safe, redactions = redact_payload(raw)
        latency_ms = int((time.time() - started) * 1000)
        record_invoke(req.connector_slug, req.tool_name, "ok", latency_ms)
        event = audit.append(
            {
                "correlation_id": result.correlation_id,
                "actor_id": req.actor,
                "organization": req.org_id,
                "tenant": req.tenant_id,
                "project": req.project_id,
                "environment": req.environment.value,
                "connector_slug": req.connector_slug,
                "connector_version": registry.get(req.connector_slug).version if registry.get(req.connector_slug) else None,
                "tool_name": req.tool_name,
                "normalized_arguments_hash": result.args_hash,
                "policy_decision": result.decision.value,
                "approval_id": None,
                "idempotency_key": req.idempotency_key,
                "latency_ms": latency_ms,
                "outcome": "ok",
                "response_hash": args_hash({"response": safe}),
                "evidence_uri": f"audit://events/{result.correlation_id}",
                "redaction_count": redactions,
            }
        )
        return {
            "correlation_id": result.correlation_id,
            "result": safe,
            "redaction_count": redactions,
            "audit_event_hash": event["event_hash"],
            "latency_ms": latency_ms,
            "run_id": run_id,
            "org_id": principal.org_id,
        }


@app.post("/api/v1/approvals")
def create_approval(
    body: ApprovalCreateRequest,
    principal: Principal = Depends(require_roles("operator", "approver", "admin")),
):
    body.actor = body.actor or principal.subject
    body.org_id = principal.org_id
    body.tenant_id = principal.tenant_id
    if not body.correlation_id:
        body.correlation_id = new_correlation_id()
    record = approvals.create_request(body)
    audit.append(
        {
            "correlation_id": body.correlation_id,
            "actor_id": body.actor,
            "organization": body.org_id,
            "tenant": body.tenant_id,
            "project": body.project_id,
            "environment": body.environment.value,
            "connector_slug": body.connector_slug,
            "connector_version": body.connector_version,
            "tool_name": body.tool_name,
            "normalized_arguments_hash": record["args_hash"],
            "policy_decision": PolicyDecision.require_approval.value,
            "approval_id": record["id"],
            "idempotency_key": body.idempotency_key,
            "latency_ms": 0,
            "outcome": "approval_requested",
            "response_hash": None,
            "evidence_uri": None,
            "redaction_count": 0,
        }
    )
    return record


@app.get("/api/v1/approvals")
def list_approvals(principal: Principal = Depends(get_principal)):
    return {"approvals": list(approvals.requests.values()), "org_id": principal.org_id}


@app.get("/api/v1/approvals/{request_id}")
def get_approval(request_id: str, principal: Principal = Depends(get_principal)):
    req = approvals.requests.get(request_id)
    if not req:
        raise HTTPException(404, "not found")
    return req


@app.post("/api/v1/approvals/{request_id}/decide")
def decide_approval(
    request_id: str,
    body: ApprovalDecision,
    principal: Principal = Depends(require_roles("approver", "admin")),
):
    try:
        record = approvals.decide(
            request_id,
            body.approver or principal.subject,
            body.approve,
            body.note,
            step_up_verified=body.step_up_verified,
        )
    except KeyError:
        raise HTTPException(404, "not found") from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    audit.append(
        {
            "correlation_id": record["correlation_id"],
            "actor_id": body.approver or principal.subject,
            "organization": record["org_id"],
            "tenant": record["tenant_id"],
            "project": record["project_id"],
            "environment": record["environment"],
            "connector_slug": record["connector_slug"],
            "connector_version": record["connector_version"],
            "tool_name": record["tool_name"],
            "normalized_arguments_hash": record["args_hash"],
            "policy_decision": (
                PolicyDecision.allow.value
                if record["status"] == "approved"
                else PolicyDecision.deny.value
                if record["status"] == "denied"
                else PolicyDecision.require_approval.value
            ),
            "approval_id": record["id"],
            "idempotency_key": record["idempotency_key"],
            "latency_ms": 0,
            "outcome": record["status"],
            "response_hash": None,
            "evidence_uri": None,
            "redaction_count": 0,
        }
    )
    return record


@app.get("/api/v1/audit/events")
def list_audit_events(limit: int = Query(100, ge=1, le=1000), correlation_id: str | None = None):
    return {"events": audit.list(limit=limit, correlation_id=correlation_id)}


@app.get("/api/v1/ops/summary")
def ops_summary():
    events = audit.events
    total = len(events)
    allows = sum(1 for e in events if e.get("policy_decision") == "allow")
    denies = sum(1 for e in events if e.get("policy_decision") == "deny")
    approvals = sum(1 for e in events if e.get("policy_decision") == "require_approval")
    latencies = [e["latency_ms"] for e in events if e.get("latency_ms")]
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
    return {
        "tool_calls": total,
        "allow": allows,
        "deny": denies,
        "require_approval": approvals,
        "p95_latency_ms": p95,
        "connectors": len(registry.connectors),
        "pending_approvals": sum(1 for a in approvals_pending()),
    }


def approvals_pending():
    return [a for a in approvals.requests.values() if a["status"] == "pending"]


# ── Dashboard pages ──────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "page": "catalog",
            "connectors": registry.list(),
            "summary": ops_summary(),
        },
    )


@app.get("/connectors/{slug}", response_class=HTMLResponse)
def dashboard_connector_detail(request: Request, slug: str):
    conn = registry.get(slug)
    if not conn:
        raise HTTPException(404, "connector not found")
    events = [e for e in audit.list(limit=200) if e.get("connector_slug") == slug][:25]
    return templates.TemplateResponse(
        request,
        "detail.html",
        {
            "page": "catalog",
            "connector": conn,
            "quarantined": control_plane.is_quarantined(slug, conn.version),
            "activations": [
                a for a in control_plane.list_activations() if a["slug"] == slug and a["version"] == conn.version
            ],
            "events": events,
        },
    )


@app.get("/lab", response_class=HTMLResponse)
def dashboard_lab(request: Request):
    return templates.TemplateResponse(
        request,
        "lab.html",
        {"page": "lab", "connectors": registry.list()},
    )


@app.get("/ops", response_class=HTMLResponse)
def dashboard_ops(request: Request):
    return templates.TemplateResponse(
        request,
        "ops.html",
        {"page": "ops", "summary": ops_summary(), "events": audit.list(limit=25)},
    )


@app.get("/audit", response_class=HTMLResponse)
def dashboard_audit(request: Request):
    return templates.TemplateResponse(
        request,
        "audit.html",
        {"page": "audit", "events": audit.list(limit=100)},
    )


@app.get("/approvals", response_class=HTMLResponse)
def dashboard_approvals(request: Request):
    return templates.TemplateResponse(
        request,
        "approvals.html",
        {
            "page": "approvals",
            "approvals": list(approvals.requests.values()),
        },
    )


@app.get("/admin/quarantine", response_class=HTMLResponse)
def dashboard_quarantine(request: Request):
    active = [q for q in control_plane.quarantines.values() if q.get("active")]
    return templates.TemplateResponse(
        request,
        "quarantine.html",
        {"page": "quarantine", "quarantines": active},
    )


# ── Phase C — production lifecycle hardening ───────────────────────────────


@app.post("/api/v1/connectors/{slug}/versions/{version}/certification-decisions")
def create_certification_decision(
    slug: str,
    version: str,
    body: dict,
    principal: Principal = Depends(require_roles("admin", "approver")),
):
    conn = registry.get(slug)
    if not conn or conn.version != version:
        raise HTTPException(404, "connector version not found")
    decision = body.get("decision", "review")
    try:
        record = control_plane.record_certification_decision(
            slug=slug,
            version=version,
            decision=decision,
            actor=body.get("actor") or principal.subject,
            reason=body.get("reason", ""),
            test_run_id=body.get("test_run_id"),
            org_id=principal.org_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if decision == "certify":
        conn.certification_state = "certified"
    elif decision == "fail":
        conn.certification_state = "failed"
    elif decision == "review":
        conn.certification_state = "reviewed"
    return record


@app.get("/api/v1/certification-queue")
def certification_queue():
    return {"queue": control_plane.list_certification_queue(registry.connectors)}


@app.get("/api/v1/certification-decisions")
def list_certification_decisions(slug: str | None = None):
    return {"decisions": control_plane.list_certification_decisions(slug)}


@app.get("/api/v1/health/connectors")
def health_connectors():
    """Current health summaries for ops dashboards (spec §5.5)."""
    events = audit.events
    by_slug: dict[str, dict] = {}
    for conn in registry.list():
        by_slug[conn.slug] = {
            "slug": conn.slug,
            "version": conn.version,
            "reported_health": (conn.health or {}).get("status", "unknown"),
            "quarantined": control_plane.is_quarantined(conn.slug, conn.version),
            "certification_state": conn.certification_state,
            "calls": 0,
            "deny": 0,
            "allow": 0,
            "last_outcome": None,
            "last_seen_at": None,
        }
    for event in events:
        slug = event.get("connector_slug")
        if slug not in by_slug:
            continue
        bucket = by_slug[slug]
        bucket["calls"] += 1
        decision = event.get("policy_decision")
        if decision == "deny":
            bucket["deny"] += 1
        elif decision == "allow":
            bucket["allow"] += 1
        bucket["last_outcome"] = event.get("outcome")
        bucket["last_seen_at"] = event.get("ts") or event.get("created_at")
    for bucket in by_slug.values():
        if bucket["quarantined"]:
            bucket["status"] = "quarantined"
        elif bucket["deny"] > 0 and bucket["allow"] == 0 and bucket["calls"] > 0:
            bucket["status"] = "unhealthy"
        elif bucket["calls"] == 0:
            bucket["status"] = bucket["reported_health"] or "unknown"
        else:
            bucket["status"] = "healthy"
    return {"connectors": list(by_slug.values())}


@app.post("/api/v1/supply-chain/refresh")
def supply_chain_refresh(principal: Principal = Depends(require_roles("admin", "operator"))):
    """Re-ingest SBOM/signature/CVE feed into the catalog index (live refresh beyond one-shot fixtures)."""
    import json
    import subprocess

    script = ROOT / "scripts" / "ingest-supply-chain.mjs"
    proc = subprocess.run(["node", str(script)], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise HTTPException(500, f"ingest failed: {proc.stderr or proc.stdout}")
    summary = json.loads(proc.stdout.strip().splitlines()[-1])
    # Auto-quarantine blocked posture connectors
    index_path = ROOT / "connectors" / "supply-chain-index.json"
    blocked = []
    if index_path.exists():
        data = json.loads(index_path.read_text(encoding="utf-8"))
        for slug, item in (data.get("connectors") or {}).items():
            if item.get("posture") == "blocked":
                conn = registry.get(slug)
                if conn and not control_plane.is_quarantined(slug, conn.version):
                    control_plane.quarantine(slug, conn.version, "supply-chain posture blocked (critical CVE)", principal.subject)
                    conn.certification_state = "quarantined"
                    blocked.append(slug)
    summary["auto_quarantined"] = blocked
    summary["refreshed_by"] = principal.subject
    return summary


@app.post("/gateway/v1/tools/complete")
def gateway_tools_complete(body: dict, principal: Principal = Depends(get_principal)):
    """Record final outcome for async tool invocations (spec §5.6)."""
    correlation_id = body.get("correlation_id")
    if not correlation_id:
        raise HTTPException(400, "correlation_id required")
    outcome = body.get("outcome", "completed")
    event = audit.append(
        {
            "correlation_id": correlation_id,
            "actor_id": principal.subject,
            "organization": principal.org_id,
            "tenant": principal.tenant_id,
            "project": body.get("project_id", "project_local"),
            "environment": body.get("environment", "development"),
            "connector_slug": body.get("connector_slug"),
            "tool_name": body.get("tool_name"),
            "normalized_arguments_hash": body.get("args_hash"),
            "policy_decision": body.get("policy_decision", "allow"),
            "approval_id": body.get("approval_id"),
            "idempotency_key": body.get("idempotency_key"),
            "latency_ms": int(body.get("latency_ms") or 0),
            "outcome": outcome,
            "response_hash": body.get("response_hash"),
            "evidence_uri": body.get("evidence_uri"),
            "redaction_count": int(body.get("redaction_count") or 0),
            "async_complete": True,
        }
    )
    return {"ok": True, "event_hash": event.get("event_hash"), "correlation_id": correlation_id}


# ── Streamable HTTP MCP termination (Milestone 3) ─────────────────────────


def _mcp_evaluate(req: InvokeRequest) -> dict:
    result = policy.evaluate(req)
    return result.model_dump()


def _mcp_invoke(req: InvokeRequest, principal: Principal):
    return invoke(req, principal)


from .mcp_transport import build_mcp_router  # noqa: E402

app.include_router(
    build_mcp_router(
        registry=registry,
        control_plane=control_plane,
        evaluate_fn=_mcp_evaluate,
        invoke_fn=_mcp_invoke,
    )
)


@app.get("/api/v1/connectors/{slug}/supply-chain")
def connector_supply_chain(slug: str):
    """SBOM / signature / CVE posture from ingested supply-chain index."""
    index_path = ROOT / "connectors" / "supply-chain-index.json"
    if not index_path.exists():
        raise HTTPException(404, "supply-chain index not ingested — run scripts/ingest-supply-chain.mjs")
    data = __import__("json").loads(index_path.read_text(encoding="utf-8"))
    item = (data.get("connectors") or {}).get(slug)
    if not item:
        raise HTTPException(404, f"no supply-chain record for {slug}")
    return item


@app.get("/api/v1/metrics/mutations")
def metrics_mutations():
    """Observe deny/approval/grant quality before expanding mutations (Milestone 5)."""
    events = audit.events
    write_events = [
        e
        for e in events
        if e.get("connector_slug") == "github-write"
        or (e.get("tool_name") or "").startswith(("apply_", "write_", "create_", "delete_"))
    ]
    total = len(write_events)
    allows = sum(1 for e in write_events if e.get("policy_decision") == "allow")
    denies = sum(1 for e in write_events if e.get("policy_decision") == "deny")
    approvals_needed = sum(1 for e in write_events if e.get("policy_decision") == "require_approval")
    consumed = sum(1 for a in approvals.requests.values() if a.get("status") == "consumed")
    dual = sum(1 for a in approvals.requests.values() if int(a.get("required_approver_count") or 1) >= 2)
    deny_rate = (denies / total) if total else 0.0
    return {
        "window": "process_lifetime",
        "mutation_shaped_events": total,
        "allow": allows,
        "deny": denies,
        "require_approval": approvals_needed,
        "deny_rate": round(deny_rate, 4),
        "grants_consumed": consumed,
        "dual_approval_requests": dual,
        "expansion_ready": total >= 10 and deny_rate >= 0 and consumed >= 1,
        "guidance": "Expand mutations only after observing deny/audit quality in staging; keep github-write dry-run until expansion_ready.",
    }
