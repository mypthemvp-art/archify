# Agent-ops local plugin

Composable, policy-gated Cursor plugin packaging LevelUpWorld rules, skills, hooks, MCP starters, and runbooks.

See [`levelupworld/README.md`](../../../../levelupworld/README.md) and [`levelupworld/docs/CATALOG.md`](../../../../levelupworld/docs/CATALOG.md).

## Layout

- `skills/` — 12 priority skills + catalog router
- `rules/` — security, database-safety, release-policy
- `hooks/` — pre-tool policy check + post-tool audit log
- `mcp.json` — starter read-only + policy gateway configuration
- `mcp-servers/` — github, postgres-readonly, ci-observer, policy-engine, approval-gateway stubs
- `docs/automation-runbooks.md` — quick routing guide

Keep secrets in the OS keychain, Vault, or CI secret manager — never commit them.
