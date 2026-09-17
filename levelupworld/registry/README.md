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
| POST | `/api/v1/policy/evaluate` | Preflight policy decision |
| POST | `/api/v1/gateway/invoke` | Policy → (approval) → stub invoke → redact → audit |
| POST | `/api/v1/approvals` | Create approval request |
| POST | `/api/v1/approvals/{id}/decide` | Issue/deny signed grant |
| GET | `/api/v1/audit/events` | Immutable evidence trail |
| GET | `/api/v1/ops/summary` | Monitoring counters |

## Cursor integration

Point project MCP at the gateway (not each powerful connector). Pre-tool hooks call `/api/v1/policy/evaluate`; post-tool hooks rely on gateway audit. See:

- `.cursor/hooks/policy-pre-tool.mjs` (calls gateway when `AGENT_OPS_GATEWAY_URL` is set)
- `.cursor/mcp.json`
- `.cursor/plugins/local/agent-ops/`

## Security defaults

- Gateway is the authority; hooks are preflight only.
- Read-only connectors first; deny kubectl/terraform/cloud-admin/db-superuser/unrestricted-http/prod-shell.
- Approvals bind to exact `args_hash`; argument changes invalidate grants.
- Fail closed for medium/high risk when approval validation fails.
