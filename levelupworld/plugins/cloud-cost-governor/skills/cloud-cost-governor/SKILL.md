---
name: cloud-cost-governor
description: >-
  Cloud Cost Governor: Recommendations only until measured savings are proven. Covers automations A045, A069, A071, A072, A073. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Cloud Cost Governor.
---

# Cloud Cost Governor

LevelUpWorld / agent-ops priority plugin skill. Automations: **A045, A069, A071, A072, A073**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A045, A069, A071, A072, A073, or when the user asks for Cloud Cost Governor outcomes.

## Instruction routine

1. Triage cloud and CI cost anomalies with read-only billing/metrics (A069, A071).
2. Recommend rightsizing and orphan cleanup plans; no automatic resize/delete (A072–A073).
3. Include capacity forecasts (A045) as advisory only until savings are measured.
4. Require human approval for any remediation write.

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
- Blueprints: `.cursor/automations/` for A045, A069, A071, A072, A073
