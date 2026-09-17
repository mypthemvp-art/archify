---
name: mcp-security-gateway
description: >-
  MCP Security Gateway: Build before enabling broad third-party connectors. Covers automations A091, A092, A093, A094, A095, A096, A097, A098, A099. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for MCP Security Gateway.
---

# MCP Security Gateway

LevelUpWorld / agent-ops priority plugin skill. Automations: **A091, A092, A093, A094, A095, A096, A097, A098, A099**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A091, A092, A093, A094, A095, A096, A097, A098, A099, or when the user asks for MCP Security Gateway outcomes.

## Instruction routine

1. Lint mcp.json and tool manifests for overbroad scopes, network, and filesystem access (A094).
2. Scaffold authenticated MCP servers from OpenAI MCPKit patterns (A091) and generate contract tests (A092).
3. Produce least-privilege capability threat models (A093).
4. Redact secrets/PII from tool responses before they re-enter model context (A095).
5. Enforce approval-gated write proxy, budgets, injection firewall, and sandbox-only replay (A096–A099).

## Shared invariants

- Treat every connector as an untrusted capability.
- Separate read-only discovery from mutations; writes must be explicit, reviewable, idempotent, and logged.
- Split risky tools into `plan_*` / `validate_*` / `apply_*` / `rollback_*`.
- Never expose production shell, unrestricted filesystem, privileged DB, broad cloud admin, or generic unrestricted HTTP.
- Record correlation_id, actor, tenant, tool, arguments hash, approval_id, result status, and evidence URI.
- Prefer GitOps PR generation over direct Kubernetes/Terraform mutation.

## References

- Catalog: `levelupworld/docs/CATALOG.md`
- Architecture: `levelupworld/docs/ARCHITECTURE.md`
- Blueprints: `.cursor/automations/` for A091, A092, A093, A094, A095, A096, A097, A098, A099
