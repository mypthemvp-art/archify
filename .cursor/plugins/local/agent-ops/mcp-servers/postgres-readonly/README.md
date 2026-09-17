# postgres-readonly

Placeholder for a narrowly scoped MCP server.

- Phase 1: read-only / policy stubs only
- Authenticate with least privilege; never embed long-lived secrets in the repo
- Prefer OpenAI MCPKit authenticated TypeScript/Python scaffolds for internal connectors
- Expose `plan_*` / `validate_*` / `apply_*` / `rollback_*` only when the gateway and approval service are live
