---
name: featureops
description: >-
  FeatureOps Plugin: Approval-gate rollout percentage changes. Covers automations A053, A054. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for FeatureOps Plugin.
---

# FeatureOps Plugin

LevelUpWorld / agent-ops priority plugin skill. Automations: **A053, A054**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A053, A054, or when the user asks for FeatureOps Plugin outcomes.

## Instruction routine

1. Inventory feature flags and experiments via read APIs (A053–A054).
2. Propose stale-flag removal PRs and experiment decision briefs.
3. Never change rollout percentages without approval-gated apply_* tools.
4. Link flag changes to issues/PRs and record correlation IDs.

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
- Blueprints: `.cursor/automations/` for A053, A054
