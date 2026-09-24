"""Approval request store and signed grant issue/verify.

Supports dual approval + step-up for production (spec §7.1 / Milestone 5).
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import jwt

from .models import ApprovalCreateRequest, Environment
from .persist import persistence
from .security import args_hash


def default_approver_count(environment: str, explicit: int | None = None) -> int:
    if explicit is not None and explicit >= 1:
        return explicit
    if environment == Environment.production.value:
        return int(os.environ.get("PRODUCTION_REQUIRED_APPROVERS", "2"))
    return 1


class ApprovalService:
    def __init__(self, signing_secret: str | None = None, store=None):
        self.signing_secret = signing_secret or os.environ.get(
            "GATEWAY_SIGNING_SECRET", "dev-only-change-me-agent-ops-gateway"
        )
        self.requests: dict[str, dict[str, Any]] = {}
        self.grants: dict[str, dict[str, Any]] = {}
        self._persist = store if store is not None else persistence

    def create_request(self, body: ApprovalCreateRequest) -> dict[str, Any]:
        req_id = f"apr_{uuid.uuid4().hex}"
        digest = args_hash(body.arguments)
        expires = time.time() + body.ttl_seconds
        env = body.environment.value
        required = default_approver_count(env, body.required_approver_count)
        mode = body.approval_mode or ("dual" if required >= 2 else "single")
        record = {
            "id": req_id,
            "status": "pending",
            "org_id": body.org_id,
            "tenant_id": body.tenant_id,
            "project_id": body.project_id,
            "environment": env,
            "actor": body.actor,
            "connector_slug": body.connector_slug,
            "connector_version": body.connector_version,
            "tool_name": body.tool_name,
            "plan_markdown": body.plan_markdown,
            "arguments": body.arguments,
            "args_hash": digest,
            "idempotency_key": body.idempotency_key,
            "correlation_id": body.correlation_id,
            "required_approver_count": required,
            "approval_mode": mode,
            "decisions": [],
            "step_up_required": env == Environment.production.value or body.step_up_required,
            "expires_at": datetime.fromtimestamp(expires, tz=timezone.utc).isoformat(),
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "grant_id": None,
            "grant_token": None,
        }
        self.requests[req_id] = record
        self._persist.upsert_approval(record)
        return record

    def decide(
        self,
        request_id: str,
        approver: str,
        approve: bool,
        note: str | None = None,
        *,
        step_up_verified: bool = False,
    ) -> dict[str, Any]:
        req = self.requests.get(request_id)
        if not req:
            raise KeyError("approval request not found")
        if req["status"] not in {"pending", "partially_approved"}:
            raise ValueError(f"request is {req['status']}")
        if datetime.fromisoformat(req["expires_at"]) < datetime.now(tz=timezone.utc):
            req["status"] = "expired"
            raise ValueError("request expired")

        # Production / dual: actor cannot self-approve
        if approver == req["actor"] and req["required_approver_count"] >= 2:
            raise ValueError("actor cannot self-approve dual/production requests")

        if req.get("step_up_required") and approve and not step_up_verified:
            raise ValueError("step-up verification required for this approval (SSO/WebAuthn)")

        decisions: list[dict[str, Any]] = req.setdefault("decisions", [])
        if any(d["approver"] == approver for d in decisions):
            raise ValueError("approver already recorded a decision")

        decisions.append(
            {
                "approver": approver,
                "approve": approve,
                "note": note,
                "step_up_verified": step_up_verified,
                "decided_at": datetime.now(tz=timezone.utc).isoformat(),
            }
        )
        req["decided_by"] = approver
        req["decided_at"] = datetime.now(tz=timezone.utc).isoformat()
        req["decision_note"] = note

        if not approve:
            req["status"] = "denied"
            self._persist.upsert_approval(req)
            return req

        approvals = [d for d in decisions if d["approve"]]
        if len(approvals) < req["required_approver_count"]:
            req["status"] = "partially_approved"
            req["grant_token"] = None
            self._persist.upsert_approval(req)
            return req

        return self._issue_grant(req, [d["approver"] for d in approvals])

    def _issue_grant(self, req: dict[str, Any], approvers: list[str]) -> dict[str, Any]:
        grant_id = f"grn_{uuid.uuid4().hex}"
        now = int(time.time())
        exp = now + 300
        claims = {
            "grant_id": grant_id,
            "iss": "agent-ops-gateway",
            "sub": req["actor"],
            "aud": "mcp-gateway",
            "org_id": req["org_id"],
            "tenant_id": req["tenant_id"],
            "project_id": req["project_id"],
            "environment": req["environment"],
            "connector_slug": req["connector_slug"],
            "connector_version": req["connector_version"],
            "tool_name": req["tool_name"],
            "args_hash": req["args_hash"],
            "idempotency_key": req["idempotency_key"],
            "policy_version": os.environ.get("GATEWAY_POLICY_VERSION", "default/v1"),
            "scope": [f"{req['connector_slug']}:{req['tool_name']}"],
            "nbf": now,
            "iat": now,
            "exp": exp,
            "approval_request_id": req["id"],
            "required_approvers": approvers,
            "required_approver_count": req["required_approver_count"],
            "approval_mode": req["approval_mode"],
            "step_up": bool(req.get("step_up_required")),
        }
        token = jwt.encode(claims, self.signing_secret, algorithm="HS256")
        self.grants[grant_id] = {
            "grant_id": grant_id,
            "token": token,
            "claims": claims,
            "consumed_at": None,
            "revoked_at": None,
        }
        req["status"] = "approved"
        req["grant_id"] = grant_id
        req["grant_token"] = token
        self._persist.upsert_approval(req)
        self._persist.upsert_grant(self.grants[grant_id], org_id=req["org_id"], approval_request_id=req["id"])
        return req

    def verify_grant(
        self,
        token: str,
        *,
        actor: str,
        tenant_id: str,
        project_id: str,
        environment: Environment,
        connector_slug: str,
        connector_version: str,
        tool_name: str,
        arguments: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        try:
            claims = jwt.decode(
                token,
                self.signing_secret,
                algorithms=["HS256"],
                audience="mcp-gateway",
                options={"require": ["exp", "iat", "sub", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise ValueError(f"invalid grant: {exc}") from exc

        digest = args_hash(arguments)
        checks = [
            (claims.get("sub") == actor, "actor mismatch"),
            (claims.get("tenant_id") == tenant_id, "tenant mismatch"),
            (claims.get("project_id") == project_id, "project mismatch"),
            (claims.get("environment") == environment.value, "environment mismatch"),
            (claims.get("connector_slug") == connector_slug, "connector mismatch"),
            (claims.get("connector_version") == connector_version, "version mismatch"),
            (claims.get("tool_name") == tool_name, "tool mismatch"),
            (claims.get("args_hash") == digest, "args_hash mismatch — approval no longer binds"),
            (claims.get("idempotency_key") == idempotency_key, "idempotency key mismatch"),
        ]
        for ok, msg in checks:
            if not ok:
                raise ValueError(msg)

        # Production grants must record dual approval in claims
        if environment == Environment.production:
            needed = int(claims.get("required_approver_count") or 2)
            got = claims.get("required_approvers") or []
            if len(got) < needed:
                raise ValueError("production grant missing dual approval evidence")

        grant_id = claims["grant_id"]
        stored = self.grants.get(grant_id)
        if not stored:
            raise ValueError("unknown grant")
        if stored.get("revoked_at"):
            raise ValueError("grant revoked")
        if stored.get("consumed_at"):
            if stored.get("claims", {}).get("idempotency_key") != idempotency_key:
                raise ValueError("grant already consumed")
        else:
            stored["consumed_at"] = datetime.now(tz=timezone.utc).isoformat()
            req_id = claims.get("approval_request_id")
            if req_id and req_id in self.requests:
                self.requests[req_id]["status"] = "consumed"
                self.requests[req_id]["consumed_at"] = stored["consumed_at"]
                self._persist.upsert_approval(self.requests[req_id])
            if req_id:
                self._persist.upsert_grant(
                    stored,
                    org_id=str(claims.get("org_id") or "org_local"),
                    approval_request_id=str(req_id),
                )
        return claims

    def consume(
        self,
        request_id: str,
        *,
        args_hash: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Gateway-only atomic consumption of an approved request (spec §7.3)."""
        req = self.requests.get(request_id)
        if not req:
            raise KeyError("approval request not found")
        if req["status"] != "approved":
            raise ValueError(f"request is {req['status']}")
        if datetime.fromisoformat(req["expires_at"]) < datetime.now(tz=timezone.utc):
            req["status"] = "expired"
            raise ValueError("request expired")
        if req["args_hash"] != args_hash:
            raise ValueError("args_hash mismatch")
        if req["idempotency_key"] != idempotency_key:
            raise ValueError("idempotency key mismatch")
        req["status"] = "consumed"
        req["consumed_at"] = datetime.now(tz=timezone.utc).isoformat()
        grant_id = req.get("grant_id")
        if grant_id and grant_id in self.grants:
            self.grants[grant_id]["consumed_at"] = req["consumed_at"]
            self._persist.upsert_grant(self.grants[grant_id], org_id=req["org_id"], approval_request_id=req["id"])
        self._persist.upsert_approval(req)
        return req
