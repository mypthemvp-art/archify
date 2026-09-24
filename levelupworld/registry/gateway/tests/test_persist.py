"""Fake DB + persistence dual-write tests (no live Postgres required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.approvals import ApprovalService  # noqa: E402
from app.audit import AuditStore  # noqa: E402
from app.models import ApprovalCreateRequest, Environment  # noqa: E402
from app.persist import GatewayPersistence  # noqa: E402


class FakeCursor:
    def __init__(self, store: list):
        self.store = store
        self._sql = ""
        self._params = None

    def execute(self, sql, params=None):
        self._sql = sql
        self._params = params
        self.store.append({"sql": " ".join(sql.split()), "params": params})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, store: list):
        self.store = store

    def cursor(self):
        return FakeCursor(self.store)


class FakeDB:
    enabled = True

    def __init__(self):
        self.writes: list[dict] = []
        self.sessions: list[tuple[str, str]] = []

    def session(self, *, org_id: str, actor_subject: str):
        self.sessions.append((org_id, actor_subject))
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            yield FakeConn(self.writes)

        return _cm()


def test_audit_dual_write_uses_org_rls_session():
    fake = FakeDB()
    store = AuditStore(store=GatewayPersistence(fake))
    rec = store.append(
        {
            "correlation_id": "c1",
            "organization": "org_demo",
            "actor_id": "user:a",
            "policy_decision": "allow",
            "outcome": "ok",
        }
    )
    assert rec["event_hash"]
    assert fake.sessions == [("org_demo", "user:a")]
    assert any("gateway_audit_events" in w["sql"] for w in fake.writes)
    assert fake.writes[0]["params"]["org_id"] == "org_demo"


def test_approval_dual_write_and_consume():
    fake = FakeDB()
    svc = ApprovalService(store=GatewayPersistence(fake))
    created = svc.create_request(
        ApprovalCreateRequest(
            actor="user:alice",
            org_id="org_demo",
            tenant_id="tenant_x",
            project_id="proj_x",
            environment=Environment.staging,
            connector_slug="filesystem-sandbox",
            connector_version="1.0.0",
            tool_name="write_artifact",
            plan_markdown="write",
            arguments={"path": "a", "content": "b"},
            idempotency_key="idem-p1",
            correlation_id="00000000-0000-0000-0000-0000000000p1",
        )
    )
    assert any("gateway_approval_requests" in w["sql"] for w in fake.writes)
    decided = svc.decide(created["id"], "user:boss", True)
    assert decided["status"] == "approved"
    assert any("gateway_approval_grants" in w["sql"] for w in fake.writes)
    # Ensure grant payload was JSON-serializable for jsonb bind
    grant_writes = [w for w in fake.writes if "gateway_approval_grants" in w["sql"]]
    assert json.loads(grant_writes[-1]["params"]["claims"])["tool_name"] == "write_artifact"
    consumed = svc.consume(created["id"], args_hash=created["args_hash"], idempotency_key="idem-p1")
    assert consumed["status"] == "consumed"
    assert fake.sessions
    assert all(s[0] == "org_demo" for s in fake.sessions)


def test_persist_disabled_when_database_unset():
    from app.db import Database

    p = GatewayPersistence(Database(url=None))
    assert p.enabled is False
    p.insert_audit_event({"event_hash": "x", "organization": "o", "actor_id": "a"})
