---
name: compliance-evidence-engine
description: >-
  Compliance Evidence Engine: Map control -> evidence source -> freshness -> owner. Covers automations A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Compliance Evidence Engine.
---

# Compliance Evidence Engine

LevelUpWorld / agent-ops priority plugin skill. Automations: **A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090, or when the user asks for Compliance Evidence Engine outcomes.

## Instruction routine

1. Collect control-to-evidence packages with immutable indexing (A080).
2. Monitor SOC 2 / HIPAA / NIST mappings without fabricating evidence or extracting PHI (A081–A083).
3. Coordinate privacy requests and access reviews as plans; approval before disclosure/deletion/revocation (A084–A085).
4. Draft vendor questionnaires and review DPAs with citations (A086–A087).
5. Track regulatory watchlists, remediation plans, and evidence retention (A088–A090).

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
- Blueprints: `.cursor/automations/` for A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090
