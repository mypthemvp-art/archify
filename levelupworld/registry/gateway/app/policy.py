"""Gateway policy evaluation — server-side authority for invoke decisions."""

from __future__ import annotations

from .approvals import ApprovalService
from .models import InvokeRequest, PolicyDecision, PolicyResult
from .registry import Registry
from .security import args_hash, new_correlation_id


DENY_CONNECTORS = {
    "kubectl-apply",
    "terraform-apply",
    "cloud-admin",
    "db-superuser",
    "unrestricted-http",
    "prod-shell",
}


class PolicyEngine:
    def __init__(self, registry: Registry, approvals: ApprovalService):
        self.registry = registry
        self.approvals = approvals

    def evaluate(self, req: InvokeRequest) -> PolicyResult:
        correlation_id = req.correlation_id or new_correlation_id()
        digest = args_hash(req.arguments)

        if req.connector_slug in DENY_CONNECTORS:
            return PolicyResult(
                decision=PolicyDecision.deny,
                reason="connector is on the hard denylist",
                correlation_id=correlation_id,
                args_hash=digest,
                risk_level="high",
            )

        conn, tool = self.registry.get_tool(req.connector_slug, req.tool_name)
        if not conn:
            return PolicyResult(
                decision=PolicyDecision.deny,
                reason=f"unknown connector '{req.connector_slug}'",
                correlation_id=correlation_id,
                args_hash=digest,
                risk_level="high",
            )
        if req.environment.value not in conn.allowed_environments:
            return PolicyResult(
                decision=PolicyDecision.deny,
                reason=f"connector not allowed in {req.environment.value}",
                correlation_id=correlation_id,
                args_hash=digest,
                risk_level="high",
            )
        if conn.certification_state == "quarantined":
            return PolicyResult(
                decision=PolicyDecision.deny,
                reason="connector version is quarantined",
                correlation_id=correlation_id,
                args_hash=digest,
                risk_level="high",
            )
        if not tool:
            return PolicyResult(
                decision=PolicyDecision.deny,
                reason=f"unknown tool '{req.tool_name}' on {req.connector_slug}",
                correlation_id=correlation_id,
                args_hash=digest,
                risk_level="high",
            )

        needs_approval = tool.requires_approval or tool.capability.value in {
            "write",
            "delete",
            "external_communication",
        } or tool.risk_level == "high"

        if needs_approval:
            if not req.approval_grant:
                return PolicyResult(
                    decision=PolicyDecision.require_approval,
                    reason="mutation/high-risk tool requires a signed approval grant",
                    correlation_id=correlation_id,
                    args_hash=digest,
                    risk_level=tool.risk_level,
                    requires_approval=True,
                )
            try:
                self.approvals.verify_grant(
                    req.approval_grant,
                    actor=req.actor,
                    tenant_id=req.tenant_id,
                    project_id=req.project_id,
                    environment=req.environment,
                    connector_slug=conn.slug,
                    connector_version=conn.version,
                    tool_name=tool.name,
                    arguments=req.arguments,
                    idempotency_key=req.idempotency_key or "",
                )
            except ValueError as exc:
                return PolicyResult(
                    decision=PolicyDecision.deny,
                    reason=str(exc),
                    correlation_id=correlation_id,
                    args_hash=digest,
                    risk_level=tool.risk_level,
                    requires_approval=True,
                )

        return PolicyResult(
            decision=PolicyDecision.allow,
            reason="policy allow",
            correlation_id=correlation_id,
            args_hash=digest,
            risk_level=tool.risk_level,
            requires_approval=needs_approval,
        )
