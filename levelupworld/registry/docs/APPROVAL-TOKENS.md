# Signed approval grants

## Purpose

Convert human approval intent into a **short-lived, server-issued authorization grant** bound to exact tool arguments. Prevents the failure mode where an agent is approved for a benign action, then alters arguments and reuses the approval.

For production-impacting writes, do **not** rely only on a Cursor approval click. Combine IDE user-intent confirmation with a backend grant enforceable across Cursor, CLIs, background agents, and any MCP client.

## Bound attributes (must all match)

```text
actor / workload identity
organization, project, and tenant
connector version ID
exact tool ID
canonical normalized-arguments hash
target environment
idempotency key
policy version
not-before and expiration times
required approver count and identities
```

The gateway **rejects** execution if any attribute changes and **atomically consumes** the grant (no replay / duplicate execution).

## Grant claims (current gateway JWT)

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
  "policy_version": "pol_v1",
  "nbf": 1770000000,
  "scope": ["github:pull_request:create"],
  "iat": 1770000000,
  "exp": 1770000300,
  "approval_request_id": "apr_…",
  "required_approvers": ["user:boss"]
}
```

`policy_version`, `nbf`, and `required_approvers` are specified for multi-tenant dashboard parity; extend `approvals.py` claims as those fields are enforced in production IdP mode.

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
  assert now < exp and now >= max(iat, nbf)
  assert grant.aud == "mcp-gateway"
  assert grant.sub == request.actor
  assert grant.org/tenant/project/environment match request
  assert grant.connector_slug/version and tool_name match
  assert grant.args_hash == hash(canonicalize(request.arguments))
  assert grant.idempotency_key == request.idempotency_key
  assert grant.policy_version matches active policy (when set)
  assert grant not revoked and atomically mark consumed
  return allow
```

## Dual approval + step-up (production)

| Environment | Default `required_approver_count` | Step-up |
|---|---:|---|
| development / staging | 1 | optional |
| production | 2 (`PRODUCTION_REQUIRED_APPROVERS`) | required (`step_up_verified=true` on each approve) |

Rules:

- Actor **cannot** self-approve when count ≥ 2.
- Status is `partially_approved` until enough distinct approvers approve.
- Grant JWT includes `required_approvers`, `required_approver_count`, `approval_mode`, `step_up`.
- Production invoke rejects grants that lack dual-approver evidence in claims.

```http
POST /api/v1/approvals/{id}/decide
{ "approver": "user:boss1", "approve": true, "step_up_verified": true }
```
