---
name: gitops-release-controller
description: >-
  GitOps Release Controller: Separate plan from execution for releases. Covers automations A036, A037, A038, A039, A070, A075, A076, A077, A078, A079, A100. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for GitOps Release Controller.
---

# GitOps Release Controller

LevelUpWorld / agent-ops priority plugin skill. Automations: **A036, A037, A038, A039, A070, A075, A076, A077, A078, A079, A100**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A036, A037, A038, A039, A070, A075, A076, A077, A078, A079, A100, or when the user asks for GitOps Release Controller outcomes.

## Instruction routine

1. Execute gated release checklists without tagging/publishing (A036).
2. Analyze canaries, generate rollback plans, and verify post-release SLOs (A037–A039).
3. Verify supply-chain provenance, Helm readiness, GitOps drift, certs, DNS/edge, and DR score (A070, A075–A079).
4. Prefer GitOps PR generation over direct cluster mutation.
5. Multi-agent release commander (A100) requires final human approval before any apply.

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
- Blueprints: `.cursor/automations/` for A036, A037, A038, A039, A070, A075, A076, A077, A078, A079, A100
