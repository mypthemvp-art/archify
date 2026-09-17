# Archify Weeks 7–8 pilot certification

Pilot repository: **this repo** (`archify`).  
Plugins under test: **Secure PR Guardian**, **Production Triage Copilot**.

## Scope (do not expand until this checklist is green)

| Plugin | Exit automations | Mutation |
|---|---|---|
| Secure PR Guardian | A003, A004, A021 | none |
| Production Triage Copilot | A024, A040 | none |

Allowed connectors: see `pilot.manifest.json` → `connectors_allowed`.  
Denied connectors include `github-write` and all hard denylist tools for the pilot window.

## Checklist

- [x] Skills + blueprints present for exit automations
- [x] `.cursor/mcp.pilot.json` routes through gateway + read-only MCP only
- [x] Policy hooks deny denylist / ask on `apply_*`
- [x] Pilot runners emit JSON+Markdown evidence with `correlation_id` and `mutation: none`
- [x] `node levelupworld/pilots/archify/scripts/certify-pilot.mjs` passes
- [x] GitHub Actions `pilot-cert.yml` runs certify on pilot/registry changes
- [ ] Human review of one Secure PR Guardian evidence bundle on a real PR
- [ ] Human review of one Production Triage evidence bundle on a real CI failure
- [ ] Expand to Database Change Guardian only after the two human reviews above

## Commands

```bash
# Produce evidence for both plugins
node levelupworld/pilots/archify/scripts/run-pilot.mjs

# Certify before expanding
node levelupworld/pilots/archify/scripts/certify-pilot.mjs
```

Evidence lands in `levelupworld/pilots/archify/evidence/runs/` (gitignored). Schema: `evidence/schema.json`.

## Cursor usage

1. Prefer `.cursor/mcp.pilot.json` (or copy servers into project mcp.json).
2. Load skills `secure-pr-guardian` / `production-triage-copilot`.
3. Obey `.cursor/rules/pilot-secure-pr-and-triage.mdc`.
4. Do **not** enable `github-write` until a separate grant-bound expansion review.
