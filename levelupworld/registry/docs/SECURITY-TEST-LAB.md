# Security Test Lab — suite catalog

Isolated ephemeral lab for connector certification. Never targets production resources.

Executable stub today: `POST /api/v1/connectors/{slug}/versions/{version}/test-runs?suite=…`  
Full family matrix is the certification contract; expand adapters toward real probes over time.

## Suites

| Suite key | Families covered |
|---|---|
| `protocol` | MCP init, tool discovery, schema validation, malformed inputs |
| `authn` | Missing/expired tokens, wrong audience, insufficient scope |
| `authz` | Tenant escape, project/environment mismatch, allowlist bypass |
| `input_safety` | SQL injection, path traversal, shell metacharacters, bad URLs, oversized payloads |
| `ssrf_egress` | Metadata IPs, private ranges, redirects, DNS rebinding, unapproved hosts |
| `data_protection` | Secret/PII/PHI redaction, output size caps, retention |
| `prompt_injection` | Hostile issues/logs/docs/web/connector responses |
| `reliability` | Timeouts, retries, circuit breakers, partial failure, duplicates |
| `approval_binding` | Arg mutation, replay, expiry, wrong identity/tenant/env |
| `supply_chain` | Digest pin, signature, SBOM, vuln policy |
| `auditability` | Correlation IDs, policy evidence, tamper-evident events, traces |
| `full` | All of the above (certification gate) |

## Hard fail gates

A `full` suite **fails certification** (not a score reduction) when any gate fails:

1. `pinned_digest`
2. `owner_present`
3. `no_embedded_creds`
4. `egress_restricted`
5. `tenant_authz`
6. `write_tools_require_approval`
7. `immutable_audit`

See [`MULTI-TENANT-DASHBOARD-SPEC.md`](MULTI-TENANT-DASHBOARD-SPEC.md) §4 and [`CERTIFICATION.md`](CERTIFICATION.md).
