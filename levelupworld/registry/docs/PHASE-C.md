# Phase C — production lifecycle hardening

After Milestones 1–5, Phase C closes remaining control-plane lifecycle gaps from [`INTERACTIVE-MCP-REGISTRY-DASHBOARD.md`](INTERACTIVE-MCP-REGISTRY-DASHBOARD.md) §5 before expanding the certified portfolio or mutation surface.

## APIs

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/connectors?limit=&cursor=` | Cursor-paginated filtered catalog |
| POST | `/api/v1/connectors/{slug}/unquarantine` | Lift quarantine with reason |
| POST | `/api/v1/connectors/{slug}/versions/{version}/unquarantine` | Version-scoped lift |
| GET | `/api/v1/quarantines` | Active (or historical) quarantine records |
| POST | `/api/v1/activations/{id}/disable` | Disable an activation |
| POST | `/api/v1/activations/{id}/renew` | Extend expiry / re-enable when safe |
| POST | `/api/v1/connectors/{slug}/versions/{version}/certification-decisions` | `review` / `certify` / `fail` / `waive` |
| GET | `/api/v1/certification-queue` | Reviewer work queue |
| GET | `/api/v1/certification-decisions` | Decision history |
| GET | `/api/v1/health/connectors` | Ops health summaries |
| POST | `/api/v1/supply-chain/refresh` | Re-ingest SBOM/CVE feed; auto-quarantine `blocked` |
| POST | `/gateway/v1/tools/complete` | Record async tool outcome |

## Rules unchanged

- Dashboard / control plane records intent; **gateway remains authoritative enforcement**.
- Hooks stay preflight-only.
- Do not expand write connectors until `GET /api/v1/metrics/mutations` observe gate + human review (see [`MUTATION-OBSERVE.md`](MUTATION-OBSERVE.md)).
- Onboard additional catalog categories one at a time (sandboxed → reviewed → certified).

## Category onboarding progress

| Category | Connector | Trust | Status |
|---|---|---|---|
| feature_flags | `feature-flags-readonly` | sandboxed / in_lab | Gateway adapter + certify gate; non-prod only; no mutate tools |