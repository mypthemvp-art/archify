# Gateway persistence (Phase B)

In-memory stores remain the default for local/demo and CI.

When `DATABASE_URL` is set, the gateway dual-writes:

- audit events → `gateway_audit_events` (hash chain preserved in payload)
- approval requests / grants → `gateway_approval_requests`, `gateway_approval_grants`

## Apply schema

```bash
psql "$DATABASE_URL" -f levelupworld/registry/schema/006_gateway_runtime.sql
```

Optional local database:

```bash
docker compose -f levelupworld/registry/docker-compose.yml up -d
export DATABASE_URL=postgresql://gateway:gateway@127.0.0.1:54329/agent_ops
psql "$DATABASE_URL" -f levelupworld/registry/schema/006_gateway_runtime.sql
```

RLS: every session sets `app.org_id` from the authenticated principal (see `db.py`). Clients cannot spoof org by header when OIDC claims are present.

`GET /healthz` reports `persistence: postgres|memory`.
