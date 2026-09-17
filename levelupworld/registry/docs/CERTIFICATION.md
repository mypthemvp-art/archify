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

- [ ] Structured OpenTelemetry traces/metrics/logs
- [ ] Append-only audit events with correlation IDs
- [ ] Incident runbook linked
- [ ] Owner, SLO, certificate expiry date recorded
- [ ] Emergency quarantine action verified end-to-end at the gateway

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
