# Multi-Tenant Interactive MCP Registry Dashboard — Full Specification

**Status:** authoritative product + architecture specification for `levelupworld/registry/`  
**Central rule:** the dashboard is a **control plane**; actual MCP tool calls route through a separate, authoritative **policy gateway**. Cursor hooks are local preflight/postflight only.

This document expands [`IMPLEMENTATION-STARTER.md`](IMPLEMENTATION-STARTER.md) and [`BLUEPRINT.md`](BLUEPRINT.md) for a registry that can catalog, filter, security-test, certify, activate, monitor, and quarantine **100+** MCP connectors.

---

## 1. Design recommendation

| Plane | Responsibility |
|---|---|
| **Registry dashboard (control plane)** | Discover, filter, certify, activate, monitor, quarantine connector versions |
| **Policy gateway (data plane)** | Authenticate, authorize, validate args, bind approvals, redact, budget, audit, quarantine enforce |
| **Cursor hooks** | Local preflight/postflight — never the sole authorization boundary |
| **Connector runtime** | Narrow integration — never sole authz |

The gateway must independently enforce: authorization, tenant scope, argument validation, approval grants, audit logs, budgets, response redaction, and emergency quarantine.

---

## 2. Product model

Entities the control plane must represent:

| Entity | Purpose |
|---|---|
| Organization | Top-level tenancy boundary |
| Team | Ownership, escalation, CODEOWNERS-aligned groups |
| Project | Cursor/repo binding; activation target |
| Tenant | Data isolation dimension inside an org |
| Principal | User or workload identity with roles |
| Connector owner | Named team + escalation contact (required for certification) |
| Connector / Connector version | Pinned semver + immutable digest + manifest |
| Tool contract | Name, capability, JSON Schema, risk, approval required, policy key |
| Certification | Suite results, supply-chain evidence, expiry, reviewer |
| Activation | Project × environment binding; enabled flag |
| Policy | Versioned decision rules + decision log |
| Approval request / grant | Human intent → short-lived args_hash-bound token |
| Health | Success rate, p95, errors, denial rates, budget |
| Audit event | Tamper-evident invocation + policy evidence |

### Trust tiers

`unverified` → `sandboxed` → `reviewed` → `certified` → `production_critical`

### Certification / lifecycle states

`draft` · `in_lab` · `failed` · `certified` · `quarantined` · `deprecated`

### Tool capabilities

`read` · `write` · `delete` · `external_communication` · `command_execution`

---

## 3. Interactive catalog (100+ connectors)

**Presentation default:** virtualized **table first**. Cards are an optional discovery mode only.

### Filter URL model

```text
/registry?category=database,observability
  &operation=read
  &trustTier=3,4
  &environment=production
  &health=healthy,degraded
  &certExpiresBefore=2026-10-16
  &sort=-activity_24h
```

### Recommended filters

- Connector name, tool name, source repository, owner, tags
- **Category:** GitHub, CI/CD, database, documentation, browser testing, observability, cloud, Kubernetes, infrastructure, security, compliance, messaging, analytics, feature flags
- **Capability / operation:** read, write, delete, external communication, command execution
- Trust tier, certification status, lifecycle state, certification expiration
- Development / staging / production eligibility and activation
- **Transport:** stdio, Streamable HTTP, legacy HTTP/SSE, gateway proxy
- **Authentication:** OAuth, workload identity, mTLS, API key, none
- **Data classification:** public, internal, confidential, regulated, PHI, PCI, secrets
- Health, p95 latency, 24h success rate, error rate, approval-denial rate, budget usage
- Image signature, SBOM, provenance, current CVEs, last pentest, last certification date
- Outbound domains, data residency, active project bindings, tool counts

### Connector detail page

Tabs / sections:

1. Overview (owner, trust, cert state, environments, digest)
2. Tools + JSON Schemas
3. OAuth / workload scopes
4. Supply-chain evidence (SBOM, signature, provenance, CVEs)
5. Security test results
6. Monitoring (latency, success, denials)
7. Audit events (correlation-linked)
8. Activation state (per project/environment)
9. Emergency quarantine action

---

## 4. Security test lab

Runs against an **ephemeral isolated environment** — not production. Synthetic data, test-only OAuth clients, egress allowlists, CPU/memory/time quotas, temporary credentials.

| Test family | Examples |
|---|---|
| MCP protocol | Initialization, tool discovery, schema validation, malformed inputs |
| Authentication | Missing/expired tokens, wrong audience, insufficient scope |
| Authorization | Tenant escape, project/environment mismatch, resource allowlist bypass |
| Input safety | SQL injection, path traversal, shell metacharacters, malformed URLs, oversized requests |
| SSRF and egress | Metadata endpoints, private IPs, redirect chains, DNS rebinding, unapproved hostnames |
| Data protection | Secret/PII/PHI redaction; output-size caps; retention |
| Prompt injection | Hostile issues, logs, webpages, documents, connector responses |
| Reliability | Timeouts, retries, circuit breakers, partial failures, duplicates |
| Approval binding | Argument changes, replay, expiry, wrong user/project/tenant/environment |
| Supply chain | Signed source/image, immutable digest, SBOM, vulnerability policy |
| Auditability | Correlation IDs, policy evidence, tamper-evident events, trace linkage |

### Hard certification failures (not score reductions)

Fail certification outright if any of:

- No pinned image digest
- Missing owner / escalation contact
- Embedded credentials in manifest or config
- Unrestricted egress
- Broken tenant authorization
- Unprotected write/delete/external tool (no approval requirement)
- Missing immutable audit evidence

---

## 5. Postgres guidance

See executable DDL:

- [`../schema/001_init.sql`](../schema/001_init.sql) — foundation
- [`../schema/002_implementation_starter.sql`](../schema/002_implementation_starter.sql) — activations, test runs, invocations
- [`../schema/003_rls_policies.sql`](../schema/003_rls_policies.sql) — `app.org_id` RLS
- [`../schema/004_multi_tenant_dashboard.sql`](../schema/004_multi_tenant_dashboard.sql) — teams, principals, richer catalog dimensions, audit partitioning notes

**RLS pattern:** application sets `SELECT set_config('app.org_id', …, true)` per request; policies compare `org_id::text = app_org_id()`.

**Audit volume:** partition `tool_invocations` / audit tables by month (`occurred_at`); keep hot indexes on `(org_id, occurred_at DESC)` and `correlation_id`.

---

## 6. REST API surface (control plane + gateway)

| Area | Examples |
|---|---|
| Catalog | `GET /api/v1/connectors` with multi-filters + sort |
| Versions | publish, pin, get by slug/version |
| Testing | `POST …/test-runs`, `GET /api/v1/test-runs/{id}` |
| Certification | promote / fail / expire |
| Activation | request, approve, list by project |
| Approvals | create, decide, grant verify (gateway) |
| Monitoring | `GET /api/v1/metrics/connectors` |
| Audit | `GET /api/v1/audit/invocations` |
| Policy | `POST /api/v1/policy/evaluate`, decision log |
| Health | `GET /healthz` |
| Gateway invoke | `POST /api/v1/gateway/invoke` |
| Quarantine | `POST /api/v1/connectors/{slug}/quarantine` |
| Auth | `GET /api/v1/auth/whoami`, IdP modes |

Gateway authorization must not accept raw connector URLs, raw production credentials, arbitrary tenant IDs, or arbitrary cloud account selection from the client.

---

## 7. Cursor hooks pattern (adaptable)

Hook **names and payloads differ across Cursor releases**. Treat the following as a project-level pattern; keep runtime scripts fail-closed for preflight.

```json
{
  "version": 1,
  "hooks": {
    "beforeMCPExecution": [
      {
        "matcher": "mcp__*",
        "command": "node .cursor/hooks/preflight-mcp.mjs",
        "timeoutSeconds": 8,
        "failClosed": true,
        "description": "Authorize and bind MCP calls through the registry policy gateway"
      }
    ],
    "afterMCPExecution": [
      {
        "matcher": "mcp__*",
        "command": "node .cursor/hooks/postflight-mcp.mjs",
        "timeoutSeconds": 8,
        "failClosed": false,
        "description": "Redact output indicators and emit MCP audit completion events"
      }
    ],
    "beforeShellExecution": [
      {
        "matcher": "*",
        "command": "node .cursor/hooks/preflight-command.mjs",
        "timeoutSeconds": 5,
        "failClosed": true,
        "description": "Block destructive and production infrastructure commands"
      }
    ],
    "afterShellExecution": [
      {
        "matcher": "*",
        "command": "node .cursor/hooks/secret-scan-output.mjs",
        "timeoutSeconds": 5,
        "failClosed": false,
        "description": "Detect accidental secret material in command output"
      }
    ]
  }
}
```

**Security principle:** pre-tool hook sends tool name + **arguments hash** to policy; the backend repeats all checks and makes the final decision.

Reference TypeScript examples (documentation / future compile target): [`.cursor/hooks/examples/`](../../../.cursor/hooks/examples/).

---

## 8. Approval-gate rule

For production-impacting writes, do **not** rely only on a Cursor approval click. The approval service issues a short-lived grant bound to:

```text
actor / workload identity
organization, project, and tenant
connector version ID
exact tool ID
canonical normalized-arguments hash
target environment
idempotency key
policy version
not-before and expiration times
required approver count and identities
```

The gateway **rejects** execution if any attribute changes, and **atomically consumes** the grant (no replay / duplicate execution).

See [`APPROVAL-TOKENS.md`](APPROVAL-TOKENS.md).

---

## 9. Core runtime rule — single gateway endpoint

```json
{
  "mcpServers": {
    "org-mcp-gateway": {
      "url": "https://mcp-gateway.example.com/mcp",
      "headers": {
        "X-Project-ID": "agent-platform",
        "X-Requested-Environment": "development"
      }
    }
  }
}
```

The gateway resolves only **certified, activated, non-quarantined, pinned** connector versions.

Project examples: [`.cursor/mcp.gateway.example.json`](../../../.cursor/mcp.gateway.example.json), [`.cursor/mcp.pilot.json`](../../../.cursor/mcp.pilot.json).

---

## 10. Operational requirements

### SLOs (targets)

| Signal | Target |
|---|---|
| Gateway policy evaluate p95 | < 50 ms (local cache warm) |
| Gateway invoke overhead p95 (ex-connector) | < 150 ms |
| Audit durability | 100% of allow/deny/require_approval decisions persisted |
| Quarantine propagation | < 60 s to deny at gateway |
| Certification suite wall clock | < 15 min per connector version |

### Quarantine procedure

1. Dashboard or API sets version `quarantined` + reason + actor.
2. Gateway denylist cache invalidated / version marked quarantined.
3. Activations disabled; Cursor local mcp.json entries ignored for that version.
4. Incident ticket + audit event with correlation IDs.
5. Re-entry requires new certification suite pass + owner approval.

### Onboarding criteria (new connector)

Pinned digest, owner, escalation, tool schemas, capability labels, egress allowlist, no embedded secrets, sandbox suite green, approval on all non-read tools, audit evidence path proven.

### Anti-patterns

- Treating Cursor hooks as the authorization boundary
- Putting production DB/cloud credentials in project `mcp.json`
- Marketplace-only UX without table filters at 100+ scale
- Soft-failing hard certification gates with a numeric score
- Accepting client-supplied connector URLs or tenant IDs unchecked
- Reusing approvals after argument mutation

---

## 11. Phased milestones (post Weeks 1–8)

| Phase | Outcome |
|---|---|
| **A — Spec + filters** | This document; multi-filter catalog API; table-first dashboard |
| **B — Multi-tenant DDL** | Teams/principals/tags; audit partitions; richer RLS |
| **C — Test lab depth** | Full suite families executable in ephemeral lab |
| **D — UI productization** | Next.js virtualized table, detail tabs, ops charts |
| **E — Scale to 100+** | Bulk import, CVE posture feeds, cert expiry workflows |

Current executable scaffold covers Weeks 1–8 (registry, gateway, IdP/RLS, OTEL, cert CI, github-write grants, Archify pilot). Phase A–B land with this specification drop.

---

## 12. Sources (external context)

Design informed by public guidance on Cursor hardening, agent hooks as a governance interface, and MCP’s ability to connect agents to databases, APIs, and remote services — which is exactly why the gateway must remain authoritative.

1. Checkmarx — Cursor AI Security Risks / critical controls  
2. Speakeasy — AI agent hooks as governance interface  
3. AxonFlow — Cursor IDE integration notes  
4. howtoharden.com — Cursor Hardening Guide  
