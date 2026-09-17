# Archify pilot — Secure PR Guardian + Production Triage Copilot

Weeks 7–8 delivery: run both priority plugins in **one repository** (this one), produce evidence-backed reports with **zero mutate tools**, and certify before expanding.

## Quick start

```bash
node levelupworld/pilots/archify/scripts/run-pilot.mjs
node levelupworld/pilots/archify/scripts/certify-pilot.mjs
```

| Script | Automations | Output |
|---|---|---|
| `run-secure-pr-guardian.mjs` | A003, A004, A021 | License inventory, secret scan (redacted), PR risk score |
| `run-production-triage.mjs` | A024, A040 | CI failure hypotheses + incident timeline |
| `certify-pilot.mjs` | gate | Fails closed if MCP/policy/evidence contract breaks |

## Package map

- Manifest: [`pilot.manifest.json`](pilot.manifest.json)
- Certification: [`CERTIFICATION.md`](CERTIFICATION.md)
- Fixtures: [`fixtures/`](fixtures/)
- Evidence schema: [`evidence/schema.json`](evidence/schema.json)
- Cursor rule: [`.cursor/rules/pilot-secure-pr-and-triage.mdc`](../../../.cursor/rules/pilot-secure-pr-and-triage.mdc)
- Pilot MCP: [`.cursor/mcp.pilot.json`](../../../.cursor/mcp.pilot.json)

## Safety

- Mutation policy: **none** for the pilot window
- `github-write` is denied in the pilot allowlist even though the gateway supports grant-bound dry-run PRs
- All findings that may contain secrets are redacted before evidence write
