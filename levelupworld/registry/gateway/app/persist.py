"""Optional Postgres persistence for audit + approvals (Phase B).

When DATABASE_URL is unset, all methods no-op and callers keep using memory.
When set, writes go through db.session with app.org_id RLS GUC.
"""

from __future__ import annotations

import json
from typing import Any

from .db import db


class GatewayPersistence:
    def __init__(self, database=db):
        self.db = database

    @property
    def enabled(self) -> bool:
        return self.db.enabled

    def insert_audit_event(self, record: dict[str, Any]) -> None:
        if not self.enabled:
            return
        org_id = str(record.get("organization") or record.get("org_id") or "org_local")
        actor = str(record.get("actor_id") or record.get("actor_subject") or "unknown")
        with self.db.session(org_id=org_id, actor_subject=actor) as conn:
            if conn is None:
                return
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gateway_audit_events (
                      event_hash, prev_event_hash, correlation_id, org_id, tenant_id,
                      project_id, environment, actor_subject, connector_slug, connector_version,
                      tool_name, args_hash, policy_decision, approval_id, idempotency_key,
                      latency_ms, outcome, response_hash, evidence_uri, redaction_count, payload
                    ) VALUES (
                      %(event_hash)s, %(prev_event_hash)s, %(correlation_id)s, %(org_id)s, %(tenant_id)s,
                      %(project_id)s, %(environment)s, %(actor_subject)s, %(connector_slug)s, %(connector_version)s,
                      %(tool_name)s, %(args_hash)s, %(policy_decision)s, %(approval_id)s, %(idempotency_key)s,
                      %(latency_ms)s, %(outcome)s, %(response_hash)s, %(evidence_uri)s, %(redaction_count)s,
                      %(payload)s::jsonb
                    )
                    ON CONFLICT (event_hash) DO NOTHING
                    """,
                    {
                        "event_hash": record["event_hash"],
                        "prev_event_hash": record.get("prev_event_hash"),
                        "correlation_id": str(record.get("correlation_id")),
                        "org_id": org_id,
                        "tenant_id": record.get("tenant"),
                        "project_id": record.get("project"),
                        "environment": record.get("environment"),
                        "actor_subject": actor,
                        "connector_slug": record.get("connector_slug"),
                        "connector_version": record.get("connector_version"),
                        "tool_name": record.get("tool_name"),
                        "args_hash": record.get("normalized_arguments_hash") or record.get("args_hash"),
                        "policy_decision": record.get("policy_decision"),
                        "approval_id": record.get("approval_id"),
                        "idempotency_key": record.get("idempotency_key"),
                        "latency_ms": record.get("latency_ms"),
                        "outcome": record.get("outcome"),
                        "response_hash": record.get("response_hash"),
                        "evidence_uri": record.get("evidence_uri"),
                        "redaction_count": int(record.get("redaction_count") or 0),
                        "payload": json.dumps(record),
                    },
                )

    def upsert_approval(self, record: dict[str, Any]) -> None:
        if not self.enabled:
            return
        org_id = str(record.get("org_id") or "org_local")
        actor = str(record.get("actor") or "unknown")
        jws = record.get("grant_token")
        with self.db.session(org_id=org_id, actor_subject=actor) as conn:
            if conn is None:
                return
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gateway_approval_requests (
                      id, status, org_id, tenant_id, project_id, environment, actor,
                      connector_slug, connector_version, tool_name, plan_markdown, arguments,
                      args_hash, idempotency_key, correlation_id, required_approver_count,
                      approval_mode, decisions, step_up_required, grant_id, grant_jws,
                      decided_by, decided_at, decision_note, expires_at, created_at, consumed_at
                    ) VALUES (
                      %(id)s, %(status)s, %(org_id)s, %(tenant_id)s, %(project_id)s, %(environment)s, %(actor)s,
                      %(connector_slug)s, %(connector_version)s, %(tool_name)s, %(plan_markdown)s, %(arguments)s::jsonb,
                      %(args_hash)s, %(idempotency_key)s, %(correlation_id)s, %(required_approver_count)s,
                      %(approval_mode)s, %(decisions)s::jsonb, %(step_up_required)s, %(grant_id)s, %(grant_jws)s,
                      %(decided_by)s, %(decided_at)s, %(decision_note)s, %(expires_at)s, %(created_at)s, %(consumed_at)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      status = EXCLUDED.status,
                      decisions = EXCLUDED.decisions,
                      grant_id = EXCLUDED.grant_id,
                      grant_jws = EXCLUDED.grant_jws,
                      decided_by = EXCLUDED.decided_by,
                      decided_at = EXCLUDED.decided_at,
                      decision_note = EXCLUDED.decision_note,
                      consumed_at = EXCLUDED.consumed_at

                    """,
                    {
                        "id": record["id"],
                        "status": record["status"],
                        "org_id": org_id,
                        "tenant_id": record["tenant_id"],
                        "project_id": record["project_id"],
                        "environment": record["environment"],
                        "actor": actor,
                        "connector_slug": record["connector_slug"],
                        "connector_version": record["connector_version"],
                        "tool_name": record["tool_name"],
                        "plan_markdown": record.get("plan_markdown") or "",
                        "arguments": json.dumps(record.get("arguments") or {}),
                        "args_hash": record["args_hash"],
                        "idempotency_key": record["idempotency_key"],
                        "correlation_id": str(record["correlation_id"]),
                        "required_approver_count": int(record.get("required_approver_count") or 1),
                        "approval_mode": record.get("approval_mode") or "single",
                        "decisions": json.dumps(record.get("decisions") or []),
                        "step_up_required": bool(record.get("step_up_required")),
                        "grant_id": record.get("grant_id"),
                        "grant_jws": jws,
                        "decided_by": record.get("decided_by"),
                        "decided_at": record.get("decided_at"),
                        "decision_note": record.get("decision_note"),
                        "expires_at": record["expires_at"],
                        "created_at": record.get("created_at"),
                        "consumed_at": record.get("consumed_at"),
                    },
                )

    def upsert_grant(self, grant: dict[str, Any], *, org_id: str, approval_request_id: str) -> None:
        if not self.enabled:
            return
        jws = grant["token"]
        with self.db.session(org_id=org_id, actor_subject="gateway") as conn:
            if conn is None:
                return
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gateway_approval_grants (
                      grant_id, approval_request_id, org_id, grant_jws, claims, consumed_at, revoked_at
                    ) VALUES (
                      %(grant_id)s, %(approval_request_id)s, %(org_id)s, %(grant_jws)s, %(claims)s::jsonb,
                      %(consumed_at)s, %(revoked_at)s
                    )
                    ON CONFLICT (grant_id) DO UPDATE SET
                      consumed_at = EXCLUDED.consumed_at,
                      revoked_at = EXCLUDED.revoked_at
                    """,
                    {
                        "grant_id": grant["grant_id"],
                        "approval_request_id": approval_request_id,
                        "org_id": org_id,
                        "grant_jws": jws,
                        "claims": json.dumps(grant.get("claims") or {}),
                        "consumed_at": grant.get("consumed_at"),
                        "revoked_at": grant.get("revoked_at"),
                    },
                )


persistence = GatewayPersistence()
