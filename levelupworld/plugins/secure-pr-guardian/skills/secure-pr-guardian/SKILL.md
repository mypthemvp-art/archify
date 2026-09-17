---
name: secure-pr-guardian
description: >-
  Secure PR Guardian: Immediate leverage for every repository. Covers automations A003, A004, A007, A011, A021, A026, A031, A068. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Secure PR Guardian.
---

# Secure PR Guardian

LevelUpWorld / agent-ops priority plugin skill. Automations: **A003, A004, A007, A011, A021, A026, A031, A068**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A003, A004, A007, A011, A021, A026, A031, A068, or when the user asks for Secure PR Guardian outcomes.

## Instruction routine

1. Collect PR diff, changed paths, and CI status with read-only GitHub/git tools.
2. Run license, secret, OWASP, API, OpenAPI, test-gap, and CI-workflow checks covered by A003/A004/A007/A011/A021/A026/A031/A068.
3. Never echo secrets; redact matches and attach revoke checklist items.
4. Emit PR risk score, owners, and ranked remediation without mutating the repository.
5. Only draft follow-up issues/PRs through approval-gated plan_* tools.

## Archify pilot (Weeks 7–8)

- Pilot exit automations: **A003, A004, A021**
- Local evidence runner: `node levelupworld/pilots/archify/scripts/run-secure-pr-guardian.mjs`
- Certify before expanding: `node levelupworld/pilots/archify/scripts/certify-pilot.mjs`
- MCP: prefer `.cursor/mcp.pilot.json` (no `github-write`)

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
- Blueprints: `.cursor/automations/` for A003, A004, A007, A011, A021, A026, A031, A068
