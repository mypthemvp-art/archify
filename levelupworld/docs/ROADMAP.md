# LevelUpWorld / agent-ops roadmap

## Phase 1 — Foundation

- Plugin skeleton (`agent-ops`) and shared Rules with the safety baseline.
- Authenticated MCP gateway using OpenAI MCPKit / FastMCP patterns.
- Audit events, tenant context, capability allowlists, read/write separation, approval service.
- Start with GitHub read-only, workspace filesystem, CI logs, documentation fetch, Postgres read replica.

**Exit:** policy hooks enforce denylist; read-only MCP servers configured; catalog router + gateway skill available.

## Phase 2 — Highest-value workflows

- Implement Secure PR Guardian, Production Triage Copilot, and Database Change Guardian.
- Deterministic artifacts: Markdown reports, JSON findings, JUnit/SARIF where appropriate, linked evidence.
- Every automation runnable locally in a disposable repository and in CI.

**Exit:** A003/A004/A021/A024/A040/A047 produce evidence-backed reports with zero mutate tools registered.

## Phase 3 — Controlled writes

- GitHub issue/PR creation through approval-gated tools.
- Feature-flag creation/updates with staged rollout limits (FeatureOps).
- GitOps pull-request generation — **no** direct cluster mutation from Cursor.

**Exit:** `apply_*` requires bound approval token; GitOps PRs are the only infra mutation path.

## Phase 4 — Scheduled / event automations

- Cursor Automations for daily security/cost/observability summaries and event-triggered incident triage.
- Bind schedules to a service identity with narrow scopes and a per-run budget.
- External notifications only through a dedicated notification tool with policy checks and delivery audit.

**Exit:** production readiness checklist below is fully checked for each enabled automation.

## Definition of done

An automation is production-ready only when it has:

- [ ] Documented tool contract and threat model
- [ ] Unit, integration, and adversarial prompt-injection tests
- [ ] Least-privilege credentials with a rotation path
- [ ] Explicit approval binding for mutations
- [ ] Idempotency and concurrency handling
- [ ] Structured audit trail and searchable correlation IDs
- [ ] Dry-run path and clear rollback/runbook
- [ ] Timeouts, retries, rate limits, and token/cost budgets
- [ ] Sandbox/staging validation before production availability
- [ ] Owner, SLO, deprecation policy, and incident response path
