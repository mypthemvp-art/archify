# Gateway authentication (IdP / OIDC)

## Modes

| `AUTH_MODE` | Behavior |
|---|---|
| `disabled` | Local/demo principal from `X-Actor` / `X-Org-ID` headers (tests) |
| `dev` | HS256 bearer via `/api/v1/auth/dev-token`, or trusted `X-*` headers |
| `oidc` | Production: validate JWT with JWKS (`RS256`/`ES256`/`PS256`) |

## Production OIDC checklist

Required environment variables when `AUTH_MODE=oidc`:

```bash
export AUTH_MODE=oidc
export OIDC_ISSUER=https://login.example.com/realms/agent-ops
export OIDC_AUDIENCE=mcp-gateway
export OIDC_JWKS_URL=https://login.example.com/realms/agent-ops/protocol/openid-connect/certs
export OIDC_ORG_CLAIM=org_id          # or org.path claim
export OIDC_TENANT_CLAIM=tenant_id
export OIDC_ROLES_CLAIM=roles         # or realm_access.roles via custom mapper
export OIDC_JWKS_CACHE_TTL=300
```

Rules:

- `iss` / `aud` / `exp` / `iat` / `sub` required.
- Org is taken from the token claim; `X-Org-ID` must match when present (no client spoofing).
- Roles drive `require_roles(...)` on approval/quarantine APIs.
- Public metadata: `GET /api/v1/auth/config` (no secrets).

## Dev token (non-oidc)

```bash
curl -s -X POST http://127.0.0.1:8787/api/v1/auth/dev-token \
  -H 'content-type: application/json' \
  -d '{"subject":"user:dev","org_id":"org_demo","roles":["operator","approver"]}'
```
