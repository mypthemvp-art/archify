# Connector certification checklist

A connector **cannot** be marked `certified` until all items pass. The gateway must refuse activation into production when certification is incomplete or digest/signature/manifest hash mismatches.

## Supply chain & ownership

- [ ] Pinned semantic version and immutable image digest
- [ ] Signed source/image provenance (Cosign/Sigstore)
- [ ] SBOM published and linked
- [ ] Vulnerability scan clean for critical/high (or waived with expiry)
- [ ] Named owner team and escalation contact
- [ ] Manifest SHA-256 stored and verified on activation

## Tool contract

- [ ] Minimal tool manifest with JSON Schemas for every tool
- [ ] Clear `read` / `write` / `delete` / `external_communication` labels
- [ ] Risk levels and policy keys assigned
- [ ] Approval required for all mutation/external tools
- [ ] Timeouts, max calls/run, max calls/minute, max response bytes declared

## Identity & network

- [ ] OAuth or workload identity with exact scopes
- [ ] No embedded long-lived secrets in manifests or Cursor config
- [ ] Tenant/environment/resource authorization verified in **both** gateway and connector
- [ ] Network egress allowlist and SSRF protections

## Adversarial & safety tests

- [ ] Argument validation for SQL injection, path traversal, shell injection, unsafe URLs
- [ ] Prompt-injection tests using hostile external content
- [ ] Output redaction for secrets, PII, and excessive response sizes
- [ ] Idempotency tests for mutation tools
- [ ] Approval-binding tests: altered arguments after approval must fail
- [ ] AuthN/entitlement negative tests
- [ ] Timeout / retry / circuit-breaker / rate-limit tests

## Operations

- [x] Structured OpenTelemetry traces/metrics on the gateway (`otel_setup.py`, OTLP optional)
- [x] Append-only audit events with correlation IDs
- [ ] Incident runbook linked
- [ ] Owner, SLO, certificate expiry date recorded
- [x] Emergency quarantine action verified end-to-end at the gateway

## CI gate (automated)

GitHub Actions workflow [`.github/workflows/registry-cert.yml`](../../../.github/workflows/registry-cert.yml) runs on registry changes:

1. Regenerate manifests and fail if committed JSON/YAML is stale
2. `node levelupworld/registry/scripts/certify-connectors.mjs` (top-10 + `github-write`)
3. Agent-ops contract checks
4. Gateway pytest (`AUTH_MODE=disabled`, `GITHUB_WRITE_DRY_RUN=1`)
5. Live API smoke: sandbox test-run + approval-bound `github-write.create_pull_request` dry-run

## First constrained mutation

`github-write` (`create_pull_request`) is certified only for **non-production** environments:

- Allowed: `development`, `staging` (never `production`)
- Requires signed grant bound to exact `args_hash`
- Default `GITHUB_WRITE_DRY_RUN=1`; live calls need token + explicit repo allowlist

## Registry gate

```text
certify(version):
  require all checklist items == pass
  require manifest_sha256 matches signed artifact
  require image_digest matches OCI digest
  set certification_status = certified
  set last_security_review_at = now
```

Quarantine clears `enabled` on all activations and forces gateway deny regardless of local Cursor `mcp.json`.
