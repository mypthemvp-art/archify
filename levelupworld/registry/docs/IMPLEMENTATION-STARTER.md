# Custom MCP Registry Dashboard — Implementation Starter

Production-oriented blueprint for a **self-hosted MCP Registry** that lets a team discover, filter, certify, test, approve, monitor, and revoke MCP connectors used by Cursor and other MCP-capable clients.

**Full multi-tenant specification (authoritative):** [`MULTI-TENANT-DASHBOARD-SPEC.md`](MULTI-TENANT-DASHBOARD-SPEC.md)

This document is the product contract for `levelupworld/registry/`. Executable pieces already scaffolded: Postgres schema, FastAPI control plane + gateway, dashboard pages, top-10 connector manifests, approval grants, and Cursor hooks.

## Product scope

### User flows

1. Browse all connectors and filter by category, transport, trust tier, owner, environment, risk, and certification state.
2. Open a connector detail page showing manifest, tools, permissions, OAuth scopes, data classifications, test history, current health, audit volume, and known risks.
3. Run a sandbox test suite against a pinned connector version.
4. Request activation of a connector into a named Cursor project/environment.
5. Route sensitive tool operations through a policy/approval gateway.
6. Monitor tool-call success, latency, approval denials, policy denials, token/cost use, and security events.
7. Quarantine or revoke a connector/version immediately.

## Core architecture

```text
                           ┌───────────────────────────┐
                           │ Cursor / CLI / Automations │
                           └─────────────┬─────────────┘
                                         │ project mcp.json
                         ┌───────────────▼───────────────┐
                         │ MCP Registry Control Plane     │
                         │ catalog | certification | RBAC │
                         └───────────┬───────────┬───────┘
                                     │           │
                      ┌──────────────▼───┐ ┌────▼─────────────────┐
                      │ Policy Gateway   │ │ Registry Dashboard   │
                      │ authz | approval │ │ catalog/detail/lab   │
                      │ redaction | audit│ │ ops/audit/approvals  │
                      └───────┬──────────┘ └──────────────────────┘
                              │
              ┌───────────────┼─────────────────────────┐
              │               │                         │
    ┌─────────▼──────┐ ┌──────▼────────┐      ┌────────▼─────────┐
    │ Read-only MCPs │ │ Approval MCP  │      │ Write-capable MCP │
    │ docs/git/CI/db │ │ signed grants │      │ GitHub/flags/IaC  │
    └────────────────┘ └───────────────┘      └──────────────────┘
                              │
                      ┌───────▼────────┐
                      │ OpenTelemetry  │
                      │ audit / SIEM   │
                      └────────────────┘
```

### Trust boundaries

| Plane | Answers / enforces |
|---|---|
| **Registry** | What connector/version exists, who owns it, whether it is certified, where it may be used |
| **Gateway** | Who may invoke a tool, on which tenant/environment, with which arguments/approval/budget |
| **Connector** | Narrow integration task — never the sole authorization layer |
| **Cursor hook** | Local preflight/postflight — supplements, does not replace the gateway |

## Stack recommendation

| Layer | Recommended implementation |
|---|---|
| Dashboard | Next.js, TypeScript, Tailwind, shadcn/ui, TanStack Query, ECharts/Recharts *(current scaffold: FastAPI + Jinja; migrate UI when productizing)* |
| API | FastAPI; OpenAPI contract; async job worker |
| Registry DB | PostgreSQL with RLS for organization/tenant partitioning |
| Cache/job queue | Redis + Arq/Celery/BullMQ |
| MCP gateway | TypeScript (OpenAI MCPKit) or FastMCP/Python; Streamable HTTP for remote; stdio only for trusted local dev |
| Policy | OPA/Rego or Cedar; versioned policies and decision logs |
| Approval | Postgres workflow + short-lived signed JWT/PASETO + WebAuthn/SSO step-up for production |
| Observability | OpenTelemetry, Prometheus, Grafana, Loki/Tempo |
| Secrets | Vault / cloud secret manager; workload identity; no static secrets in manifests |
| Supply chain | OCI images, SBOM, Cosign/Sigstore, provenance attestations, SLSA-oriented CI |

## Gateway decision flow

1. Cursor requests tool call through gateway.
2. Authenticate user/workload; resolve org, project, tenant, environment.
3. Look up exact connector version and tool manifest.
4. Validate JSON Schema, normalize arguments, redact prohibited fields, calculate `args_hash`.
5. Evaluate policy: identity + role + tenant + environment + tool + arguments + risk + budget.
6. If mutation/external action, require unexpired approval bound to connector, tool, `args_hash`, actor, tenant, environment, idempotency key.
7. Invoke connector with delegated short-lived credentials only.
8. Sanitize response for secrets/PII; block instruction-like content from becoming control data.
9. Emit immutable audit event and OpenTelemetry trace.
10. Return a structured, size-limited result to Cursor.

## Cursor project integration

Point one project-level MCP entry at the gateway—not every high-risk service:

```json
{
  "mcpServers": {
    "company-mcp-gateway": {
      "url": "https://mcp-gateway.example.com/mcp",
      "headers": {
        "X-Project-ID": "agent-platform",
        "X-Environment": "development"
      }
    }
  }
}
```

For local development, the scaffold uses a stdio proxy that forwards to `AGENT_OPS_GATEWAY_URL`. Never put bearer secrets in `mcp.json`.

## Non-negotiable operating rules

1. No direct production database write connector in Cursor.
2. No direct Terraform apply, kubectl apply, or cloud-admin connector in Cursor.
3. No generic unrestricted HTTP client MCP server.
4. No connector activation without a pinned version, owner, scope inventory, and test result.
5. No production mutation without exact argument-bound, short-lived server-side approval.
6. No unlogged tool call: every gateway invocation needs a correlation ID and result status.
7. No automatic trust of fetched content, logs, tickets, or PR descriptions.
8. Emergency quarantine must disable a connector version immediately at the gateway—even if it remains installed in a Cursor configuration.

See also: [`CERTIFICATION.md`](CERTIFICATION.md), [`BUILD-SEQUENCE.md`](BUILD-SEQUENCE.md), [`APPROVAL-TOKENS.md`](APPROVAL-TOKENS.md), [`../schema/`](../schema/).
