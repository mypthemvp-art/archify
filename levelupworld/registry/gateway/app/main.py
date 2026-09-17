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

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .approvals import ApprovalService
from .audit import AuditStore
from .control_plane import ControlPlaneStore
from .models import ApprovalCreateRequest, ApprovalDecision, InvokeRequest, PolicyDecision
from .policy import PolicyEngine
from .registry import Registry
from .security import BudgetTracker, args_hash, new_correlation_id, redact_payload

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "dashboard"

app = FastAPI(
    title="Agent-Ops MCP Registry Gateway",
    version="0.2.0",
    description="Control plane (registry) + policy gateway for certified MCP connectors.",
)

registry = Registry()
approvals = ApprovalService()
audit = AuditStore()
budgets = BudgetTracker()
control_plane = ControlPlaneStore()
policy = PolicyEngine(registry, approvals, control_plane)

if (DASHBOARD / "static").exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD / "static")), name="static")
templates = Jinja2Templates(directory=str(DASHBOARD / "templates"))


@app.get("/healthz")
def healthz():
    return {"ok": True, "connectors": len(registry.connectors), "audit_events": len(audit.events)}


# ── Registry (control plane) ─────────────────────────────────────────────


@app.get("/api/v1/connectors")
def list_connectors(
    category: str | None = None,
    trust_tier: str | None = None,
    capability: str | None = None,
    environment: str | None = None,
    q: str | None = None,
):
    items = registry.list(
        category=category,
        trust_tier=trust_tier,
        capability=capability,
        environment=environment,
        q=q,
    )
    return {"count": len(items), "connectors": [c.model_dump() for c in items]}


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
def evaluate_policy(req: InvokeRequest):
    result = policy.evaluate(req)
    control_plane.log_policy_decision(
        policy_key=f"{req.connector_slug}.{req.tool_name}",
        decision=result.decision.value,
        correlation_id=result.correlation_id,
        reason=result.reason,
        input_data={
            "actor": req.actor,
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
def invoke(req: InvokeRequest):
    """Evaluate policy, optionally require grant, stub-invoke connector, redact, audit."""
    started = time.time()
    run_id = budgets.begin(req.run_id)
    ok, budget_msg = budgets.charge(run_id)
    if not ok:
        raise HTTPException(429, budget_msg)

    result = policy.evaluate(req)
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
                "latency_ms": int((time.time() - started) * 1000),
                "outcome": result.reason,
                "response_hash": None,
                "evidence_uri": None,
                "redaction_count": 0,
            }
        )
        raise HTTPException(403, result.reason)

    # Stub connector response — real adapters plug in here.
    raw = {
        "ok": True,
        "connector": req.connector_slug,
        "tool": req.tool_name,
        "echo_args": req.arguments,
        "note": "stub invoke — replace with certified connector adapter",
    }
    safe, redactions = redact_payload(raw)
    latency_ms = int((time.time() - started) * 1000)
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
    }


@app.post("/api/v1/approvals")
def create_approval(body: ApprovalCreateRequest):
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
def list_approvals():
    return {"approvals": list(approvals.requests.values())}


@app.get("/api/v1/approvals/{request_id}")
def get_approval(request_id: str):
    req = approvals.requests.get(request_id)
    if not req:
        raise HTTPException(404, "not found")
    return req


@app.post("/api/v1/approvals/{request_id}/decide")
def decide_approval(request_id: str, body: ApprovalDecision):
    try:
        record = approvals.decide(request_id, body.approver, body.approve, body.note)
    except KeyError:
        raise HTTPException(404, "not found") from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    audit.append(
        {
            "correlation_id": record["correlation_id"],
            "actor_id": body.approver,
            "organization": record["org_id"],
            "tenant": record["tenant_id"],
            "project": record["project_id"],
            "environment": record["environment"],
            "connector_slug": record["connector_slug"],
            "connector_version": record["connector_version"],
            "tool_name": record["tool_name"],
            "normalized_arguments_hash": record["args_hash"],
            "policy_decision": PolicyDecision.allow.value if body.approve else PolicyDecision.deny.value,
            "approval_id": record["id"],
            "idempotency_key": record["idempotency_key"],
            "latency_ms": 0,
            "outcome": "approved" if body.approve else "denied",
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
