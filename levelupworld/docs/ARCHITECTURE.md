# LevelUpWorld / agent-ops architecture

## Purpose

Secure AI-agent SaaS automations for FastAPI, TypeScript, PostgreSQL, Redis, Docker, Kubernetes, GitHub Actions, Terraform, policy enforcement, and audited human approval.

**Design principle:** treat every connector as an untrusted capability. Separate read-only discovery from mutations; minimize OAuth scopes; make writes explicit, reviewable, idempotent, and logged.

## Control plane

```text
Cursor IDE / Cursor CLI / Cursor Automations
                |
        Project plugin package
  (rules + skills + hooks + mcp.json)
                |
        MCP capability gateway
  authn | RBAC/ABAC | policy | budgets | audit
        |             |            |
   Read-only tools  Approval queue  Write tools
        |             |            |
 GitHub / CI / DB / cloud / docs / tickets / observability
```

## Suggested local plugin package

```text
.cursor/plugins/local/agent-ops/
├── plugin.json
├── .cursor-plugin/plugin.json
├── skills/                      # 12 priority skills + catalog router
├── rules/                       # security, database-safety, release-policy
├── hooks/                       # pre-tool policy + post-tool audit
├── mcp.json                     # starter read-only + policy gateway
├── mcp-servers/
│   ├── github/
│   ├── postgres-readonly/
│   ├── ci-observer/
│   ├── policy-engine/
│   └── approval-gateway/
└── docs/automation-runbooks.md
```

Project discovery also mirrors skills and rules at:

- `.cursor/skills/levelupworld/`
- `.cursor/rules/`
- `.cursor/hooks.json` + `.cursor/hooks/`
- `.cursor/mcp.json`
- `.cursor/automations/` (100 blueprints)

## Automation contract

Each automation must provide:

1. **Trigger** — slash command, prompt, PR/issue event, deployment signal, schedule, or webhook
2. **Inputs** — repository, environment, tenant, time range, policy context
3. **Plan** — dry-run with impacted objects, risk, expected changes
4. **Guardrails** — allowlists, schema validation, least privilege, redaction, rate limits, timeout, concurrency key, budgets
5. **Approval** — required for production writes, external communications, deletes, migrations, spending
6. **Evidence** — immutable audit event (actor, tool, args hash, decision, result hash, correlation ID)
7. **Verification** — tests, policy check, health check, rollback guidance, concise artifact

## Tool naming

| Family | Purpose | Approval |
|---|---|---|
| `plan_*` | Reviewable change set / report | No |
| `validate_*` | Dry-run / policy check | No |
| `apply_*` | Live mutation / privileged side effect | **Yes** |
| `rollback_*` | Reverse a prior apply | **Yes** |

## Hard denylist

- Production interactive shell
- Unrestricted filesystem rooted outside the workspace
- Privileged database account on a production primary
- Broad cloud administrator credentials
- Generic unrestricted HTTP client without allowlist + SSRF guards

## Initial MCP stack

GitHub read-only, Git, filesystem sandbox, docs/fetch via gateway, CI logs, Playwright for test environments, Postgres read-only, policy/approval MCP, audit MCP. Expand only behind the MCP Security Gateway.

Authenticated internal connectors should start from **OpenAI MCPKit** TypeScript/Python scaffolds (entitlements, `search`/`fetch` shapes, evidence logging).
