# LevelUpWorld

Governed **Cursor automations platform** for this repository: 100 narrowly scoped automation blueprints composed from MCP connectors, Cursor Rules / Skills / Hooks / Plugins, and approval-gated operational workflows.

The strongest approach is **not** to install 100 broad-permission tools at once. Build a small plugin platform that composes least-privilege capabilities behind an MCP Security Gateway.

## What landed in this repo

| Path | Purpose |
|---|---|
| [`docs/CATALOG.md`](docs/CATALOG.md) | Full 100-automation catalog |
| [`docs/catalog.json`](docs/catalog.json) | Machine-readable catalog |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Recommended architecture + plugin layout |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Four-phase implementation plan + definition of done |
| [`docs/POLICY_HOOK.md`](docs/POLICY_HOOK.md) | Pre-tool policy-hook pseudocode + approval binding |
| [`plugins/`](plugins/) | Six highest-priority Cursor plugins |
| [`.cursor-plugin/marketplace.json`](../.cursor-plugin/marketplace.json) | Multi-plugin marketplace manifest |
| [`.cursor/skills/levelupworld/`](../.cursor/skills/levelupworld/) | Project skill instruction routines |
| [`.cursor/rules/`](../.cursor/rules/) | Mandatory safety Rules |
| [`.cursor/hooks.json`](../.cursor/hooks.json) + [`hooks/`](../.cursor/hooks/) | Pre-tool policy hooks |
| [`.cursor/mcp.json`](../.cursor/mcp.json) | Starter read-only MCP configuration |
| [`.cursor/automations/`](../.cursor/automations/) | 100 automation blueprints (config-as-code ready) |

## Highest-priority plugins

1. **Secure PR Guardian** — secret scan, vuln triage, API review, threat-model delta, CI hardening, PR risk summary
2. **MCP Security Gateway** — permission lint, redaction, approval proxy, spend governor, injection firewall, replay harness
3. **Production Triage Copilot** — failed-CI, incident timeline, error clustering, traces, SLO burn, K8s diagnostics
4. **Database Change Guardian** — tenant isolation, slow queries, migration safety, backup evidence, retention
5. **GitOps Release Controller** — release checklist, canary, rollback PRs, provenance, Helm readiness, drift
6. **Compliance Evidence Engine** — SOC 2 / HIPAA / NIST mapping, access reviews, vendor assessments, remediation tracking

## Quick start for agents

1. Discover skills under `.cursor/skills/levelupworld/` (catalog router + six priority skills).
2. Obey always-on Rules in `.cursor/rules/levelupworld-*.mdc`.
3. For a scheduled/event workflow, open the matching blueprint in `.cursor/automations/aNNN-*.md` and follow its mutation class (`none` / `plan` / `apply`).
4. Prefer Archify (`archify` skill) when an automation needs an architecture / workflow / incident diagram (`A092`).

## Regenerate catalog

```bash
node levelupworld/scripts/generate-catalog.mjs
```

## Sources (research baseline)

Cursor automations / skills / hooks / plugins docs; OpenAI MCPKit authenticated scaffolds; official MCP reference servers. MCP standardizes the tool interface but does **not** make a connector safe—permissions, validation, approval gates, logging, and hostile-content handling remain our responsibility.
