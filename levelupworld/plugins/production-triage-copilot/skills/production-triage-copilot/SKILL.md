---
name: production-triage-copilot
description: >-
  Production Triage Copilot: Read-only by default for incidents and CI failures. Covers automations A024, A040, A041, A042, A043, A044, A045, A046, A074. Use for
  LevelUpWorld/agent-ops workflows matching those IDs or when the user asks for Production Triage Copilot.
---

# Production Triage Copilot

LevelUpWorld / agent-ops priority plugin skill. Automations: **A024, A040, A041, A042, A043, A044, A045, A046, A074**.

## When to use

Use when an automation blueprint under `.cursor/automations/` matches A024, A040, A041, A042, A043, A044, A045, A046, A074, or when the user asks for Production Triage Copilot outcomes.

## Instruction routine

1. Gather CI logs, metrics, traces, alerts, and related commits with read-only credentials.
2. Build incident timelines, error clusters, log-to-code correlations, and trace explanations (A024, A040–A044, A074).
3. Include slow-query and capacity context when relevant (A045–A046) without mutating systems.
4. Propose mitigations and rollback guidance; do not auto-page externally or apply changes.
5. Stop at the report unless an approval-bound follow-up mutation is explicitly authorized.

## Archify pilot (Weeks 7–8)

- Pilot exit automations: **A024, A040**
- Local evidence runner: `node levelupworld/pilots/archify/scripts/run-production-triage.mjs`
- Certify before expanding: `node levelupworld/pilots/archify/scripts/certify-pilot.mjs`
- MCP: prefer `.cursor/mcp.pilot.json` (read-only + gateway)

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
- Blueprints: `.cursor/automations/` for A024, A040, A041, A042, A043, A044, A045, A046, A074
