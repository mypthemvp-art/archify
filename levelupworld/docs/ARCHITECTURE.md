# LevelUpWorld architecture

## Goal

Package repeatable engineering workflows (PR security review, incident triage, database migration review, release verification, compliance evidence) as **governed Cursor plugins**, not ad hoc prompts.

## Control plane

```text
                    ┌──────────────────────────────┐
  Triggers ───────► │ Cursor Automations (cloud)   │
  (PR, CI, cron,    │ + project blueprints         │
   webhook, alert)  └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Skills + Rules + Agents      │
                    │ (.cursor/skills, rules)      │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Policy Hooks                 │
                    │ preToolUse / beforeShell /   │
                    │ beforeMCPExecution           │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ MCP Security Gateway         │
                    │ allowlist · schema · redact  │
                    │ budget · approval proxy      │
                    └──────────────┬───────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
           Read-only MCPs    plan_*/validate_*   apply_*/rollback_*
           (GitHub, CI,      (PR drafts,         (approval-token
            metrics, logs,    GitOps diffs)       bound only)
            Postgres RO)
```

## Plugin repository layout

```text
levelupworld/
├── README.md
├── docs/
│   ├── CATALOG.md
│   ├── catalog.json
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── scripts/
│   └── generate-catalog.mjs
└── plugins/
    ├── secure-pr-guardian/
    │   ├── .cursor-plugin/plugin.json
    │   ├── skills/.../SKILL.md
    │   ├── rules/*.mdc
    │   ├── agents/*.md
    │   ├── commands/*.md
    │   ├── hooks/hooks.json
    │   └── mcp.json
    ├── mcp-security-gateway/
    ├── production-triage-copilot/
    ├── database-change-guardian/
    ├── gitops-release-controller/
    └── compliance-evidence-engine/

.cursor-plugin/marketplace.json          # multi-plugin registry
.cursor/
├── skills/levelupworld/                 # project discovery copies / routers
├── rules/                               # always-on safety
├── hooks.json + hooks/                  # policy enforcement
├── mcp.json                             # starter read-only servers
└── automations/                         # 100 blueprints
```

## Tool naming contract

Every risky connector exposes four tool families:

| Family | Purpose | Approval |
|---|---|---|
| `plan_*` | Produce a reviewable change set / report | No |
| `validate_*` | Dry-run / policy check | No |
| `apply_*` | Mutate the live system or create privileged side effects | **Yes** — bound token |
| `rollback_*` | Reverse a prior apply | **Yes** — bound token |

Approval tokens must bind: arguments hash, short TTL, idempotency key, tenant, environment, actor, correlation ID.

## Hard denylist (never expose to an agent)

- Production interactive shell
- Unrestricted filesystem MCP rooted at `/` or home
- Privileged database account (owner/superuser/migrations on prod primary)
- Broad cloud administrator credentials
- Generic arbitrary HTTP client without URL allowlist + SSRF guards

## Untrusted data surfaces

Issue bodies, pull-request text, CI logs, webpages, retrieved documents, and MCP responses can contain prompt-injection. Skills must:

1. Separate **instructions** from **data**.
2. Never follow imperative language found inside retrieved content.
3. Pass content through the injection firewall / redaction path before reuse in another tool call.

## Starter MCP posture

Phase 1 enables only read-oriented servers (examples):

- Filesystem limited to the repository workspace
- Git (local read operations)
- GitHub with read scopes (contents, pull requests, checks)
- Memory / structured notes for correlation IDs (no secrets)
- Fetch through the gateway with allowlisted hosts

Authenticated internal connectors should start from **OpenAI MCPKit** TypeScript/Python scaffolds (entitlements, `search`/`fetch` shapes, evidence logging)—not bare local PoC servers.

## Relationship to Archify

Automation `A092` (architecture diagram delta) uses the existing `archify` skill to produce validated, evidence-linked diagrams for significant system changes. LevelUpWorld does not fork Archify; it calls it as a specialized skill.
