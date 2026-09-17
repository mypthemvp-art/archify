## Delivery plan

Mapped to the full product milestones in [`INTERACTIVE-MCP-REGISTRY-DASHBOARD.md`](INTERACTIVE-MCP-REGISTRY-DASHBOARD.md) §9.

### Milestone 1 — Registry foundation

- [x] PostgreSQL schema foundation + RLS patterns (`001`–`005`)
- [x] Connector manifest validation, catalog UI (table-first), multi-filters, saved views API
- [x] Version detail pages and owner/certification metadata
- [ ] OIDC production IdP wiring beyond `AUTH_MODE=dev|oidc` scaffold
- [ ] Next.js virtualized table at 100+ scale

### Milestone 2 — Assurance plane

- [x] Security test suite catalog + hard gates (stub runner)
- [x] Quarantine center UI + gateway deny
- [x] Certification checklist + CI certify workflows
- [ ] Ephemeral sandbox runner with synthetic fixtures and signed evidence store
- [ ] Live SBOM/signature/CVE feed ingestion

### Milestone 3 — Gateway enforcement

- [x] Single gateway entry pattern + policy evaluate/invoke
- [x] Schema validation path, redaction, budgets, OTEL, audit
- [x] `/gateway/v1/tools/authorize|invoke`, `/redact`, `/egress/check`
- [x] Core read-only connector portfolio + constrained `github-write`
- [ ] Streamable HTTP MCP terminate at gateway (beyond proxy stub)

### Milestone 4 — Cursor package

- [x] Project mcp gateway + pilot configs
- [x] Hooks preflight/postflight/secret-scan (+ TypeScript examples)
- [x] Rules baseline `00/10/20/30` + LevelUpWorld operating rules
- [x] Archify pilot: Secure PR Guardian + Production Triage Copilot
- [ ] CI proving hooks cannot be bypassed by ordinary project workflows

### Milestone 5 — Controlled mutations

- [x] Approval API, args_hash-bound grants, consume semantics
- [x] First constrained write: `github-write.create_pull_request` (non-prod, dry-run default)
- [ ] Dual approval + step-up for production writes
- [ ] Expand mutations only after observing deny/audit/test quality

### Weeks 1–8 (historical delivery slices)

- [x] Weeks 1–2 registry read path
- [x] Weeks 3–4 observability + cert CI + RLS
- [x] Weeks 5–6 gateway approvals + github-write
- [x] Weeks 7–8 Cursor pilot certification

See [`IMPLEMENTATION-STARTER.md`](IMPLEMENTATION-STARTER.md), [`CERTIFICATION.md`](CERTIFICATION.md), and [`../../pilots/archify/CERTIFICATION.md`](../../pilots/archify/CERTIFICATION.md).
