"""Approval request store and signed grant issue/verify."""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import jwt

from .models import ApprovalCreateRequest, Environment
from .security import args_hash


class ApprovalService:
    def __init__(self, signing_secret: str | None = None):
        self.signing_secret = signing_secret or os.environ.get(
            "GATEWAY_SIGNING_SECRET", "dev-only-change-me-agent-ops-gateway"
        )
        self.requests: dict[str, dict[str, Any]] = {}
        self.grants: dict[str, dict[str, Any]] = {}

    def create_request(self, body: ApprovalCreateRequest) -> dict[str, Any]:
        req_id = f"apr_{uuid.uuid4().hex}"
        digest = args_hash(body.arguments)
        expires = time.time() + body.ttl_seconds
        record = {
            "id": req_id,
            "status": "pending",
            "org_id": body.org_id,
            "tenant_id": body.tenant_id,
            "project_id": body.project_id,
            "environment": body.environment.value,
            "actor": body.actor,
            "connector_slug": body.connector_slug,
            "connector_version": body.connector_version,
            "tool_name": body.tool_name,
            "plan_markdown": body.plan_markdown,
            "arguments": body.arguments,
            "args_hash": digest,
            "idempotency_key": body.idempotency_key,
            "correlation_id": body.correlation_id,
            "expires_at": datetime.fromtimestamp(expires, tz=timezone.utc).isoformat(),
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "grant_id": None,
        }
        self.requests[req_id] = record
        return record

    def decide(self, request_id: str, approver: str, approve: bool, note: str | None = None) -> dict[str, Any]:
        req = self.requests.get(request_id)
        if not req:
            raise KeyError("approval request not found")
        if req["status"] != "pending":
            raise ValueError(f"request is {req['status']}")
        if datetime.fromisoformat(req["expires_at"]) < datetime.now(tz=timezone.utc):
            req["status"] = "expired"
            raise ValueError("request expired")

        req["decided_by"] = approver
        req["decided_at"] = datetime.now(tz=timezone.utc).isoformat()
        req["decision_note"] = note
        if not approve:
            req["status"] = "denied"
            return req

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
            "scope": [f"{req['connector_slug']}:{req['tool_name']}"],
            "iat": now,
            "exp": exp,
            "approval_request_id": request_id,
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

        grant_id = claims["grant_id"]
        stored = self.grants.get(grant_id)
        if not stored:
            raise ValueError("unknown grant")
        if stored.get("revoked_at"):
            raise ValueError("grant revoked")
        if stored.get("consumed_at") and stored.get("claims", {}).get("args_hash") != digest:
            raise ValueError("grant already consumed")
        stored["consumed_at"] = datetime.now(tz=timezone.utc).isoformat()
        return claims
