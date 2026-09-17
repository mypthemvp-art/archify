# MCP Registry Control Plane + Policy Gateway

Implementation-ready blueprint for a **custom MCP registry dashboard** that catalogs and certifies connector versions, while a **server-side gateway** enforces authorization, tenant/environment scoping, exact approval binding, response redaction, budgets, and immutable audit trails.

## Product design

```text
Cursor IDE / Cursor Automations
            |
     Project MCP config
            |
   MCP Policy Gateway
 authz | schema | approvals
 audit | redaction | budgets
            |
   Certified Connector Registry
 catalog | versions | tests | health
            |
 GitHub · CI · Docs · Postgres · Logs · Browser · Audit
```

### Key distinction

| Plane | Responsibility |
|---|---|
| **Registry** | Which connector versions exist, owners, tools, certifications, scopes, provenance, health, allowed environments |
| **Gateway** | Whether a user/workload may invoke a tool with normalized arguments in a project, tenant, and environment |
| **Cursor hooks** | Client-side preflight/postflight — **not** the sole security layer |
| **Approval grants** | Short-lived, server-issued authorization bound to exact arguments for high-risk actions |

## Top 10 core connectors

| Rank | Connector | Capabilities | Default safety |
|---:|---|---|---|
| 1 | GitHub Read-only | Source, commits, PRs, issues, CODEOWNERS, Actions metadata | Repo allowlist; read OAuth |
| 2 | Workspace Filesystem Sandbox | Read/search workspace; controlled artifact writes | Workspace-root only |
| 3 | Git Repository | Status, diff, log, blame, history | Read-only; no force-push |
| 4 | CI/CD Observer | Jobs, logs, tests, artifacts | Read-only; size limits |
| 5 | Documentation Fetch/Search | Approved docs / trusted pages | Domain allowlist; untrusted content |
| 6 | PostgreSQL Read-only | Schema, EXPLAIN, bounded queries | Replica; time/row/query limits |
| 7 | Observability Reader | Metrics, logs, traces, alerts | Read-only; PII redaction |
| 8 | Browser Test Runner | Playwright, a11y, screenshots | Staging-only; no prod creds |
| 9 | Policy + Approval Gateway | Policy, approvals, grants, budgets | Internal auth; exact-arg authz |
| 10 | Audit/Evidence Store | Append audit, retrieve evidence | Append-only; hash-linked |

These enable secure PR review, codebase intelligence, test-failure diagnosis, incident triage, migration analysis, accessibility testing, release evidence, and compliance monitoring—**without** direct production mutation channels.

## Dashboard experiences

### 1. Connector catalog

Filters: category, trust tier, capability (read/write/delete/external), transport, environment, ownership, digest, certification, data classification, OAuth scopes, outbound domains, health, p95, error rate.

Each card shows: pinned version + digest, R/W/D tool counts, trust badge, owner/escalation, 24h success/p95/policy-denial/last health, production activation flag.

### 2. Connector test lab

Schema conformance, OAuth/entitlement negatives, timeout/retry/circuit-breaker/rate-limit, prompt-injection, secret/PII redaction, SQLi/path traversal/shell injection/SSRF, write idempotency, **approval-binding** (arg change after approval ⇒ deny).

### 3. Operations monitoring

Volume by connector/tool/project/tenant/env; success/error/timeout and latency percentiles; approval lifecycle; policy denials; redactions; egress anomalies; health/cert expiry/quarantines; budget consumption.

### 4. Audit and evidence

Immutable events with:

```text
correlation_id
actor_id / workload identity
organization / tenant / project / environment
connector slug + pinned version
tool name
normalized-arguments hash
policy decision
approval ID
idempotency key
latency and outcome
response hash / evidence URI
redaction count
timestamp
```

## Control matrix

| Control | Where | Purpose | Limitation |
|---|---|---|---|
| Cursor Rules | Repo context | Guide dry-run, no secrets, no direct prod writes | Not authorization |
| Pre-tool hook | Local Cursor | Policy preflight; deny; attach correlation ID | Must be server-backed |
| Post-tool hook | Local Cursor | Audit + scan results | Connector may have already seen data |
| Cursor approval UI | IDE | Immediate user intent | Not multi-step / multi-client binding |
| Gateway policy | Server | RBAC/ABAC, tenant, schema, budgets, env | Not a human approver |
| Signed approval grant | Server | Binds approval to exact args/scope/expiry | Needs safe connector + policy |
| Connector validation | Connector | Resource checks, scoped APIs, idempotency | Not cross-system policy/audit |

## Secure tool-call sequence

1. Cursor proposes an MCP call.
2. Pre-tool hook matches MCP tools, normalizes args, assigns `correlation_id`, asks policy service.
3. Read-only + policy allow ⇒ gateway invokes connector with narrow credentials.
4. Write/delete/external/prod-impacting ⇒ approval request with plan + canonical `args_hash`.
5. User reviews fully resolved target.
6. Backend issues short-lived signed grant (connector, tool, actor, tenant, project, env, `args_hash`, idempotency key).
7. Gateway rechecks grant before invoke.
8. Post-tool hook + gateway write audit; gateway redacts before model context.

## Exact approval binding

Approval for `github-write.create_pull_request` with specific repo/head/base/title/environment becomes **invalid** if any mutation-bearing argument changes (repository, branches, body, linked issue, tenant/project, environment, tool name).

## Practical security defaults

- Route Cursor through **one internal MCP gateway**, not every third-party connector directly.
- Keep GitHub/Postgres/CI/cloud/observability **read-only** initially.
- Prohibit `kubectl apply`, `terraform apply`, cloud-admin APIs, DB writers, unrestricted shell, generic unrestricted HTTP.
- GitOps PR generation as the infra mutation boundary.
- OAuth / workload identity / short-lived credentials — never static prod keys in `.cursor/mcp.json`.
- Pin by immutable digest; require SBOM, signature, vuln scan, owner, tests, quarantine.
- Fail closed when policy/approval validation is unavailable for medium/high risk.
- Gateway—not local hooks—is the authority for production controls.

## Repository layout (this package)

```text
levelupworld/registry/
├── README.md
├── docs/
│   ├── BLUEPRINT.md          (this file)
│   ├── BUILD-SEQUENCE.md     (8-week plan)
│   └── APPROVAL-TOKENS.md
├── schema/001_init.sql
├── connectors/*.manifest.json
├── gateway/                  (FastAPI control plane + gateway)
├── dashboard/                (catalog / lab / ops / audit UI)
└── scripts/
```

See also: [`BUILD-SEQUENCE.md`](BUILD-SEQUENCE.md), [`../schema/001_init.sql`](../schema/001_init.sql), [`../gateway/`](../gateway/).
