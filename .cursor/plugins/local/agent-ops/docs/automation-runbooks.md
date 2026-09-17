# Agent-ops automation runbooks

See the full catalog at `levelupworld/docs/CATALOG.md` and per-automation blueprints in `.cursor/automations/`.

## Quick paths

- PR security → Secure PR Guardian
- Incident / failed CI → Production Triage Copilot
- Migration PR → Database Change Guardian *(expand only after Weeks 7–8 pilot cert)*
- Release window → GitOps Release Controller (+ Multi-agent release commander A100)
- MCP expansion → MCP Security Gateway first

## Archify pilot (Weeks 7–8)

```bash
node levelupworld/pilots/archify/scripts/run-pilot.mjs
node levelupworld/pilots/archify/scripts/certify-pilot.mjs
```

Use `.cursor/mcp.pilot.json` and obey `.cursor/rules/pilot-secure-pr-and-triage.mdc`.
