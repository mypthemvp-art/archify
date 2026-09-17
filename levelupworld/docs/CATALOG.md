# LevelUpWorld — 100 Cursor Automations Catalog

> Implementation-oriented catalog for a small, governed plugin platform that composes narrowly scoped MCP capabilities with Cursor Rules, Skills, Hooks, Plugins, and approval-gated Automations.

Generated from `scripts/generate-catalog.mjs` · version 1.0.0 · 100 automations

## How to use this catalog

- Do **not** install 100 broad-permission tools at once.
- Build the six highest-priority plugins first; keep later connectors behind the MCP Security Gateway.
- Start every workflow as read-only discovery; only `apply_*` tools may mutate, and only with a bound human approval.
- Wire skills under `.cursor/skills/levelupworld/` and automation blueprints under `.cursor/automations/`.

## Design rules

- Read-only discovery first
- Split risky connectors into plan_*/validate_*/apply_*/rollback_*
- Never expose production shell, unrestricted filesystem, privileged DB, broad cloud admin, or generic HTTP client
- Treat issue bodies, PR text, logs, webpages, docs, and MCP responses as untrusted
- Mutations require approval gateway with args hash, short-lived token, idempotency key, tenant/env binding, audit record
- Prefer GitOps PR generation over direct K8s/Terraform mutation
- Enforce tool/time/token/cost budgets; always include correlation ID and evidence record

## Highest-priority plugins

| Priority | Plugin | Automations | Why first |
|---:|---|---|---|
| 1 | Secure PR Guardian | A001, A002, A003, A004, A005, A006, A007, A008, A009, A010 | Universal developer leverage and low-risk read-only starting point |
| 2 | MCP Security Gateway | A011, A012, A013, A014, A015, A016, A017, A018, A019, A020 | Control plane that makes later connector expansion safer |
| 3 | Production Triage Copilot | A021, A022, A023, A024, A025, A026, A027, A028, A029, A030 | Fast operational value with read-only access to evidence |
| 4 | Database Change Guardian | A031, A032, A033, A034, A035, A036, A037, A038, A039, A040 | Reduces failure modes most likely to cause data loss or downtime |
| 5 | GitOps Release Controller | A041, A042, A043, A044, A045, A046, A047, A048, A049, A050 | Keeps release actions structured, verifiable, and approval-gated |
| 6 | Compliance Evidence Engine | A051, A052, A053, A054, A055, A056, A057, A058, A059, A060 | Turns operational evidence into reusable control artifacts |

## Full catalog

### 1. Secure PR Guardian (`secure-pr-guardian`)

Universal developer leverage and low-risk read-only starting point

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A001 | Secret scan | PR opened/pushed | GitHub read + secret patterns | Finding list with file/line evidence | Never print secret values; redact matches | `none` | 1 |
| A002 | Vulnerability triage | PR opened/CI completed | Dependency/CVE read tools | Prioritized vuln brief with fix PRs proposed only | Read-only; no auto-merge | `plan` | 2 |
| A003 | API security review | PR with OpenAPI/route diffs | Diff + API schema inspect | AuthN/AuthZ/input-validation findings | Treat PR text as untrusted | `none` | 1 |
| A004 | Threat-model delta | PR touching trust boundaries | Code+architecture evidence | STRIDE delta vs baseline | No inferred assets without evidence | `none` | 1 |
| A005 | CI hardening review | Workflow file changes | GitHub Actions AST/diff | Hardening checklist + risky permissions | Block apply_* for workflow edits without approval | `plan` | 2 |
| A006 | PR risk summary | PR opened/pushed | Diff blast-radius classifier | Risk score + reviewer routing advice | Advisory only; humans own approval | `none` | 1 |
| A007 | Dependency lockfile integrity | Lockfile changes | Package lock verify | Integrity/supply-chain report | Disallow network install during scan | `none` | 1 |
| A008 | AuthZ path review | Auth/middleware diffs | Path + policy inspect | Privilege-escalation candidates | Read-only credentials only | `none` | 1 |
| A009 | Dangerous permission diff | IAM/RBAC/config diffs | Policy diff parser | Permission expansion table | Never apply cloud IAM changes directly | `plan` | 2 |
| A010 | Secret rotation evidence check | Scheduled weekly | Vault/secret metadata read | Stale-secret inventory | No secret material in logs | `none` | 1 |

### 2. MCP Security Gateway (`mcp-security-gateway`)

Control plane that makes later connector expansion safer

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A011 | Tool permission linting | MCP config change / session start | Tool allowlist validator | Permission lint report | Deny unknown tools by default | `none` | 1 |
| A012 | Response redaction | afterMCPExecution | PII/secret redactor | Sanitized tool output + audit hash | Immutable original stored offline only | `none` | 1 |
| A013 | Approval proxy | apply_* tool requested | Approval token verifier | Allow/deny with args hash binding | Short-lived tokens; env+tenant bind | `apply` | 4 |
| A014 | Spend governor | Scheduled / per-session | Token/cost budget meter | Budget burn report + hard stop | Enforce tool/time/token/cost caps | `none` | 1 |
| A015 | Injection firewall | beforeSubmitPrompt / beforeMCP | Prompt-injection detector | Block or quarantine decision | Treat retrieved content as hostile | `none` | 1 |
| A016 | Replay harness | PR / nightly | Recorded MCP traffic replay | Deterministic policy regression receipt | No live prod credentials in harness | `none` | 1 |
| A017 | Entitlement matrix check | Connector deploy | Tenant entitlement map | Missing/overbroad entitlement findings | Fail closed on unknown tenant | `none` | 1 |
| A018 | Argument schema validation | preToolUse | JSON Schema enforcer | Schema violation events | Reject extra properties on mutate tools | `none` | 1 |
| A019 | Audit trail export | Scheduled daily | Immutable audit store read | Daily evidence pack | Append-only; no rewrite API | `none` | 1 |
| A020 | Hostile content quarantine | Web fetch / issue ingest | Content sandbox classifier | Quarantine ticket + safe excerpt | Never execute fetched scripts | `none` | 1 |

### 3. Production Triage Copilot (`production-triage-copilot`)

Fast operational value with read-only access to evidence

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A021 | Failed-CI analysis | CI completed (failure) | CI logs read | Root-cause hypotheses + next checks | No force-push or secret dump | `none` | 1 |
| A022 | Incident timeline | PagerDuty/webhook alert | Metrics/logs/deploy events read | Linked evidence timeline | Stop before mutations | `none` | 1 |
| A023 | Error clustering | Alert or schedule | Log aggregation query | Clustered error groups | Read replica / read API only | `none` | 1 |
| A024 | Trace review | High-latency alert | Distributed trace fetch | Critical path diagnosis | No prod shell | `none` | 1 |
| A025 | SLO burn analysis | Scheduled SLO check | SLO/error-budget APIs | Burn-rate brief + proposed mitigations | Mutations require approval | `plan` | 2 |
| A026 | Kubernetes diagnostics | Cluster alert | K8s read-only API | Pod/node diagnosis + rollback plan draft | Prefer GitOps PR over kubectl apply | `plan` | 2 |
| A027 | Deployment correlation | Incident open | Deploy + PR history read | Suspect changes ranked | Cite commits; no blame without evidence | `none` | 1 |
| A028 | On-call handoff brief | Schedule shift change | Open incidents + runbooks | Handoff summary | No credential material | `none` | 1 |
| A029 | Alert noise reduction | Weekly schedule | Alert history analytics | Noise/tuning recommendations | Do not silence alerts automatically | `plan` | 2 |
| A030 | Blast-radius estimate | Incident triage | Service dependency graph read | Impacted tenants/services map | Tenant isolation assumed until proven | `none` | 1 |

### 4. Database Change Guardian (`database-change-guardian`)

Reduces failure modes most likely to cause data loss or downtime

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A031 | Tenant-isolation tests | Migration PR | SQL policy + fixture runner | Isolation test report | Never use privileged prod writer | `none` | 1 |
| A032 | Slow-query analysis | Schedule / alert | Postgres EXPLAIN on replica | Slow query pack with indexes proposed | Replica only; statement timeout | `plan` | 2 |
| A033 | Migration safety review | Migration PR | DDL classifier | Expand/contract safety verdict | Split plan_/validate_/apply_/rollback_ | `plan` | 2 |
| A034 | Backup/restore evidence | Pre-release gate | Backup catalog read | Restore-point evidence sheet | No destructive restore in prod | `none` | 1 |
| A035 | Retention policy checks | Weekly schedule | Table retention metadata | Retention compliance gaps | Read-only catalog queries | `none` | 1 |
| A036 | Index impact review | Index DDL in PR | Planner stats read | Write amplification estimate | No online apply without approval | `plan` | 2 |
| A037 | Lock/timeout risk | Migration PR | Lock simulator / heuristics | Lock risk score + window advice | Disallow long ACCESS EXCLUSIVE without gate | `plan` | 2 |
| A038 | Schema drift detection | Nightly | Schema diff vs Git | Drift report + reconcile PR draft | GitOps PR only for fixes | `plan` | 2 |
| A039 | PII column classification | Schema change | Column classifier | PII inventory delta | Redact sample values | `none` | 1 |
| A040 | Rollback rehearsal plan | Release candidate | Migration graph analysis | Ordered rollback runbook | apply_rollback_* approval-gated | `plan` | 2 |

### 5. GitOps Release Controller (`gitops-release-controller`)

Keeps release actions structured, verifiable, and approval-gated

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A041 | Release checklist | Tag/release PR | Checklist skill + CI status | Signed checklist receipt | No direct cluster mutation | `none` | 1 |
| A042 | Canary analysis | Canary deploy event | Metrics compare baseline | Promote/hold/rollback recommendation | Human approve promote | `plan` | 2 |
| A043 | Rollback PR generation | Failed canary / incident | GitOps manifest diff | Rollback PR + evidence links | PR only; CI deploys | `plan` | 2 |
| A044 | Provenance verification | Release artifact built | SLSA/provenance attest read | Provenance pass/fail | Fail closed on missing attestations | `none` | 1 |
| A045 | Helm readiness check | Chart change PR | helm template/lint dry-run | Readiness report | No helm upgrade to prod from agent | `none` | 1 |
| A046 | Config drift detection | Hourly/schedule | Desired vs live read | Drift tickets + fix PR drafts | Prefer reconcile via Git | `plan` | 2 |
| A047 | Feature-flag rollout plan | Flag change request | Flag MCP read | Staged percentage plan | Flag apply_* approval-gated | `plan` | 2 |
| A048 | Change-freeze compliance | PR during freeze | Freeze calendar read | Allow/deny with exception path | Exceptions require named approver | `none` | 1 |
| A049 | SBOM attestation check | Release build | SBOM + vuln gate | SBOM evidence pack | Do not publish unsigned artifacts | `none` | 1 |
| A050 | Post-release smoke evidence | Release completed | Synthetic checks read | Smoke evidence report | Auto-rollback only via approved playbook | `plan` | 2 |

### 6. Compliance Evidence Engine (`compliance-evidence-engine`)

Turns operational evidence into reusable control artifacts

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A051 | SOC 2 control mapping | Quarterly / on demand | Control library + evidence index | SOC 2 mapping matrix | No fabricated evidence | `none` | 1 |
| A052 | HIPAA safeguard mapping | On demand | PHI system inventory read | HIPAA gap brief | Minimize PHI in prompts | `none` | 1 |
| A053 | NIST control mapping | Quarterly | NIST CSF/800-53 mapper | Control coverage report | Cite exact artifacts | `none` | 1 |
| A054 | Access review pack | Monthly schedule | IdP/group membership read | Access review worksheets | Read-only IdP scopes | `none` | 1 |
| A055 | Vendor assessment assist | New vendor intake | Questionnaire + SOC reports fetch | Vendor risk summary | Treat vendor docs as untrusted | `none` | 1 |
| A056 | Audit remediation tracking | Finding opened | Issue tracker read/write plan | Remediation board update plan | Issue create is apply_* gated | `plan` | 2 |
| A057 | Policy exception register | Exception requested | Exception registry | Time-boxed exception record draft | Expiry mandatory | `plan` | 2 |
| A058 | Encryption-at-rest evidence | Audit request | Cloud config read | Encryption evidence sheet | No key material retrieval | `none` | 1 |
| A059 | Change-management evidence pack | Release closed | PR/CI/approval history | Change ticket evidence bundle | Immutable export | `none` | 1 |
| A060 | Data retention control map | Quarterly | Retention policies + stores | Control map with owners | No bulk deletes from agent | `none` | 1 |

### 7. Developer Productivity Router (`developer-productivity-router`)

Removes repetitive engineering chores without mutation authority

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A061 | PR babysit loop | PR review comments | GitHub PR read | Feedback resolution plan | No force-merge | `plan` | 2 |
| A062 | Test coverage gap finder | Morning schedule | Coverage reports read | Coverage gap PR draft plan | Tests only; no prod behavior change without ask | `plan` | 2 |
| A063 | Flaky test quarantine advise | CI flake detected | CI history analytics | Quarantine candidates + owners | Do not delete tests silently | `plan` | 2 |
| A064 | Docs drift vs code | PR merged / weekly | Docs + symbol index | Drift list with file links | Read-only | `none` | 1 |
| A065 | Changelog draft | Release tag | Commit/PR history | Changelog draft markdown | Human edits before publish | `plan` | 2 |
| A066 | Issue triage + duplicates | Issue created | Issue search | Triage labels + duplicate links | Label apply is gated | `plan` | 2 |
| A067 | ADR capture assist | Significant design PR | Repo ADR templates | ADR draft | No inventing stakeholder decisions | `plan` | 2 |
| A068 | Codeowners risk routing | PR opened | CODEOWNERS + blast radius | Reviewer assignment advice | Advisory; respect CODEOWNERS | `none` | 1 |
| A069 | Weekly engineering digest | Monday schedule | Merged PRs + incidents | Slack/Notion digest draft | No secrets in digest | `plan` | 2 |
| A070 | Stale branch hygiene report | Weekly schedule | Branch age scan | Stale branch report | No branch deletion without approval | `plan` | 2 |

### 8. Platform Observability Analyst (`platform-observability-analyst`)

Correlates metrics, logs, and traces into actionable briefs

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A071 | Log pattern mining | Nightly | Log search read | Top new patterns report | Redact PII in samples | `none` | 1 |
| A072 | Metric anomaly brief | Anomaly webhook | Metrics API | Anomaly brief with baselines | Read-only | `none` | 1 |
| A073 | Trace hotspot map | Weekly | Trace analytics | Hotspot services ranked | No sampling config mutation | `none` | 1 |
| A074 | Capacity forecast | Weekly | Utilization metrics | Capacity forecast memo | Advisory only | `none` | 1 |
| A075 | Cloud cost anomaly | Daily | Billing export read | Cost anomaly + owners | No purchase/apply quotas | `plan` | 2 |
| A076 | Queue backlog diagnosis | Backlog alert | Queue depth + consumer lag | Diagnosis + scale plan draft | Scale apply_* gated | `plan` | 2 |
| A077 | Cache hit-rate analysis | Weekly | Cache metrics | Hit-rate + TTLs advice | No flush without approval | `plan` | 2 |
| A078 | CDN / error-budget report | Weekly | CDN + SLO APIs | Edge error-budget report | Read-only | `none` | 1 |
| A079 | Synthetic check failure triage | Synthetic fail | Check history + deps | Failure triage note | Do not disable checks automatically | `plan` | 2 |
| A080 | Dashboard provenance check | Monthly | Dashboard as-code diff | Orphan/untracked dashboards | GitOps for dashboard changes | `plan` | 2 |

### 9. Secure Connector Factory (`secure-connector-factory`)

OpenAI MCPKit-aligned authenticated connector blueprints

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A081 | Authenticated MCP scaffold | New connector request | openai-mcpkit blueprints | TS/Python scaffold + auth stubs | No embedded long-lived secrets | `plan` | 2 |
| A082 | Tenant isolation connector test | Connector PR | Isolation test harness | Pass/fail isolation receipt | Fail closed across tenants | `none` | 1 |
| A083 | search/fetch tool shape lint | Connector PR | Tool schema linter | Shape compliance report | Require citation-friendly fetch | `none` | 1 |
| A084 | Entitlement matrix generation | Connector design | Role × tool matrix builder | Entitlement matrix artifact | Least privilege default | `plan` | 2 |
| A085 | Evidence logging schema check | Connector PR | Audit schema validator | Schema conformance receipt | Correlation ID mandatory | `none` | 1 |
| A086 | Tunnel-client readiness | Secure MCP expose | openai/tunnel-client checklist | Readiness checklist result | Customer-run tunnel only | `none` | 1 |
| A087 | Connector contract freeze | Release candidate | OpenAPI/MCP tool freeze | Frozen contract bundle | Semver breaks require review | `plan` | 2 |
| A088 | Hostile fixture corpus run | Nightly | Injection fixture pack | Firewall regression receipt | Fixtures never hit prod | `none` | 1 |
| A089 | Rate-limit and budget probe | Pre-prod | Load + budget probe | Limit effectiveness report | Caps enforced in gateway | `none` | 1 |
| A090 | Connector decommission checklist | Retirement request | Inventory + dependency scan | Decommission plan + evidence | Revoke creds via human-approved path | `plan` | 2 |

### 10. Knowledge & Docs Copilot (`knowledge-docs-copilot`)

Keeps runbooks, diagrams, and policies evidence-linked

| ID | Automation | Trigger | Connector / capability | Expected output | Key guardrail | Mutation | Phase |
|---|---|---|---|---|---|---|---:|
| A091 | Runbook freshness audit | Monthly | Runbook + last-incident dates | Stale runbook list | Do not delete runbooks | `plan` | 2 |
| A092 | Architecture diagram delta | Significant system PR | Archify skill + repo evidence | Validated Archify HTML + receipt | Showcase validate before handoff | `plan` | 2 |
| A093 | API docs vs OpenAPI drift | API PR / weekly | OpenAPI + docs diff | Drift findings | Read-only | `none` | 1 |
| A094 | Security policy Q&A with citations | On demand | Policy corpus fetch | Answer with citations only | Refuse if uncited | `none` | 1 |
| A095 | Onboarding path verification | Quarterly | Onboarding docs + scripts | Broken-step report | No credential creation | `none` | 1 |
| A096 | Incident postmortem drafter | Incident resolved | Timeline + actions | Postmortem draft | Human owns blame-free edit | `plan` | 2 |
| A097 | Decision log indexer | ADR merged | ADR corpus index | Searchable decision index | No silent ADR rewrites | `none` | 1 |
| A098 | External doc fetch with injection guard | Research request | Web fetch via gateway | Safe summary + sources | Sandbox untrusted HTML/MD | `none` | 1 |
| A099 | Memory / knowledge-base hygiene | Weekly | Memory store inventory | Stale/conflicting memory report | No unrestricted memory wipe | `plan` | 2 |
| A100 | Catalog self-audit | Monthly | This catalog + plugin coverage | Coverage & guardrail audit | Track phase roadmap status | `none` | 1 |

## Illustrative workflow — production incident triage

1. Trigger on an alert webhook or scheduled SLO burn-rate check (`A022`, `A025`).
2. Query metrics, traces, logs, recent deploys, and relevant GitHub PRs with **read-only** credentials (`A023`–`A027`).
3. Construct an incident timeline, cluster errors, identify likely changes, estimate blast radius (`A022`, `A023`, `A030`).
4. Produce a structured report with linked evidence, proposed mitigations, and a rollback plan (`A043`).
5. Stop unless an authorized person approves a follow-up mutation (incident issue, feature flag, rollback PR).

## Phased build roadmap

| Phase | Goal | Automation mutation classes |
|---:|---|---|
| 1 | Read-only foundations | `none` |
| 2 | Plan-only PR/GitOps generation | `plan` |
| 3 | Gateway + approval proxy hardening | gateway controls for future `apply` |
| 4 | Scheduled/event-driven controlled operations | gated `apply` |

## Production readiness definition of done

- [ ] MCP Security Gateway enforces allowlists, schema validation, redaction, budgets, and approval tokens.
- [ ] Every mutate tool is split into `plan_*` / `validate_*` / `apply_*` / `rollback_*`.
- [ ] Cursor Rules cover secrets, tenancy, database safety, infrastructure changes, and audit events.
- [ ] Policy hooks block disallowed shell/MCP/tool calls in project `.cursor/hooks.json`.
- [ ] Priority plugins 1–6 ship as skills with automation blueprints and correlation-ID evidence records.
- [ ] No production shell, unrestricted filesystem, privileged DB, broad cloud admin, or generic HTTP client is exposed to agents.
- [ ] Catalog self-audit (`A100`) passes monthly.

