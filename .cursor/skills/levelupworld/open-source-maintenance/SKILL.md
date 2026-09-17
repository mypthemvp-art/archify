---
name: open-source-maintenance
description: >-
  Open-Source Maintenance Plugin: Issue/PR hygiene and dependency triage for OSS maintainers. Covers automations A013, A061, A062, A063, A064, A065, A066, A067, A088. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Open-Source Maintenance Plugin.
---

# Open-Source Maintenance Plugin

LevelUpWorld / agent-ops priority plugin skill. Automations: **A013, A061, A062, A063, A064, A065, A066, A067, A088**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A013, A061, A062, A063, A064, A065, A066, A067, A088, or when the user asks for Open-Source Maintenance Plugin outcomes.

## Instruction routine

1. Triage dependency vulnerabilities into prioritized issue drafts (A013).
2. Classify issues, plan implementations, link PRs, and care for stale PRs (A061–A064).
3. Draft merge-conflict resolutions without force-push (A065).
4. Validate commit-message policy and propose housekeeping with approval for deletion (A066–A067).
5. Maintain regulatory/watchlist awareness for maintained packages (A088).

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
- Blueprints: `.cursor/automations/` for A013, A061, A062, A063, A064, A065, A066, A067, A088
