---
name: accessibility-qa
description: >-
  Accessibility QA Plugin: Store a11y/visual/e2e artifacts as CI evidence. Covers automations A055, A056, A057. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Accessibility QA Plugin.
---

# Accessibility QA Plugin

LevelUpWorld / agent-ops priority plugin skill. Automations: **A055, A056, A057**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A055, A056, A057, or when the user asks for Accessibility QA Plugin outcomes.

## Instruction routine

1. Run Playwright/axe accessibility checks and capture artifacts (A055).
2. Review visual diffs; require approval before baseline updates (A056).
3. Execute browser e2e journeys in test environments only (A057).
4. Store screenshots and reports as CI evidence; no production mutation.

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
- Blueprints: `.cursor/automations/` for A055, A056, A057
