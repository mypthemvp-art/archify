# MCP Registry Control Plane + Policy Gateway

Catalog and certify MCP connector versions; enforce authorization, tenant/environment scoping, exact approval binding, redaction, budgets, and immutable audit on a **server-side gateway**.

## Quick start

```bash
# Generate top-10 connector manifests
node levelupworld/registry/scripts/generate-connectors.mjs

# Install and run gateway + dashboard
python3 -m venv levelupworld/registry/.venv
levelupworld/registry/.venv/bin/pip install -r levelupworld/registry/gateway/requirements.txt
levelupworld/registry/.venv/bin/uvicorn app.main:app \
  --app-dir levelupworld/registry/gateway \
  --host 127.0.0.1 --port 8787

# Open dashboard
open http://127.0.0.1:8787/
```

Tests:

```bash
levelupworld/registry/.venv/bin/pytest -q levelupworld/registry/gateway/tests
```

## Layout

| Path | Role |
|---|---|
| `docs/BLUEPRINT.md` | Architecture + control matrix |
| `docs/BUILD-SEQUENCE.md` | 8-week plan |
| `docs/APPROVAL-TOKENS.md` | Signed grant design |
| `schema/001_init.sql` | Postgres schema |
| `connectors/*.manifest.json` | Top-10 certified/core connectors |
| `gateway/` | FastAPI registry + policy gateway |
| `dashboard/` | Catalog / Lab / Ops / Audit / Approvals UI |

## API surface (v1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/connectors` | Catalog with filters |
| GET | `/api/v1/connectors/{slug}` | Connector detail |
| GET | `/api/v1/connectors/{slug}/versions/{version}` | Pinned version + activations |
| POST | `/api/v1/connectors/{slug}/versions/{version}/test-runs` | Sandbox certification suite |
| GET | `/api/v1/test-runs/{id}` | Test run report |
| POST | `/api/v1/activations` | Request project/env activation |
| POST | `/api/v1/activations/{id}/approve` | Approve/deny activation |
| POST | `/api/v1/connectors/{slug}/quarantine` | Emergency gateway quarantine |
| POST | `/api/v1/policy/evaluate` | Preflight policy decision |
| POST | `/api/v1/gateway/invoke` | Policy → approval → stub invoke → redact → audit |
| POST | `/api/v1/approvals` | Create approval request |
| POST | `/api/v1/approvals/{id}/decide` | Issue/deny signed grant |
| GET | `/api/v1/metrics/connectors` | Ops metrics by connector |
| GET | `/api/v1/audit/invocations` | Immutable evidence trail |
| GET | `/api/v1/policies/{policyKey}/decisions` | Policy decision log |

## Docs

- [`docs/IMPLEMENTATION-STARTER.md`](docs/IMPLEMENTATION-STARTER.md) — product contract
- [`docs/CERTIFICATION.md`](docs/CERTIFICATION.md) — certification checklist
- [`docs/APPROVAL-TOKENS.md`](docs/APPROVAL-TOKENS.md) — signed grants
- [`docs/BUILD-SEQUENCE.md`](docs/BUILD-SEQUENCE.md) — 8-week delivery plan
- [`schema/001_init.sql`](schema/001_init.sql) / [`schema/002_implementation_starter.sql`](schema/002_implementation_starter.sql)

## Security defaults

- Gateway is the authority; hooks are preflight only.
- Read-only connectors first; deny kubectl/terraform/cloud-admin/db-superuser/unrestricted-http/prod-shell.
- Approvals bind to exact `args_hash`; argument changes invalidate grants.
- Quarantine disables a version at the gateway even if still listed in Cursor mcp.json.
- Fail closed for medium/high risk when approval validation fails.
