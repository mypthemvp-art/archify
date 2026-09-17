# Cursor + Open-Source OpenAI/MCP Automation Catalog

## Purpose

This catalog proposes **100 production-oriented automations** for Cursor using MCP connectors, Cursor plugins, rules, skills, hooks, and scheduled/event-driven automations. It is designed for secure AI-agent SaaS development: FastAPI, TypeScript, PostgreSQL, Redis, Docker, Kubernetes, GitHub Actions, Terraform, policy enforcement, and audited human approval.

**Important design principle:** Treat every connector as an untrusted capability. Separate read-only discovery from mutations; minimize OAuth scopes; make writes explicit, reviewable, idempotent, and logged.

Generated version `2.0.0` · 100 automations

## Automation contract

1. **Trigger** — slash command, prompt, PR/issue event, deployment signal, schedule, or webhook
2. **Inputs** — repository, environment, tenant, time range, and policy context
3. **Plan** — structured dry-run output with impacted objects, risk, and expected changes
4. **Guardrails** — allowlists, schema validation, least privilege, secret redaction, rate limits, timeout, concurrency key, and cost/token budget
5. **Approval** — required for production writes, external communications, deletes, migrations, or spending
6. **Evidence** — immutable audit event containing actor, tool, arguments hash, decision, result hash, and correlation ID
7. **Verification** — tests, policy check, health check, rollback guidance, and a concise artifact

## The 12 plugins to build first

| Priority | Plugin | Automations | Why |
|---:|---|---|---|
| 1 | Secure PR Guardian (`secure-pr-guardian`) | A003, A004, A007, A011, A021, A026, A031, A068 | Immediate leverage for every repository |
| 2 | MCP Security Gateway (`mcp-security-gateway`) | A091, A092, A093, A094, A095, A096, A097, A098, A099 | Build before enabling broad third-party connectors |
| 3 | Production Triage Copilot (`production-triage-copilot`) | A024, A040, A041, A042, A043, A044, A045, A046, A074 | Read-only by default for incidents and CI failures |
| 4 | Database Change Guardian (`database-change-guardian`) | A010, A046, A047, A048, A049 | Require explicit approval for all schema writes |
| 5 | GitOps Release Controller (`gitops-release-controller`) | A036, A037, A038, A039, A070, A075, A076, A077, A078, A079, A100 | Separate plan from execution for releases |
| 6 | Compliance Evidence Engine (`compliance-evidence-engine`) | A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090 | Map control -> evidence source -> freshness -> owner |
| 7 | FeatureOps Plugin (`featureops`) | A053, A054 | Approval-gate rollout percentage changes |
| 8 | Accessibility QA Plugin (`accessibility-qa`) | A055, A056, A057 | Store a11y/visual/e2e artifacts as CI evidence |
| 9 | Repository Intelligence Plugin (`repository-intelligence`) | A001, A002, A022, A029, A030, A058, A060 | Architecture, debt, docs, and onboarding intelligence |
| 10 | Cloud Cost Governor (`cloud-cost-governor`) | A045, A069, A071, A072, A073 | Recommendations only until measured savings are proven |
| 11 | Privacy Engineering Plugin (`privacy-engineering`) | A005, A049, A051, A082, A084, A095 | Data-flow, retention, HIPAA, and redaction workflows |
| 12 | Open-Source Maintenance Plugin (`open-source-maintenance`) | A013, A061, A062, A063, A064, A065, A066, A067, A088 | Issue/PR hygiene and dependency triage for OSS maintainers |

## 100 automation blueprints

| # | ID | Automation | Trigger | Connector / plugin capability | Output and guardrail | Mutation | Primary plugin |
|---:|---|---|---|---|---|---|---|
| 1 | A001 | Repository architecture map | On demand or weekly | filesystem, git, GitHub | Mermaid/Archify map + ownership; read-only | `none` | `repository-intelligence` |
| 2 | A002 | Dependency inventory | On commit | filesystem, package registries | SBOM diff; no writes | `none` | `repository-intelligence` |
| 3 | A003 | License compliance gate | PR opened | dependency scanner, policy MCP | Pass/fail report; block restricted licenses | `none` | `secure-pr-guardian` |
| 4 | A004 | Secret exposure scan | PR opened | git, secret scanner | Findings + revoke checklist; never echo secrets | `none` | `secure-pr-guardian` |
| 5 | A005 | PII data-flow mapper | Weekly | code search, docs, database schema read | DFD and risk register; read-only | `none` | `privacy-engineering` |
| 6 | A006 | Threat-model generator | Feature branch | filesystem, memory, policy | STRIDE document; human review required | `plan` | `unassigned` |
| 7 | A007 | Secure API endpoint review | PR opened | GitHub, filesystem, policy | Auth/input/rate-limit checklist | `none` | `secure-pr-guardian` |
| 8 | A008 | Authentication regression audit | PR opened | test runner, code search | Test plan and failures; no deployment | `none` | `unassigned` |
| 9 | A009 | RBAC policy diff reviewer | Policy change | policy engine, git | Permission delta; approval for privilege expansion | `plan` | `unassigned` |
| 10 | A010 | Tenant-isolation test builder | Schema or API change | Postgres read, test runner | Generated tests; sanitize tenant IDs | `plan` | `database-change-guardian` |
| 11 | A011 | OWASP change review | PR opened | GitHub, code scan | Ranked remediation plan | `plan` | `secure-pr-guardian` |
| 12 | A012 | CSP/header verifier | CI failed or PR | browser/test, config reader | Header evidence; no production mutation | `none` | `unassigned` |
| 13 | A013 | Dependency vulnerability triage | Daily | GitHub advisories, SBOM | Prioritized issue drafts; approval to create issues | `plan` | `open-source-maintenance` |
| 14 | A014 | Container hardening audit | Dockerfile changed | filesystem, image scanner | Base-image and privilege findings | `none` | `unassigned` |
| 15 | A015 | Kubernetes manifest review | Manifest changed | filesystem, policy engine | Admission-style violations; deny dangerous defaults | `none` | `unassigned` |
| 16 | A016 | Terraform plan reviewer | Plan artifact ready | Terraform plan reader, policy | Resource blast-radius summary; no apply | `none` | `unassigned` |
| 17 | A017 | IAM least-privilege analyzer | Weekly | cloud read API, policy | Unused/excess grants; approval for revoke | `plan` | `unassigned` |
| 18 | A018 | Key-rotation tracker | Daily | vault read metadata, ticketing | Rotation calendar; no secret values | `none` | `unassigned` |
| 19 | A019 | Audit-log completeness test | CI | application tests, database read | Missing event coverage report | `none` | `unassigned` |
| 20 | A020 | Cryptographic signing verifier | Release candidate | git, CI, key metadata | Signature/attestation status | `none` | `unassigned` |
| 21 | A021 | PR summary and risk score | PR opened/updated | GitHub, git, code analysis | Summary, risk, tests, owners; read-only | `none` | `secure-pr-guardian` |
| 22 | A022 | Change-impact explorer | On demand | git, code graph, GitHub | Callers, services, migrations, dashboards | `none` | `repository-intelligence` |
| 23 | A023 | Reviewer recommender | PR opened | CODEOWNERS, git blame, GitHub | Suggested reviewers; no automatic assignment by default | `none` | `unassigned` |
| 24 | A024 | Failing-test root-cause assistant | CI failure | CI logs, git diff, test artifacts | Ranked hypotheses with evidence | `none` | `production-triage-copilot` |
| 25 | A025 | Flaky-test detector | Nightly | CI history, test artifacts | Flake score and quarantine proposal | `plan` | `unassigned` |
| 26 | A026 | Test-gap generator | PR opened | coverage, filesystem | Missing unit/integration/e2e test suggestions | `plan` | `secure-pr-guardian` |
| 27 | A027 | Snapshot-change explainer | PR opened | git, test artifacts | Semantic diff; require review of snapshots | `none` | `unassigned` |
| 28 | A028 | Build-time regression investigator | CI trend | CI metrics, git history | Suspect changes and optimization plan | `plan` | `unassigned` |
| 29 | A029 | Code-quality debt radar | Weekly | static analysis, GitHub | Ranked refactor backlog | `plan` | `repository-intelligence` |
| 30 | A030 | Dead-code candidate report | Weekly | code graph, coverage | Candidate list; never auto-delete | `plan` | `repository-intelligence` |
| 31 | A031 | API breaking-change detector | PR opened | OpenAPI, git | Versioning/migration guidance | `none` | `secure-pr-guardian` |
| 32 | A032 | OpenAPI contract test generator | API spec changed | OpenAPI, test runner | Tests and negative-case coverage | `plan` | `unassigned` |
| 33 | A033 | SDK regeneration assistant | API spec merged | OpenAPI generator, GitHub | PR draft; approval to create/update branch | `plan` | `unassigned` |
| 34 | A034 | Changelog composer | Release candidate | git, PR labels, issues | Human-readable release notes | `plan` | `unassigned` |
| 35 | A035 | Semantic version adviser | Release candidate | git, API diff | Proposed version with rationale | `plan` | `unassigned` |
| 36 | A036 | Release checklist executor | Tag proposed | GitHub, CI, policy, docs | Gated checklist; no tag/publish without approval | `plan` | `gitops-release-controller` |
| 37 | A037 | Canary-analysis report | Deployment event | metrics, logs, traces | Compare baseline/canary; rollback recommendation | `plan` | `gitops-release-controller` |
| 38 | A038 | Rollback-plan generator | Deploy request | GitOps, CI, cloud read | Exact rollback steps; approval before execution | `plan` | `gitops-release-controller` |
| 39 | A039 | Post-release verifier | Deployment completed | health checks, metrics, logs | SLO and error-budget validation | `none` | `gitops-release-controller` |
| 40 | A040 | Incident timeline constructor | Incident webhook | Slack/alerts/logs/traces | Timestamped chronology; redact PII | `none` | `production-triage-copilot` |
| 41 | A041 | Error-cluster triage | New error spike | Sentry/observability, GitHub | Grouped fingerprints and likely owner | `none` | `production-triage-copilot` |
| 42 | A042 | Log-to-code correlation | Alert fired | logs, traces, git | Relevant commit/PR candidates | `none` | `production-triage-copilot` |
| 43 | A043 | Distributed-trace explainer | On demand | tracing backend | Critical path and latency bottleneck | `none` | `production-triage-copilot` |
| 44 | A044 | SLO burn-rate responder | Burn alert | metrics, runbooks, paging | Evidence-based mitigation plan; no auto-page externally | `plan` | `production-triage-copilot` |
| 45 | A045 | Capacity forecast | Weekly | metrics, cost data | Utilization forecast and scale recommendations | `plan` | `production-triage-copilot` |
| 46 | A046 | Database slow-query review | Daily | Postgres read-only, telemetry | Query plan findings; approval for indexes | `plan` | `production-triage-copilot` |
| 47 | A047 | Migration safety analyzer | Migration PR | Postgres schema, migration files | Lock/rollback/backfill assessment | `plan` | `database-change-guardian` |
| 48 | A048 | Backup-restore drill assistant | Monthly | backup metadata, runbook, CI sandbox | Drill report; isolate test restore environment | `plan` | `database-change-guardian` |
| 49 | A049 | Data-retention enforcement audit | Weekly | schemas, object storage metadata, policy | Expired-data exceptions report | `none` | `database-change-guardian` |
| 50 | A050 | Data-quality anomaly detector | Scheduled | warehouse/read replica, metrics | Anomaly report; no destructive repair | `none` | `unassigned` |
| 51 | A051 | Product telemetry schema reviewer | Event schema change | analytics schema, privacy policy | PII/minimization review | `none` | `privacy-engineering` |
| 52 | A052 | Funnel regression investigator | Metric alert | analytics read, deployments | Correlated release and segment analysis | `none` | `unassigned` |
| 53 | A053 | Feature-flag hygiene bot | Weekly | Unleash/flag service, GitHub | Stale flag list and removal PR draft | `plan` | `featureops` |
| 54 | A054 | Experiment analysis brief | Experiment completed | analytics read, flag platform | Guardrail metrics + decision template | `plan` | `featureops` |
| 55 | A055 | UX accessibility test runner | PR opened | Playwright, axe, browser | WCAG-oriented findings with screenshots/artifacts | `none` | `accessibility-qa` |
| 56 | A056 | Visual-regression review | UI PR | Playwright, visual baseline | Diff review; approval to update baseline | `plan` | `accessibility-qa` |
| 57 | A057 | Browser e2e journey executor | Nightly | Playwright/browser MCP | Journey result and failure artifacts | `none` | `accessibility-qa` |
| 58 | A058 | Documentation drift detector | Weekly | code, docs, OpenAPI | Drift report and suggested patches | `plan` | `repository-intelligence` |
| 59 | A059 | Runbook quality reviewer | Incident closed | docs, incident artifacts | Missing diagnosis/rollback/escalation steps | `plan` | `unassigned` |
| 60 | A060 | Developer onboarding guide generator | Repo bootstrap | filesystem, GitHub, docs | Setup guide validated against CI | `plan` | `repository-intelligence` |
| 61 | A061 | Issue intake classifier | New GitHub issue | GitHub, policy, memory | Labels, severity, reproduction prompts; no auto-close | `plan` | `open-source-maintenance` |
| 62 | A062 | Issue-to-implementation planner | Approved issue | GitHub, code graph | Scoped plan, files, tests, risks | `plan` | `open-source-maintenance` |
| 63 | A063 | PR-to-issue linker | PR opened | GitHub | Missing references and release impact | `plan` | `open-source-maintenance` |
| 64 | A064 | Stale-PR caretaker | Daily | GitHub | Status summary; approval to comment/close | `plan` | `open-source-maintenance` |
| 65 | A065 | Merge-conflict resolver draft | Conflict detected | git, GitHub, CI | Candidate resolution branch; never force-push | `plan` | `open-source-maintenance` |
| 66 | A066 | Commit-message policy bot | Commit/PR | git, policy | Conventional-commit validation | `none` | `open-source-maintenance` |
| 67 | A067 | Repository housekeeping | Weekly | GitHub, git | Branch/artifact cleanup proposal; approval for deletion | `plan` | `open-source-maintenance` |
| 68 | A068 | CI workflow hardening review | Workflow change | GitHub Actions, policy | Pinning, permissions, provenance findings | `none` | `secure-pr-guardian` |
| 69 | A069 | CI cost optimizer | Weekly | CI metrics/billing, workflows | Cache/parallelism/right-sizing plan | `plan` | `cloud-cost-governor` |
| 70 | A070 | Supply-chain provenance verifier | Release candidate | CI attestations, registry | SBOM, signatures, provenance status | `none` | `gitops-release-controller` |
| 71 | A071 | Cloud cost anomaly triage | Daily | cloud billing read, metrics | Cost drivers and remediation candidates | `plan` | `cloud-cost-governor` |
| 72 | A072 | Resource-rightsizing planner | Weekly | cloud metrics, IaC | CPU/memory recommendations; no automatic resize | `plan` | `cloud-cost-governor` |
| 73 | A073 | Orphan-resource detector | Weekly | cloud inventory, IaC state | Candidate cleanup plan; human approval needed | `plan` | `cloud-cost-governor` |
| 74 | A074 | Kubernetes event triage | Cluster alert | Kubernetes read, logs, metrics | Pod/node/event diagnosis; read-only | `none` | `production-triage-copilot` |
| 75 | A075 | Helm upgrade readiness | Release candidate | Helm diff, cluster read, policy | Compatibility/risk report | `none` | `gitops-release-controller` |
| 76 | A076 | GitOps drift detector | Scheduled | cluster read, Git repo | Drift evidence and reconciliation PR suggestion | `plan` | `gitops-release-controller` |
| 77 | A077 | Certificate-expiry responder | Daily | cert metadata, ticketing | Renewal timeline; no key material exposure | `plan` | `gitops-release-controller` |
| 78 | A078 | DNS/edge configuration audit | Weekly | cloud edge read, policy | TLS/cache/WAF/security finding list | `none` | `gitops-release-controller` |
| 79 | A079 | Disaster-recovery readiness score | Monthly | backups, IaC, runbooks, CI | RTO/RPO evidence scorecard | `none` | `gitops-release-controller` |
| 80 | A080 | Compliance evidence collector | Scheduled | GitHub, CI, cloud, policy | Control-to-evidence package; immutable indexing | `none` | `compliance-evidence-engine` |
| 81 | A081 | SOC 2 control monitor | Weekly | policy, CI, identity/cloud read | Exception dashboard and owner routing | `none` | `compliance-evidence-engine` |
| 82 | A082 | HIPAA safeguards checker | Scheduled | data flows, access logs, policy | Safeguard gaps; no PHI extraction | `none` | `compliance-evidence-engine` |
| 83 | A083 | NIST control mapping assistant | Release/assessment | policy library, system inventory | Mapped controls and evidence gaps | `none` | `compliance-evidence-engine` |
| 84 | A084 | Privacy request workflow coordinator | Ticket opened | ticketing, data inventory, approval | Data-location plan; approval for disclosure/deletion | `plan` | `compliance-evidence-engine` |
| 85 | A085 | Access-review campaign assistant | Quarterly | IAM read, HR directory read | Reviewer packets; approval before revocations | `plan` | `compliance-evidence-engine` |
| 86 | A086 | Vendor-security questionnaire drafter | Request received | policy docs, evidence vault | Draft answers with evidence citations | `plan` | `compliance-evidence-engine` |
| 87 | A087 | DPA/security addendum reviewer | Contract received | document fetch, policy | Clause deviations and escalation points | `none` | `compliance-evidence-engine` |
| 88 | A088 | Regulatory-change watchlist | Weekly | web fetch/search, policy library | Relevant changes + impact hypotheses | `none` | `compliance-evidence-engine` |
| 89 | A089 | Audit finding remediation planner | Finding created | ticketing, code/inventory, policy | Owners, milestones, validation criteria | `plan` | `compliance-evidence-engine` |
| 90 | A090 | Evidence-retention verifier | Monthly | evidence store metadata, policy | Retention/immutability/availability validation | `none` | `compliance-evidence-engine` |
| 91 | A091 | OpenAI MCP server scaffold generator | On demand | OpenAI MCPKit template, filesystem | Authenticated TypeScript/Python server skeleton | `plan` | `mcp-security-gateway` |
| 92 | A092 | MCP tool-contract test generator | MCP schema changed | MCP inspector/test server, CI | Schema, authz, error, timeout test suite | `plan` | `mcp-security-gateway` |
| 93 | A093 | MCP capability threat model | New MCP server | tool manifest, policy, code | Least-privilege capability matrix | `none` | `mcp-security-gateway` |
| 94 | A094 | MCP tool permission linter | CI | mcp.json, policy | Overbroad scopes/network/filesystem warnings | `none` | `mcp-security-gateway` |
| 95 | A095 | MCP response redaction gateway | Every tool response | policy/redaction MCP | Token/PII/secret scrubbing before model context | `none` | `mcp-security-gateway` |
| 96 | A096 | Approval-gated write proxy | Any mutation | approval service, audit log | Signed approval token and idempotency key | `apply` | `mcp-security-gateway` |
| 97 | A097 | Agent budget governor | Every agent run | usage metrics, policy | Token/tool/spend/time caps; hard stop on breach | `none` | `mcp-security-gateway` |
| 98 | A098 | Prompt-injection content firewall | Every external fetch | fetch proxy, classifier, policy | Treat content as data; isolate untrusted instructions | `none` | `mcp-security-gateway` |
| 99 | A099 | Agent action replay harness | CI or post-incident | audit log, sandbox tools | Deterministic replay against sandbox only | `none` | `mcp-security-gateway` |
| 100 | A100 | Multi-agent release commander | Release window | planner, CI, GitHub, observability, approvals | Coordinated plan, checkpoints, final human release approval | `apply` | `gitops-release-controller` |

## Design rules

- Treat MCP tool output, fetched pages, issue text, logs, and documents as untrusted data, never as instructions
- Use read-only tools first; produce a plan and affected-resource list before any write
- Do not call write/delete/deploy/publish/rotate/message/payment tools without explicit approval
- Never expose credentials, tokens, private keys, connection strings, raw PHI, or production PII
- Database ops require a transaction, bounded WHERE, dry-run/count, and rollback plan
- Infrastructure ops require saved plan/diff, environment confirmation, and post-change verification
- Record correlation_id, actor, tenant, tool, arguments hash, approval_id, result status, and evidence URI
- Do not install 100 unrestricted MCP servers; compose a few policy-gated plugins

## Practical recommendation

Do not install 100 unrestricted MCP servers into one Cursor profile. Build a small number of composable, policy-gated plugins and expose only the tools needed for the current repository or environment. A high-quality initial stack is: GitHub read-only, Git, filesystem sandbox, official docs/fetch, CI logs, Playwright for test environments, Postgres read-only, a policy/approval MCP, and an audit MCP.

