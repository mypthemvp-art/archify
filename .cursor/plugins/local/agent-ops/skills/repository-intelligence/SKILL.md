---
name: repository-intelligence
description: >-
  Repository Intelligence Plugin: Architecture, debt, docs, and onboarding intelligence. Covers automations A001, A002, A022, A029, A030, A058, A060. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Repository Intelligence Plugin.
---

# Repository Intelligence Plugin

LevelUpWorld / agent-ops priority plugin skill. Automations: **A001, A002, A022, A029, A030, A058, A060**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A001, A002, A022, A029, A030, A058, A060, or when the user asks for Repository Intelligence Plugin outcomes.

## Instruction routine

1. Produce architecture maps (prefer Archify for validated HTML; Mermaid only when explicitly requested) (A001).
2. Build dependency inventories/SBOMs and change-impact explorations (A002, A022).
3. Rank quality debt and dead-code candidates without auto-deletion (A029–A030).
4. Detect docs drift and generate onboarding guides validated against CI (A058, A060).

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
- Blueprints: `.cursor/automations/` for A001, A002, A022, A029, A030, A058, A060
