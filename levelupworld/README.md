# LevelUpWorld / agent-ops

Governed **Cursor + Open-Source OpenAI/MCP automation catalog** for secure AI-agent SaaS development.

**Design principle:** treat every connector as an untrusted capability. Separate read-only discovery from mutations; minimize OAuth scopes; make writes explicit, reviewable, idempotent, and logged.

## What landed

| Path | Purpose |
|---|---|
| [`docs/CATALOG.md`](docs/CATALOG.md) | Exact 100 automation blueprints |
| [`docs/catalog.json`](docs/catalog.json) | Machine-readable catalog v2 |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Control plane + plugin layout |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Four-phase plan + definition of done |
| [`docs/POLICY_HOOK.md`](docs/POLICY_HOOK.md) | Pre-tool policy pseudocode |
| [`plugins/`](plugins/) | Twelve priority Cursor plugins |
| [`.cursor/plugins/local/agent-ops/`](../.cursor/plugins/local/agent-ops/) | Packaged local plugin (rules/skills/hooks/mcp-servers) |
| [`.cursor/skills/levelupworld/`](../.cursor/skills/levelupworld/) | Project skill instruction routines |
| [`.cursor/rules/`](../.cursor/rules/) | Mandatory safety Rules |
| [`.cursor/hooks.json`](../.cursor/hooks.json) | Policy + audit hooks |
| [`.cursor/mcp.json`](../.cursor/mcp.json) | Starter read-only + policy MCP config |
| [`.cursor/automations/`](../.cursor/automations/) | 100 automation blueprints |

## Build the 12 plugins first

1. Secure PR Guardian
2. MCP Security Gateway *(before broad connectors)*
3. Production Triage Copilot
4. Database Change Guardian
5. GitOps Release Controller
6. Compliance Evidence Engine
7. FeatureOps Plugin
8. Accessibility QA Plugin
9. Repository Intelligence Plugin
10. Cloud Cost Governor
11. Privacy Engineering Plugin
12. Open-Source Maintenance Plugin

## MCP Registry + Policy Gateway

Control plane (catalog/certify) + server-side gateway (authz, approvals, redaction, budgets, audit):

- Blueprint: [`registry/docs/BLUEPRINT.md`](registry/docs/BLUEPRINT.md)
- Implementation starter: [`registry/docs/IMPLEMENTATION-STARTER.md`](registry/docs/IMPLEMENTATION-STARTER.md)
- Certification checklist: [`registry/docs/CERTIFICATION.md`](registry/docs/CERTIFICATION.md)
- Run: see [`registry/README.md`](registry/README.md)
- Dashboard pages: Catalog · Test Lab · Operations · Audit · Approvals
- Top-10 connectors: [`registry/connectors/`](registry/connectors/)

## Quick start

1. Discover skills under `.cursor/skills/levelupworld/` or `.cursor/plugins/local/agent-ops/skills/`.
2. Obey Rules in `.cursor/rules/` (also mirrored under `agent-ops/rules/`).
3. Open a blueprint in `.cursor/automations/` and create a Cursor Automation via `/automate`.
4. Keep secrets in OS keychain / Vault / CI — never commit them.

```bash
node levelupworld/scripts/generate-catalog.mjs
node levelupworld/scripts/scaffold-plugins.mjs
node levelupworld/scripts/check-contract.mjs
```
