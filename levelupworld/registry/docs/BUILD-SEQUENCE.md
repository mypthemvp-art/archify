## Delivery plan

### Week 1–2: registry read path

- [x] Registry schema, connector manifest ingestion, catalog UI, connector detail pages
- [x] Register the ten core connectors as metadata
- [x] SSO/IdP modes (`AUTH_MODE=disabled|dev|oidc`) + org principal on gateway APIs
- [x] Connector version pinning fields in manifests

### Week 3–4: test and observability plane

- [x] Sandbox test-run API stubs + certification suite list
- [x] OpenTelemetry traces/metrics instrumentation (OTLP soft-dep + console export)
- [x] Policy-decision and invocation audit tables/APIs
- [x] Automated certification checks in GitHub Actions (`.github/workflows/registry-cert.yml`)
- [x] Postgres RLS policies via `app.org_id` GUC (`schema/003_rls_policies.sql` + `db.py`)

### Week 5–6: gateway and approvals

- [x] MCP gateway with read-only connectors first (stub adapters)
- [x] JSON-schema path, output redaction, tool budgets, audit events
- [x] Approval requests and signed grants with exact args_hash binding
- [x] First constrained mutation connector: `github-write.create_pull_request` (non-prod, dry-run default, repo allowlist, signed grants)

### Week 7–8: Cursor package

- [x] Cursor plugin Rules/Skills/hooks + project gateway config
- [x] Hooks inject correlation IDs and call gateway when configured
- [x] Pilot Secure PR Guardian and Production Triage Copilot in one repository (`levelupworld/pilots/archify`)
- [x] Certify the workflow before expanding (`certify-pilot.mjs` + `.github/workflows/pilot-cert.yml`)

See [`IMPLEMENTATION-STARTER.md`](IMPLEMENTATION-STARTER.md), [`CERTIFICATION.md`](CERTIFICATION.md), and [`../../pilots/archify/CERTIFICATION.md`](../../pilots/archify/CERTIFICATION.md).
