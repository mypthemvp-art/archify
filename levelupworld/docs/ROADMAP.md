# LevelUpWorld implementation roadmap

## Phase 1 — Read-only foundations

**Goal:** deliver value with discovery tools only.

- Install project Rules + catalog router skill + Secure PR Guardian + Production Triage Copilot (read paths).
- Enable workspace-scoped filesystem, git, and read-only GitHub MCP entries in `.cursor/mcp.json`.
- Ship policy hooks that deny shell patterns associated with production mutation and deny unknown MCP tools.
- Activate automations with `mutation: none` (see `catalog.json`).

**Exit criteria:** PR risk summary and failed-CI analysis run end-to-end with evidence records and zero mutate tools registered.

## Phase 2 — Plan-only GitOps

**Goal:** agents may draft reviewable changes, never apply them.

- Add Database Change Guardian + GitOps Release Controller plan skills.
- Allow `plan_*` / `validate_*` tools that open PRs or write proposal markdown in-repo.
- Keep cluster/DB/cloud apply paths unimplemented or permanently denied.

**Exit criteria:** migration safety and rollback PR drafts land as PRs with human review required by CODEOWNERS.

## Phase 3 — Gateway hardening

**Goal:** make connector expansion safe.

- Productionize MCP Security Gateway: allowlists, JSON Schema validation, redaction, spend governor, injection firewall, replay harness.
- Require correlation IDs and immutable audit events for every tool call.
- Add Compliance Evidence Engine read packs.

**Exit criteria:** hostile fixture corpus (`A088`) and permission lint (`A011`) pass in CI-like replay.

## Phase 4 — Controlled apply operations

**Goal:** scheduled/event-driven mutations with approval gates.

- Implement approval proxy (`A013`) with args-hash tokens.
- Enable a minimal set of `apply_*` / `rollback_*` tools (feature flags, incident issues, GitOps merge after checks)—never raw prod shell.
- Enforce tool/time/token/cost budgets on every scheduled automation.

**Exit criteria:** production readiness checklist below is fully checked.

## Production readiness definition of done

- [ ] MCP Security Gateway enforces allowlists, schema validation, redaction, budgets, and approval tokens.
- [ ] Every mutate tool is split into `plan_*` / `validate_*` / `apply_*` / `rollback_*`.
- [ ] Cursor Rules cover secrets, tenancy, database safety, infrastructure changes, and audit events.
- [ ] Policy hooks block disallowed shell/MCP/tool calls via `.cursor/hooks.json`.
- [ ] Priority plugins 1–6 ship as skills with automation blueprints and correlation-ID evidence records.
- [ ] No production shell, unrestricted filesystem, privileged DB, broad cloud admin, or generic HTTP client is exposed.
- [ ] Catalog self-audit (`A100`) passes on a monthly cadence.
- [ ] Incident triage workflow stops at the report unless a human approves a follow-up mutation.
