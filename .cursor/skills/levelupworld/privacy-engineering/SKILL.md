---
name: privacy-engineering
description: >-
  Privacy Engineering Plugin: Data-flow, retention, HIPAA, and redaction workflows. Covers automations A005, A049, A051, A082, A084, A095. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Privacy Engineering Plugin.
---

# Privacy Engineering Plugin

LevelUpWorld / agent-ops priority plugin skill. Automations: **A005, A049, A051, A082, A084, A095**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A005, A049, A051, A082, A084, A095, or when the user asks for Privacy Engineering Plugin outcomes.

## Instruction routine

1. Map PII data flows and retention exceptions (A005, A049).
2. Review telemetry schemas for minimization (A051).
3. Run HIPAA safeguard checks without PHI extraction (A082).
4. Coordinate privacy-request plans; approval before disclosure/deletion (A084).
5. Ensure MCP response redaction before model context (A095).

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
- Blueprints: `.cursor/automations/` for A005, A049, A051, A082, A084, A095
