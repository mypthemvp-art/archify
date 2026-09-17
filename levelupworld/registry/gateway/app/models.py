"""Shared models for the MCP registry control plane and policy gateway."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TrustTier(str, Enum):
    unverified = "unverified"
    sandboxed = "sandboxed"
    reviewed = "reviewed"
    certified = "certified"
    production_critical = "production_critical"


class Capability(str, Enum):
    read = "read"
    write = "write"
    delete = "delete"
    external_communication = "external_communication"


class PolicyDecision(str, Enum):
    allow = "allow"
    deny = "deny"
    require_approval = "require_approval"
    error = "error"


class Environment(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"


class ToolSpec(BaseModel):
    name: str
    capability: Capability
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "low"
    requires_approval: bool = False


class ConnectorManifest(BaseModel):
    slug: str
    display_name: str
    category: str
    rank: int
    description: str
    owner_team: str
    escalation_contact: str
    trust_tier: TrustTier
    certification_state: str
    transport: str
    version: str
    image_digest: str
    oauth_scopes: list[str] = Field(default_factory=list)
    outbound_domains: list[str] = Field(default_factory=list)
    allowed_environments: list[str] = Field(default_factory=list)
    data_classification: str = "internal"
    tools: list[ToolSpec] = Field(default_factory=list)
    read_tool_count: int = 0
    write_tool_count: int = 0
    delete_tool_count: int = 0
    safety: str = ""
    health: dict[str, Any] = Field(default_factory=dict)
    active_in_production: bool = False


class InvokeRequest(BaseModel):
    actor: str
    org_id: str = "org_local"
    tenant_id: str = "tenant_local"
    project_id: str = "project_local"
    environment: Environment = Environment.development
    connector_slug: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    idempotency_key: str | None = None
    approval_grant: str | None = None
    run_id: str | None = None


class PolicyResult(BaseModel):
    decision: PolicyDecision
    reason: str
    correlation_id: str
    args_hash: str
    risk_level: str
    requires_approval: bool = False
    approval_request_id: str | None = None


class ApprovalCreateRequest(BaseModel):
    actor: str
    org_id: str = "org_local"
    tenant_id: str = "tenant_local"
    project_id: str = "project_local"
    environment: Environment
    connector_slug: str
    connector_version: str
    tool_name: str
    plan_markdown: str
    arguments: dict[str, Any]
    idempotency_key: str
    correlation_id: str
    ttl_seconds: int = 300


class ApprovalDecision(BaseModel):
    approver: str
    approve: bool
    note: str | None = None
