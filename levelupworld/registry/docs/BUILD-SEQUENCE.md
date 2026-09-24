## Delivery plan

Mapped to the full product milestones in [`INTERACTIVE-MCP-REGISTRY-DASHBOARD.md`](INTERACTIVE-MCP-REGISTRY-DASHBOARD.md) §9.

### Milestone 1 — Registry foundation

- [x] PostgreSQL schema foundation + RLS patterns (`001`–`005`)
- [x] Connector manifest validation, catalog UI (table-first), multi-filters, saved views API
- [x] Version detail pages and owner/certification metadata
- [x] OIDC production IdP wiring (`gateway/app/oidc.py`, `docs/AUTH.md`, `AUTH_MODE=oidc` + JWKS)
- [x] Next.js virtualized table at 100+ scale (`registry/web` `/registry`; window test `scripts/test-catalog-window.mjs`)

### Milestone 2 — Assurance plane

- [x] Security test suite catalog + hard gates (stub runner)
- [x] Quarantine center UI + gateway deny
- [x] Certification checklist + CI certify workflows
- [x] Ephemeral sandbox runner with HMAC-signed evidence (`scripts/ephemeral-lab-runner.mjs` + `/lab-runs`)
- [x] SBOM/signature/CVE posture ingestion (`scripts/ingest-supply-chain.mjs` + feed → index API)

### Milestone 3 — Gateway enforcement

- [x] Single gateway entry pattern + policy evaluate/invoke
- [x] Schema validation path, redaction, budgets, OTEL, audit
- [x] `/gateway/v1/tools/authorize|invoke`, `/redact`, `/egress/check`
- [x] Core read-only connector portfolio + constrained `github-write`
- [x] Streamable HTTP MCP terminate at gateway (`POST /mcp` JSON-RPC; stdio proxy fallback only)

### Milestone 4 — Cursor package

- [x] Project mcp gateway + pilot configs
- [x] Hooks preflight/postflight/secret-scan (+ TypeScript examples)
- [x] Rules baseline `00/10/20/30` + LevelUpWorld operating rules
- [x] Archify pilot: Secure PR Guardian + Production Triage Copilot
- [x] CI proving hooks cannot be bypassed (`.github/workflows/hooks-bypass-proof.yml`)

### Milestone 5 — Controlled mutations

- [x] Approval API, args_hash-bound grants, consume semantics
- [x] First constrained write: `github-write.create_pull_request` (non-prod, dry-run default)
- [x] Dual approval + step-up for production writes
- [x] Mutation observe gate (`GET /api/v1/metrics/mutations` + `docs/MUTATION-OBSERVE.md`) — expand writes only after staging quality review

### Phase B — Production persistence

- [x] Postgres dual-write for audit + approvals (`schema/006_gateway_runtime.sql`, `gateway/app/persist.py`)
- [x] Optional `docker-compose.yml` for local Postgres (`DATABASE_URL`)
- [x] Persistence runbook (`docs/PERSISTENCE.md`); `/healthz` reports `persistence`

### Phase C — production lifecycle hardening

- [x] Cursor-paginated catalog (`limit` / `next_cursor` on `GET /api/v1/connectors`)
- [x] Unquarantine + quarantine list APIs
- [x] Activation disable / renew
- [x] Certification decisions + reviewer queue
- [x] Connector health summaries (`GET /api/v1/health/connectors`)
- [x] Supply-chain live refresh (`POST /api/v1/supply-chain/refresh`) with auto-quarantine on blocked posture
- [x] Async invoke completion (`POST /gateway/v1/tools/complete`)
- [x] Onboard next sandboxed connector category beyond the core 11 (`feature-flags-readonly`)
- [ ] Expand mutations beyond `github-write` dry-run after staging observe review
- [ ] Hosted gateway deploy with `AUTH_MODE=oidc` (no disabled auth in production)

### Weeks 1–8 (historical delivery slices)

- [x] Weeks 1–2 registry read path
- [x] Weeks 3–4 observability + cert CI + RLS
- [x] Weeks 5–6 gateway approvals + github-write
- [x] Weeks 7–8 Cursor pilot certification

See [`IMPLEMENTATION-STARTER.md`](IMPLEMENTATION-STARTER.md), [`CERTIFICATION.md`](CERTIFICATION.md), [`PERSISTENCE.md`](PERSISTENCE.md), [`PHASE-C.md`](PHASE-C.md), and [`../../pilots/archify/CERTIFICATION.md`](../../pilots/archify/CERTIFICATION.md).
