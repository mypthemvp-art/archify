# MCP Registry Control Plane + Policy Gateway

Catalog and certify MCP connector versions; enforce authorization, tenant/environment scoping, exact approval binding, redaction, budgets, and immutable audit on a **server-side gateway**.

## Quick start

```bash
# Generate core connectors + github-write + sandboxed feature-flags-readonly
node levelupworld/registry/scripts/generate-connectors.mjs
node levelupworld/registry/scripts/certify-connectors.mjs

# Install and run gateway + dashboard
python3 -m venv levelupworld/registry/.venv
levelupworld/registry/.venv/bin/pip install -r levelupworld/registry/gateway/requirements.txt
AUTH_MODE=disabled GITHUB_WRITE_DRY_RUN=1 \
  levelupworld/registry/.venv/bin/uvicorn app.main:app \
  --app-dir levelupworld/registry/gateway \
  --host 127.0.0.1 --port 8787

# Open dashboard
open http://127.0.0.1:8787/
```

Tests:

```bash
AUTH_MODE=disabled GITHUB_WRITE_DRY_RUN=1 \
  levelupworld/registry/.venv/bin/pytest -q levelupworld/registry/gateway/tests
```

## Weeks 3–6 capabilities

| Capability | How |
|---|---|
| IdP / principal | `AUTH_MODE=disabled\|dev\|oidc` — JWT + org/tenant/roles (`app/auth.py`) |
| Postgres RLS | `DATABASE_URL` + `schema/003_rls_policies.sql`; sessions set `app.org_id` |
| OpenTelemetry | Soft-dep OTLP (`OTEL_EXPORTER_OTLP_ENDPOINT`) or `OTEL_CONSOLE=1` |
| Cert CI | `.github/workflows/registry-cert.yml` |
| First mutation | `github-write.create_pull_request` — non-prod, signed grant, dry-run default |

## Layout

| Path | Role |
|---|---|
| `docs/BLUEPRINT.md` | Architecture + control matrix |
| `docs/BUILD-SEQUENCE.md` | 8-week plan |
| `docs/APPROVAL-TOKENS.md` | Signed grant design |
| `schema/001_init.sql` | Postgres schema |
| `schema/003_rls_policies.sql` | RLS via `app.org_id` |
| `connectors/*.manifest.json` | Core connectors + `github-write` |
| `gateway/` | FastAPI registry + policy gateway |
| `dashboard/` | Catalog / Lab / Ops / Audit / Approvals UI |
| `schema/006_gateway_runtime.sql` | Postgres dual-write for audit/approvals (`DATABASE_URL`) |
| `docs/PERSISTENCE.md` | Phase B persistence runbook |

## API surface (v1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness + auth/RLS mode |
| GET | `/api/v1/auth/whoami` | Current principal |
| POST | `/api/v1/auth/dev-token` | Issue HS256 token (`AUTH_MODE=dev`) |
| GET | `/api/v1/connectors` | Catalog with filters |
| GET | `/api/v1/connectors/{slug}` | Connector detail |
| GET | `/api/v1/connectors/{slug}/versions/{version}` | Pinned version + activations |
| POST | `/api/v1/connectors/{slug}/versions/{version}/test-runs` | Sandbox certification suite |
| GET | `/api/v1/test-runs/{id}` | Test run report |
| POST | `/api/v1/activations` | Request project/env activation |
| POST | `/api/v1/activations/{id}/approve` | Approve/deny activation |
| POST | `/api/v1/connectors/{slug}/quarantine` | Emergency gateway quarantine |
| POST | `/api/v1/policy/evaluate` | Preflight policy decision |
| POST | `/api/v1/gateway/invoke` | Policy → approval → adapter invoke → redact → audit |
| POST | `/api/v1/approvals` | Create approval request |
| POST | `/api/v1/approvals/{id}/decide` | Issue/deny signed grant |
| GET | `/api/v1/metrics/connectors` | Ops metrics by connector |
| GET | `/api/v1/health/connectors` | Connector health summaries |
| GET | `/api/v1/certification-queue` | Reviewer certification queue |
| POST | `/api/v1/supply-chain/refresh` | Re-ingest SBOM/CVE posture |
| POST | `/gateway/v1/tools/complete` | Async invoke completion |
| GET | `/api/v1/audit/invocations` | Immutable evidence trail |
| GET | `/api/v1/policies/{policyKey}/decisions` | Policy decision log |

## Docs

- [`docs/INTERACTIVE-MCP-REGISTRY-DASHBOARD.md`](docs/INTERACTIVE-MCP-REGISTRY-DASHBOARD.md) — full Product/Security/Data/API/Hooks specification
- [`docs/MULTI-TENANT-DASHBOARD-SPEC.md`](docs/MULTI-TENANT-DASHBOARD-SPEC.md) — index into the full spec
- [`docs/IMPLEMENTATION-STARTER.md`](docs/IMPLEMENTATION-STARTER.md) — product contract
- [`docs/SECURITY-TEST-LAB.md`](docs/SECURITY-TEST-LAB.md) — suite families + hard gates
- [`docs/CERTIFICATION.md`](docs/CERTIFICATION.md) — certification checklist + CI gate
- [`docs/APPROVAL-TOKENS.md`](docs/APPROVAL-TOKENS.md) — signed grants
- [`docs/BUILD-SEQUENCE.md`](docs/BUILD-SEQUENCE.md) — milestones M1–M5 + Phase C
- [`docs/PHASE-C.md`](docs/PHASE-C.md) — production lifecycle hardening APIs
- [`schema/001_init.sql`](schema/001_init.sql) … [`schema/005_full_product_model.sql`](schema/005_full_product_model.sql)
- [`types/connector-filters.ts`](types/connector-filters.ts) — shareable filter model

## Security defaults

- Gateway is the authority; hooks are preflight only.
- Read-only connectors first; deny kubectl/terraform/cloud-admin/db-superuser/unrestricted-http/prod-shell.
- Approvals bind to exact `args_hash`; argument changes invalidate grants.
- Quarantine disables a version at the gateway even if still listed in Cursor mcp.json.
- Fail closed for medium/high risk when approval validation fails.
- `github-write` never allowed in production; live PRs require allowlist + token and still need a grant.
