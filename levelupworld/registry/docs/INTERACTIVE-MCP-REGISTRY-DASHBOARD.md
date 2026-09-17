# Interactive MCP Registry Dashboard

## Full Product, Security, Data, API, and Cursor Hook Specification

**Purpose:** Build a self-hosted, multi-tenant registry and control plane for 100+ Model Context Protocol (MCP) connectors used by Cursor, background automations, CLI agents, and internal agent platforms.

The system must let engineering and security teams:

- Discover and filter connectors by capability, trust, owner, environment, data class, transport, health, and certification.
- Inspect every connector version, tool contract, dependency/provenance record, OAuth scope, policy, and audit history.
- Run repeatable security audits in a sandbox before a connector is certified or activated.
- Activate only approved connector versions for specific projects and environments.
- Route all runtime tool calls through a policy-and-approval gateway.
- Monitor health, latency, policy denials, approval activity, egress, error rate, budget use, and security anomalies.
- Quarantine a connector/version immediately, even if it remains configured on a developer machine.

> **Security position:** A connector registry is not just a marketplace. It is a capability-management system. The registry records allowed capabilities; the runtime gateway independently enforces them.

**Executable companions:** [`005_full_product_model.sql`](../schema/005_full_product_model.sql) · [`connector-filters.ts`](../types/connector-filters.ts) · [`.cursor/hooks/`](../../../.cursor/hooks/) · [`BUILD-SEQUENCE.md`](BUILD-SEQUENCE.md)

---

## 1. Product model

### 1.1 Terminology

| Term | Meaning |
|---|---|
| Connector | An MCP server integration, such as GitHub, PostgreSQL read-only, CI, observability, document search, or an internal API. |
| Connector version | A pinned immutable release of a connector, normally linked to a source commit and OCI image digest. |
| Tool | A specific MCP-exposed action, such as `get_pull_request`, `search_code`, `create_issue`, or `run_query`. |
| Capability | The effective permission of a tool over data/resources: read, write, delete, external communication, privileged execution. |
| Registry | Catalog/control plane that stores connector manifests, versions, owners, policies, tests, certification, and activation state. |
| Gateway | Runtime service that authenticates, authorizes, validates, approves, budgets, proxies, redacts, and audits calls. |
| Certification | A time-bounded security status applied to a version after automated and human checks. |
| Activation | An approved binding that makes a connector version available for a project and environment. |
| Approval grant | Short-lived server-issued authorization tied to the exact normalized arguments of one sensitive action. |
| Quarantine | Emergency state that blocks a connector version at the gateway immediately. |

### 1.2 Roles

| Role | Permissions |
|---|---|
| Registry viewer | Browse approved metadata and connector health; no activation or test execution |
| Developer | Test sandboxed connectors and request activation; request approval for actions |
| Connector owner | Publish versions, resolve findings, propose manifests, view connector audit records |
| Security reviewer | Approve certification, quarantine versions, configure security test baselines |
| Project administrator | Activate/deactivate certified connectors for projects and environments |
| Production approver | Approve time-bound high-risk actions within assigned scopes |
| Platform operator | Operate gateway, policy engine, observability, and emergency response |

### 1.3 Trust tiers

| Tier | State | Suitable environments | Meaning |
|---:|---|---|---|
| 0 | Unverified | None | Metadata exists but no security evidence; cannot run |
| 1 | Sandboxed | Local development/test | Can execute only in isolated test infrastructure with synthetic credentials/data |
| 2 | Reviewed | Development/staging | Automated audit passed and human review completed; no high-risk production actions |
| 3 | Certified | Development/staging/limited production | Version pinned, attested, tested, policy-bound, and actively monitored |
| 4 | Production-critical | Production | Additional SLO, incident response, dual approval, and continuous evidence requirements |
| Q | Quarantined | None | Gateway denies all calls immediately |

---

## 2. Dashboard UX

### 2.1 Main navigation

```text
Registry
  Catalog
  Connector detail
  Activation requests
Assurance
  Security test lab
  Certification queue
  Policy simulator
Operations
  Live tool calls
  Health and SLOs
  Approval queue
  Audit explorer
Administration
  Owners and teams
  Policies
  Environments
  Egress allowlists
  Quarantine center
```

### 2.2 Catalog dashboard

The catalog must support **100+ connectors** without becoming a grid of vague cards. Use a virtualized table as the default view and offer a card view for discovery.

#### Persistent filter bar

- Free text: name, description, tool name, owner, repository, tag, data source, domain
- Category: source control, workspace, CI/CD, documentation, database, analytics, observability, browser testing, cloud, Kubernetes, IaC, security, compliance, messaging, product analytics, feature flags, financial data
- Capability: read, write, delete, external communication, command execution
- Trust tier and certification state
- Lifecycle: draft, active, deprecated, quarantined, revoked
- Environment: local, development, staging, production
- Transport: stdio, Streamable HTTP, HTTP/SSE legacy, internal gateway proxy
- Data classification: public, internal, confidential, regulated, PHI, PCI, secrets
- Authentication: none, API key, OAuth, workload identity, mTLS, delegated token
- Health: healthy, degraded, failing, unknown
- Owner/team, business unit, repository, source license
- Security attributes: signed image, SBOM, SLSA/provenance, current CVEs, last pentest date, last certification date
- Network egress domain and geographic residency
- Tool count and write/delete tool count

#### Columns

| Column | Meaning |
|---|---|
| Connector | Icon, name, slug, active pinned version |
| Category | Primary business/technical category |
| Tools | Total, read, write, delete, external action counts |
| Trust | Tier and certification status/expiry |
| Health | Current status, p95 latency, 24h success rate |
| Security | Signature, SBOM, vulnerability posture, test status |
| Data | Highest classification and outbound domains |
| Scope | Activated projects/environments |
| Owner | Team, human owner, escalation SLO |
| Activity | 24h tool calls, denials, approvals, anomalies |
| Actions | View, test, request activation, quarantine when authorized |

#### Saved views

Provide built-in and user-saved query views:

- Certified, read-only, production-active
- Production connectors with certification expiring in 30 days
- Write-capable connectors requiring approval
- Connectors with new CVEs or failed audit tests
- Connectors with unusual error rate or egress
- Unowned connectors
- Staging candidates
- Quarantined/revoked versions
- Data connectors accessing confidential or regulated data

### 2.3 Connector detail page

Use a stable URL such as `/registry/connectors/{slug}/versions/{version}`. Render tabs: Overview, Tool inventory, Security and provenance, Test lab, Monitoring, Audit (see product brief for field-level detail).

### 2.4 Security test lab

Each test run is isolated from production:

```text
Test controller
  -> creates ephemeral namespace/container/VM
  -> supplies fake OAuth client or short-lived sandbox identity
  -> mounts synthetic fixtures, not production secrets/data
  -> restricts DNS/egress to approved mock/test endpoints
  -> executes test suite under CPU/memory/time quotas
  -> uploads signed results to evidence store
  -> destroys environment
```

Hard-fail certification when any critical control is missing (no soft average). See [`SECURITY-TEST-LAB.md`](SECURITY-TEST-LAB.md).

### 2.5 Interactive filter state

Keep filters in the URL so teams can share a specific view.

```text
/registry?category=database,observability
  &operation=read
  &trustTier=3,4
  &environment=production
  &health=healthy,degraded
  &certExpiresBefore=2026-10-16
  &sort=-activity_24h
```

TypeScript filter model: [`../types/connector-filters.ts`](../types/connector-filters.ts)

---

## 3. Reference architecture

```text
                           ┌──────────────────────────┐
                           │ Cursor / CLI / Agents    │
                           │ rules + hooks + mcp.json │
                           └─────────────┬────────────┘
                                         │ authenticated MCP
                 ┌───────────────────────▼────────────────────────┐
                 │ MCP Gateway (authoritative enforcement)        │
                 │ authn | ABAC/RBAC | schema | budgets | redact  │
                 │ approval verification | egress | audit | trace  │
                 └───────┬──────────────────────────────┬─────────┘
                         │                              │
          ┌──────────────▼──────────────┐  ┌────────────▼─────────────┐
          │ Registry API / Control Plane │  │ Policy + Approval Service │
          │ catalog | versions | tests   │  │ OPA/Cedar | signed grants │
          │ cert | activation | quarantine│ └──────────────────────────┘
          └───────────┬─────────┬────────┘
                      │         │
            ┌─────────▼──┐  ┌──▼──────────────────────────┐
            │ PostgreSQL │  │ Object / evidence storage    │
            │ RLS + audit│  │ SBOM, reports, signed output │
            └────────────┘  └─────────────────────────────┘
                      │
        ┌─────────────▼───────────────────────────────────────────────┐
        │ certified connectors: GitHub | Git | filesystem | CI | docs  │
        │ Postgres RO | observability | browser | policies | evidence  │
        └─────────────────────────────────────────────────────────────┘
```

### 3.1 Runtime flow

1. Cursor asks the gateway to enumerate or call an MCP tool.
2. Gateway verifies user/workload identity, organization, project, tenant, and target environment.
3. Gateway resolves the requested connector **version** and checks lifecycle, certification, quarantine, project activation, trust tier, and environment eligibility.
4. Gateway validates the tool’s JSON Schema; canonicalizes arguments; strips prohibited fields; generates `args_hash` and a correlation ID.
5. Policy engine evaluates identity, roles, tenant, environment, connector, tool, data class, argument-derived resource, budget, and time.
6. For sensitive operations, gateway creates/requires an approval request tied to the exact call.
7. Gateway invokes the connector with a narrow, short-lived delegated credential and enforced egress policy.
8. Gateway validates response size/schema, redacts secrets/regulated data, treats returned prose as untrusted data, and records evidence.
9. Gateway returns a structured result to Cursor; post-tool hooks can record local validation but cannot override gateway denial.

### 3.2 MCP entry point

Expose a single gateway endpoint to clients whenever feasible. Do not put bearer tokens, production database URLs, private keys, or broad cloud credentials into `.cursor/mcp.json`.

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

---

## 4. Postgres schema

Target DDL lives in [`../schema/005_full_product_model.sql`](../schema/005_full_product_model.sql). It includes:

- Enums: lifecycle, certification, operation (`read|write|delete|external_communication|exec`), risk, transport, test/approval/invocation status, environments (`local|development|staging|production`)
- Tenant/project/identity: organizations, teams, principals, projects, project_memberships
- Registry: connectors, connector_versions, connector_tools, environment eligibility, activations
- Assurance: security_test_suites, security_test_runs, security_test_results, certification_decisions, policy_versions, policy_decisions
- Runtime: approval_requests, approval_decisions, tool_invocations, connector_health_checks, connector_quarantines
- RLS via `set_config('app.org_id', verified_org_id, true)` — never browser-controlled
- Partition guidance for high-volume `tool_invocations`

Prior migrations `001`–`004` remain the current scaffold; `005` is the greenfield / migration target for the full product model.

---

## 5. API endpoints

All endpoints are versioned under `/api/v1`. Authenticate via OIDC session/JWT; derive organization and principal from validated claims. Do not accept an arbitrary `org_id` as authoritative request input.

### 5.1 Registry catalog

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/connectors` | Filtered, cursor-paginated registry catalog |
| POST | `/connectors` | Create connector metadata draft |
| GET | `/connectors/{slug}` | Connector summary and current versions |
| PATCH | `/connectors/{slug}` | Update connector metadata/owners |
| POST | `/connectors/{slug}/versions` | Publish a version manifest to validation queue |
| GET | `/connectors/{slug}/versions/{version}` | Full version detail |
| PATCH | `/connectors/{slug}/versions/{version}` | Amend non-immutable metadata or lifecycle state |
| GET | `/connectors/{slug}/versions/{version}/tools` | Tool inventory |
| POST | `/connectors/{slug}/versions/{version}/quarantine` | Emergency quarantine |
| POST | `/connectors/{slug}/versions/{version}/unquarantine` | Lift quarantine with recorded reason |

### 5.2 Test lab and certification

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/connector-versions/{id}/test-runs` | Start isolated security test run |
| GET | `/test-runs/{id}` | Test status, findings, evidence |
| POST | `/test-runs/{id}/cancel` | Cancel test run |
| GET | `/connector-versions/{id}/test-runs` | Test history |
| POST | `/connector-versions/{id}/certification-decisions` | Review/certify/fail version |
| GET | `/certification-queue` | Reviewer work queue |
| POST | `/policy/simulate` | Evaluate proposed tool invocation without executing it |

### 5.3 Activation lifecycle

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/activations` | Request project/environment activation |
| GET | `/activations` | Filter activation records |
| POST | `/activations/{id}/approve` | Approve eligible activation |
| POST | `/activations/{id}/disable` | Disable an activation |
| POST | `/activations/{id}/renew` | Renew expiring activation |

### 5.4 Approval API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/approvals` | Create approval request from normalized planned action |
| GET | `/approvals` | Pending/history queue |
| GET | `/approvals/{id}` | Review exact bound action |
| POST | `/approvals/{id}/approve` / `deny` | Add decision |
| POST | `/approvals/{id}/consume` | Gateway-only atomic consume |

Signed grants must bind actor, org/project/tenant, connector version ID, tool ID, `args_hash`, environment, idempotency key, policy version, nbf/exp, required approvers. See [`APPROVAL-TOKENS.md`](APPROVAL-TOKENS.md).

### 5.5 Operations and audit API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/metrics/connectors` | Aggregated health/activity metrics |
| GET | `/invocations` | Redacted audit explorer |
| GET | `/policy-decisions` | Policy audit stream |
| GET | `/health/connectors` | Current health summaries |
| GET/POST | `/quarantines` | Quarantine records / emergency block |

### 5.6 Gateway API (service-to-service)

Protect with mTLS/workload identity. Never accept a raw connector endpoint from the client.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/gateway/v1/tools/authorize` | Resolve/authorize a prospective tool call |
| POST | `/gateway/v1/tools/invoke` | Validate, enforce, proxy, redact, audit |
| POST | `/gateway/v1/tools/complete` | Record final outcome when async |
| POST | `/gateway/v1/redact` | Structured secret/PII redaction |
| POST | `/gateway/v1/egress/check` | URL/domain egress decision |

Current FastAPI scaffold maps many of these under `/api/v1/...` and `/gateway/v1/...` aliases.

---

## 6. Cursor hooks and package

Suggested layout:

```text
.cursor/
├── hooks.json
├── mcp.json / mcp.gateway.example.json / mcp.pilot.json
├── rules/
│   ├── 00-agent-security.mdc
│   ├── 10-mcp-tool-policy.mdc
│   ├── 20-database-safety.mdc
│   └── 30-release-safety.mdc
├── skills/…
└── hooks/
    ├── preflight-mcp.mjs (+ .ts examples)
    ├── postflight-mcp.mjs
    ├── preflight-command.mjs
    ├── secret-scan-output.mjs
    └── examples/lib/canonicalize.ts …
```

Hooks are **preflight only**. The gateway repeats all checks and fails closed for high-risk calls. Hook event names vary by Cursor release — preserve behavior, update adapters.

### Cursor Rules baseline

Always-applied rules must require: treat MCP/web/issue/log content as untrusted data; read-only discovery before mutation; plans + rollback for writes; no direct prod shell/DB/TF/kubectl; route through org gateway; never reveal secrets/PHI; explicit tenant/environment scope; never bypass hooks/policy/approvals.

---

## 7. Approval-gate design

| Action class | Default | Required controls |
|---|---|---|
| Read internal non-regulated | Auto-allow if policy passes | AuthN, scope, schema, audit |
| Read confidential/regulated | Permit only when necessary | ABAC, minimization, redaction, limits |
| Write development/staging | Approval depending on risk | Plan, idempotency, approval if shared |
| Write production | Approval required | Exact args binding, short grant, rollback |
| Delete / access / secrets / external msg | Dual approval by default | Binding, step-up, time limit, evidence |
| Deploy / schema change | Controlled GitOps | Reviewed PR, CI, policy, canary/rollback |

Atomic consumption:

```sql
update approval_requests
set status = 'consumed', consumed_at = now()
where id = :approval_id
  and status = 'approved'
  and expires_at > now()
  and args_hash = :args_hash
  and idempotency_key = :idempotency_key
returning id;
```

If no row returns, deny execution.

---

## 8. Security and operations requirements

### Onboarding gate

Immutable digest, signed provenance/SBOM, named owner + runbook, tool schemas, risk/approval labels, least-privilege identity, tenant authz in gateway **and** connector, egress/SSRF defenses, injection validation, redaction + size limits, reliability controls, prompt-injection tests, OTEL + tamper-evident audit, quarantine drill.

### SLOs

| Metric | Target |
|---|---:|
| Registry catalog availability | 99.9% monthly |
| Gateway authorization availability | 99.95% monthly (prod paths) |
| Certification evidence retention | ≥ 1 year (or control requirement) |
| Quarantine propagation | < 60 seconds |
| High-risk invocation audit completeness | 100% |
| Unapproved production write success | 0 |
| Critical security test failure bypass | 0 |
| Approval-grant lifetime | 5–15 minutes default |

### Anti-patterns

- Auto-install from a public registry entry
- Unreviewed `npx -y` from arbitrary packages
- Shared broad credentials across users/tenants
- Generic unrestricted HTTP fetch
- Logging raw prod args/responses into developer dashboards
- Treating a Cursor click as proof the backend call is unchanged
- Read-only connectors with write escape hatches
- Letting the LLM choose raw connector URLs, cloud accounts, tenants, or prod credentials

---

## 9. Implementation milestones

| Milestone | Outcome |
|---|---|
| **1 — Registry foundation** | Postgres + RLS + OIDC; catalog UI; filters; saved views; version detail |
| **2 — Assurance plane** | Ephemeral sandbox, suites, evidence, certification, SBOM/CVE, quarantine |
| **3 — Gateway enforcement** | Single entry, activation resolution, policy, schema, egress, redaction, OTEL; core RO connectors |
| **4 — Cursor package** | Gateway-only mcp.json; hooks; rules/skills; CI proving hooks |
| **5 — Controlled mutations** | Approval API, bound grants, dual approval, atomic consume; first non-prod GitHub PR create |

Current repo status: scaffold covers much of M1–M5 in prototype form (Weeks 1–8 + Phase A/B). Use this document as the product contract for hardening toward production.

---

## 10. Initial connector portfolio

1. GitHub Read-only  
2. Workspace Filesystem Sandbox  
3. Git Repository Read-only  
4. CI/CD Observer  
5. Documentation Fetch/Search with egress controls  
6. PostgreSQL Read-only via replica and query bounds  
7. Observability Reader  
8. Browser Test Runner (test/staging targets)  
9. Policy + Approval Gateway  
10. Append-only Audit/Evidence Store  

Plus constrained `github-write` (non-prod, grant-bound, dry-run default) as the first mutation after Milestone 5 controls are green.

For all other connectors in the 100+ catalog, onboard one category at a time—sandboxed/read-only → reviewed → certified—rather than granting broad access based on popularity.
