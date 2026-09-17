# Signed approval grants

## Purpose

Convert human approval intent into a **short-lived, server-issued authorization grant** bound to exact tool arguments. Prevents the failure mode where an agent is approved for a benign action, then alters arguments and reuses the approval.

## Grant claims

```json
{
  "grant_id": "grn_01J...",
  "iss": "agent-ops-gateway",
  "sub": "user:alice@acme.example",
  "aud": "mcp-gateway",
  "org_id": "org_acme",
  "tenant_id": "tenant_acme",
  "project_id": "proj_agent_platform",
  "environment": "staging",
  "connector_slug": "github-write",
  "connector_version": "1.4.2",
  "tool_name": "create_pull_request",
  "args_hash": "sha256:…",
  "idempotency_key": "idem_…",
  "scope": ["github:pull_request:create"],
  "iat": 1770000000,
  "exp": 1770000300,
  "approval_request_id": "apr_…"
}
```

## Canonical args hash

1. Parse tool arguments as JSON.
2. Reject unknown properties for mutate tools.
3. Normalize: UTF-8, sorted object keys, no insignificant whitespace, arrays preserve order.
4. Hash with SHA-256 over the canonical bytes.
5. Store as `sha256:<hex>`.

Any change to repository, branches, body, linked issue, tenant/project, environment, tool name, or other mutation-bearing fields changes `args_hash` and **invalidates** the grant.

## Verification algorithm

```text
verify_grant(grant, request):
  assert signature valid with current gateway keyset
  assert now < exp and now >= iat
  assert grant.aud == "mcp-gateway"
  assert grant.sub == request.actor
  assert grant.tenant/project/environment match request
  assert grant.connector_slug/version and tool_name match
  assert grant.args_hash == hash(canonicalize(request.arguments))
  assert grant.idempotency_key == request.idempotency_key
  assert grant not revoked and not already consumed (or allow idempotent replay with same key)
  return allow
```

## Security properties

- TTL typically 1–15 minutes for high-risk tools.
- Single-use or idempotent-replay only (same key + same hash).
- Fail closed if signing keys or approval service unavailable for medium/high risk.
- Audit both grant issuance and grant consumption with correlation IDs.
