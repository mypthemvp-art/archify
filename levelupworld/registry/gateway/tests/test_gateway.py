"""Unit tests for registry gateway policy, approvals, redaction, and audit chain."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "gateway"))

from app.approvals import ApprovalService  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ApprovalCreateRequest, Environment, InvokeRequest  # noqa: E402
from app.policy import PolicyEngine  # noqa: E402
from app.registry import Registry  # noqa: E402
from app.security import args_hash, redact_payload  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_control_plane():
    from app.main import control_plane, registry

    control_plane.activations.clear()
    control_plane.quarantines.clear()
    control_plane.test_runs.clear()
    control_plane.policy_decisions.clear()
    # Restore any certification_state mutated by quarantine UX
    for conn in registry.connectors.values():
        if conn.certification_state == "quarantined":
            # default certified/in_lab from manifests — reload
            pass
    registry.reload()
    yield


def test_catalog_lists_core_connectors_plus_github_write(client):
    res = client.get("/api/v1/connectors")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 11
    slugs = {c["slug"] for c in body["connectors"]}
    assert "github-readonly" in slugs
    assert "policy-approval-gateway" in slugs
    assert "audit-evidence-store" in slugs
    assert "github-write" in slugs
    gw = next(c for c in body["connectors"] if c["slug"] == "github-write")
    assert "production" not in gw["allowed_environments"]


def test_read_only_invoke_allowed(client):
    res = client.post(
        "/api/v1/gateway/invoke",
        json={
            "actor": "user:alice",
            "connector_slug": "github-readonly",
            "tool_name": "get_pull_request",
            "arguments": {"number": 1},
            "environment": "development",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["result"]["ok"] is True
    assert body["correlation_id"]


def test_write_requires_approval(client):
    res = client.post(
        "/api/v1/gateway/invoke",
        json={
            "actor": "user:alice",
            "connector_slug": "filesystem-sandbox",
            "tool_name": "write_artifact",
            "arguments": {"path": "out/report.md", "content": "hi"},
            "environment": "development",
            "idempotency_key": "idem-1",
        },
    )
    assert res.status_code == 401
    assert res.json()["error"] == "approval_required"


def test_approval_binding_rejects_changed_args(client):
    create = client.post(
        "/api/v1/approvals",
        json={
            "actor": "user:alice",
            "environment": "staging",
            "connector_slug": "filesystem-sandbox",
            "connector_version": "1.0.0",
            "tool_name": "write_artifact",
            "plan_markdown": "Write report artifact",
            "arguments": {"path": "out/report.md", "content": "safe"},
            "idempotency_key": "idem-bind-1",
            "correlation_id": "00000000-0000-0000-0000-000000000099",
        },
    )
    assert create.status_code == 200
    req_id = create.json()["id"]
    decide = client.post(
        f"/api/v1/approvals/{req_id}/decide",
        json={"approver": "user:boss", "approve": True},
    )
    assert decide.status_code == 200
    token = decide.json()["grant_token"]

    # Same args → allow
    ok = client.post(
        "/api/v1/gateway/invoke",
        json={
            "actor": "user:alice",
            "tenant_id": "tenant_local",
            "project_id": "project_local",
            "environment": "staging",
            "connector_slug": "filesystem-sandbox",
            "tool_name": "write_artifact",
            "arguments": {"path": "out/report.md", "content": "safe"},
            "idempotency_key": "idem-bind-1",
            "approval_grant": token,
        },
    )
    assert ok.status_code == 200

    # Changed content → deny (args_hash mismatch)
    create2 = client.post(
        "/api/v1/approvals",
        json={
            "actor": "user:alice",
            "environment": "staging",
            "connector_slug": "filesystem-sandbox",
            "connector_version": "1.0.0",
            "tool_name": "write_artifact",
            "plan_markdown": "Write report artifact",
            "arguments": {"path": "out/report.md", "content": "safe"},
            "idempotency_key": "idem-bind-2",
            "correlation_id": "00000000-0000-0000-0000-000000000098",
        },
    )
    req2 = create2.json()["id"]
    token2 = client.post(
        f"/api/v1/approvals/{req2}/decide",
        json={"approver": "user:boss", "approve": True},
    ).json()["grant_token"]

    bad = client.post(
        "/api/v1/gateway/invoke",
        json={
            "actor": "user:alice",
            "tenant_id": "tenant_local",
            "project_id": "project_local",
            "environment": "staging",
            "connector_slug": "filesystem-sandbox",
            "tool_name": "write_artifact",
            "arguments": {"path": "out/report.md", "content": "EVIL"},
            "idempotency_key": "idem-bind-2",
            "approval_grant": token2,
        },
    )
    assert bad.status_code == 403
    assert "args_hash mismatch" in bad.json()["detail"]


def test_redaction_and_args_hash():
    assert args_hash({"b": 1, "a": 2}) == args_hash({"a": 2, "b": 1})
    redacted, count = redact_payload({"token": "abc123456", "email": "a@b.co"})
    assert count >= 1
    assert "abc123456" not in str(redacted)


def test_denylist_connector():
    reg = Registry()
    eng = PolicyEngine(reg, ApprovalService())
    result = eng.evaluate(
        InvokeRequest(
            actor="user:x",
            connector_slug="kubectl-apply",
            tool_name="apply",
            arguments={},
            environment=Environment.production,
        )
    )
    assert result.decision.value == "deny"


def test_dashboard_pages(client):
    for path in ["/", "/lab", "/ops", "/audit", "/approvals", "/connectors/github-readonly"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "Agent-Ops" in res.text


def test_quarantine_blocks_invoke(client):
    q = client.post(
        "/api/v1/connectors/docs-fetch-search/quarantine",
        json={"version": "1.0.0", "reason": "test", "actor": "user:secops"},
    )
    assert q.status_code == 200
    res = client.post(
        "/api/v1/gateway/invoke",
        json={
            "actor": "user:alice",
            "connector_slug": "docs-fetch-search",
            "tool_name": "search_docs",
            "arguments": {"q": "mcp"},
            "environment": "development",
        },
    )
    assert res.status_code == 403
    assert "quarantined" in res.json()["detail"]


def test_activation_and_test_run(client):
    run = client.post("/api/v1/connectors/github-readonly/versions/1.0.0/test-runs?suite=full")
    assert run.status_code == 200
    assert run.json()["status"] == "passed"
    got = client.get(f"/api/v1/test-runs/{run.json()['id']}")
    assert got.status_code == 200

    act = client.post(
        "/api/v1/activations",
        json={
            "slug": "github-readonly",
            "version": "1.0.0",
            "project_id": "agent-platform",
            "environment": "staging",
            "actor": "user:alice",
        },
    )
    assert act.status_code == 200
    approved = client.post(
        f"/api/v1/activations/{act.json()['id']}/approve",
        json={"approver": "user:boss", "approve": True},
    )
    assert approved.status_code == 200
    assert approved.json()["enabled"] is True


def test_metrics_and_version_detail(client):
    client.post(
        "/api/v1/policy/evaluate",
        json={
            "actor": "user:alice",
            "connector_slug": "git-repository",
            "tool_name": "status",
            "arguments": {},
            "environment": "development",
        },
    )
    metrics = client.get("/api/v1/metrics/connectors")
    assert metrics.status_code == 200
    assert "connectors" in metrics.json()
    detail = client.get("/api/v1/connectors/git-repository/versions/1.0.0")
    assert detail.status_code == 200
    assert detail.json()["slug"] == "git-repository"


def test_catalog_multi_filters_and_sort(client):
    res = client.get(
        "/api/v1/connectors",
        params={
            "category": "github",
            "operation": "read",
            "trustTier": "3,4",
            "environment": "development",
            "sort": "-success_rate_24h",
            "view": "table",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["view"] == "table"
    assert body["count"] >= 1
    for c in body["connectors"]:
        assert c["category"] == "github"
        assert any(t["capability"] == "read" for t in c["tools"])


def test_full_suite_includes_hard_gates(client):
    run = client.post("/api/v1/connectors/github-readonly/versions/1.0.0/test-runs?suite=full")
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "passed"
    gates = {g["gate"] for g in body["report"]["hard_gates"]}
    assert "pinned_digest" in gates
    assert "write_tools_require_approval" in gates
    assert "immutable_audit" in gates
    assert len(body["report"]["results"]) > 8


def test_gateway_v1_authorize_redact_egress(client):
    authz = client.post(
        "/gateway/v1/tools/authorize",
        json={
            "actor": "user:alice",
            "connector_slug": "github-readonly",
            "tool_name": "get_pull_request",
            "arguments": {"number": 1},
            "environment": "development",
        },
    )
    assert authz.status_code == 200
    assert authz.json()["allow"] is True

    red = client.post("/gateway/v1/redact", json={"payload": {"token": "abc123456789"}})
    assert red.status_code == 200
    assert red.json()["redaction_count"] >= 1

    eg = client.post(
        "/gateway/v1/egress/check",
        json={"url": "https://api.github.com/repos/x", "allowlist": ["api.github.com"]},
    )
    assert eg.status_code == 200
    assert eg.json()["allow"] is True
    blocked = client.post(
        "/gateway/v1/egress/check",
        json={"url": "http://169.254.169.254/latest", "allowlist": ["api.github.com"]},
    )
    assert blocked.json()["allow"] is False


def test_saved_views_and_quarantine_page(client):
    views = client.get("/api/v1/catalog/views")
    assert views.status_code == 200
    assert any(v["id"] == "certified-readonly-prod" for v in views.json()["views"])
    page = client.get("/admin/quarantine")
    assert page.status_code == 200
    assert "Quarantine" in page.text


def test_dual_approval_and_step_up_for_production(client):
    create = client.post(
        "/api/v1/approvals",
        json={
            "actor": "user:alice",
            "environment": "production",
            "connector_slug": "filesystem-sandbox",
            "connector_version": "1.0.0",
            "tool_name": "write_artifact",
            "plan_markdown": "Prod write needs dual approval",
            "arguments": {"path": "out/x.md", "content": "x"},
            "idempotency_key": "dual-1",
            "correlation_id": "00000000-0000-0000-0000-0000000000d1",
        },
    )
    assert create.status_code == 200
    body = create.json()
    assert body["required_approver_count"] == 2
    assert body["step_up_required"] is True
    req_id = body["id"]

    # Self-approve rejected
    self_approve = client.post(
        f"/api/v1/approvals/{req_id}/decide",
        json={"approver": "user:alice", "approve": True, "step_up_verified": True},
    )
    assert self_approve.status_code == 400

    # First approver without step-up rejected
    no_step = client.post(
        f"/api/v1/approvals/{req_id}/decide",
        json={"approver": "user:boss1", "approve": True, "step_up_verified": False},
    )
    assert no_step.status_code == 400

    first = client.post(
        f"/api/v1/approvals/{req_id}/decide",
        json={"approver": "user:boss1", "approve": True, "step_up_verified": True},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "partially_approved"
    assert first.json().get("grant_token") in (None, "")

    second = client.post(
        f"/api/v1/approvals/{req_id}/decide",
        json={"approver": "user:boss2", "approve": True, "step_up_verified": True},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "approved"
    assert second.json()["grant_token"]
    assert len(second.json()["decisions"]) == 2


def test_ephemeral_lab_run(client):
    res = client.post("/api/v1/connectors/github-readonly/versions/1.0.0/lab-runs?suite=full")
    assert res.status_code == 200
    body = res.json()
    assert "ephemeral" in body
    assert body["ephemeral"]["ok"] is True
    assert body["ephemeral"]["evidence"]


def test_healthz_reports_auth_and_rls(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["auth_mode"] == "disabled"
    assert body["database_rls"] is False
    assert "version" in body


def test_whoami_and_dev_token(client):
    who = client.get("/api/v1/auth/whoami")
    assert who.status_code == 200
    assert who.json()["org_id"] == "org_local"

    tok = client.post(
        "/api/v1/auth/dev-token",
        json={
            "subject": "user:dev",
            "org_id": "org_demo",
            "roles": ["operator", "approver"],
        },
    )
    assert tok.status_code == 200
    assert tok.json()["token_type"] == "bearer"
    assert tok.json()["access_token"]


def test_github_write_requires_grant_then_dry_run(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WRITE_DRY_RUN", "1")
    args = {
        "repository": "acme/agent-platform",
        "head": "feat/demo",
        "base": "main",
        "title": "Demo PR",
        "draft": True,
    }
    blocked = client.post(
        "/api/v1/gateway/invoke",
        json={
            "actor": "user:alice",
            "connector_slug": "github-write",
            "tool_name": "create_pull_request",
            "arguments": args,
            "environment": "staging",
            "idempotency_key": "gw-1",
        },
    )
    assert blocked.status_code == 401

    # Production is hard-denied by environment allowlist
    prod = client.post(
        "/api/v1/policy/evaluate",
        json={
            "actor": "user:alice",
            "connector_slug": "github-write",
            "tool_name": "create_pull_request",
            "arguments": args,
            "environment": "production",
        },
    )
    assert prod.status_code == 200
    assert prod.json()["decision"] == "deny"

    create = client.post(
        "/api/v1/approvals",
        json={
            "actor": "user:alice",
            "environment": "staging",
            "connector_slug": "github-write",
            "connector_version": "1.0.0",
            "tool_name": "create_pull_request",
            "plan_markdown": "Create demo PR",
            "arguments": args,
            "idempotency_key": "gw-1",
            "correlation_id": "00000000-0000-0000-0000-0000000000aa",
        },
    )
    assert create.status_code == 200
    token = client.post(
        f"/api/v1/approvals/{create.json()['id']}/decide",
        json={"approver": "user:boss", "approve": True},
    ).json()["grant_token"]

    ok = client.post(
        "/api/v1/gateway/invoke",
        json={
            "actor": "user:alice",
            "tenant_id": "tenant_local",
            "project_id": "project_local",
            "environment": "staging",
            "connector_slug": "github-write",
            "tool_name": "create_pull_request",
            "arguments": args,
            "idempotency_key": "gw-1",
            "approval_grant": token,
        },
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["result"]["ok"] is True
    assert body["result"]["dry_run"] is True
    assert body["result"]["repository"] == "acme/agent-platform"


def test_github_write_adapter_rejects_prod_and_bad_repo():
    from app.adapters import github_write

    with pytest.raises(ValueError, match="forbidden in production"):
        github_write.validate_args(
            {"repository": "acme/x", "head": "a", "base": "b", "title": "t"},
            "production",
        )
    with pytest.raises(ValueError, match="repository"):
        github_write.validate_args(
            {"repository": "not-a-repo", "head": "a", "base": "b", "title": "t"},
            "staging",
        )


def test_db_disabled_without_url():
    from app.db import Database

    d = Database(url=None)
    assert d.enabled is False
    with d.session(org_id="org_x", actor_subject="user:x") as conn:
        assert conn is None
