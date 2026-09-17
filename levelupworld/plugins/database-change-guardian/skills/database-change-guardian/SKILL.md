---
name: database-change-guardian
description: >-
  Database Change Guardian: Require explicit approval for all schema writes. Covers automations A010, A046, A047, A048, A049. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Database Change Guardian.
---

# Database Change Guardian

LevelUpWorld / agent-ops priority plugin skill. Automations: **A010, A046, A047, A048, A049**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A010, A046, A047, A048, A049, or when the user asks for Database Change Guardian outcomes.

## Instruction routine

1. Classify migrations for locks, rollback, and backfill risk (A047).
2. Build/sanitize tenant-isolation tests (A010); fail closed on cross-tenant access.
3. Use Postgres read-only/replicas for slow-query review (A046) with statement timeouts.
4. Assist backup-restore drills only in isolated sandboxes (A048).
5. Audit retention exceptions (A049); never perform destructive repair or prod schema apply from the agent.

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
- Blueprints: `.cursor/automations/` for A010, A046, A047, A048, A049
