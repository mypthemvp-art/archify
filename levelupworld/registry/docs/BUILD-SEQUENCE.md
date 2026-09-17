# 8-week build sequence

## Week 1 — Registry foundation

- [x] Blueprint + product design docs
- [x] Postgres schema with RLS hooks (org/tenant/project)
- [x] Connector manifest format + top-10 connector metadata
- [ ] SSO/RBAC wiring (OIDC stub → real IdP)
- [ ] Catalog list/detail API

**Exit:** manifests load; schema migrates; catalog API returns certified/unverified connectors.

## Week 2 — Catalog UI + versioning

- [x] Dashboard shell: Catalog, Test Lab, Operations, Audit
- [ ] Version pin + image digest fields enforced in UI
- [ ] Trust tier badges and certification state machine
- [ ] Ownership / escalation contacts

**Exit:** operators can browse and filter the ten core connectors.

## Week 3 — Gateway core (read-only path)

- [x] Policy gateway FastAPI service skeleton
- [x] Authz stubs, schema validation hooks, budgets, redaction, audit writers
- [ ] Deploy gateway in front of GitHub RO, filesystem sandbox, Git, CI observer, docs fetch, audit store
- [ ] Project MCP config points only at the gateway

**Exit:** Cursor calls go through gateway for at least three read-only connectors.

## Week 4 — Observability

- [ ] OpenTelemetry metrics/traces from gateway
- [ ] Connector health checks + p95/error panels
- [ ] Tool-call evidence in Audit page
- [ ] Policy-denial telemetry

**Exit:** ops dashboard shows live volume, latency, denials for sandbox traffic.

## Week 5 — Test lab + certification

- [ ] Schema-conformance suite per tool
- [ ] Injection / redaction / SSRF / path-traversal suites
- [ ] Approval-binding negative tests
- [ ] Certification checklist gates activation

**Exit:** no connector reaches `certified` without green lab run.

## Week 6 — Approvals + first mutation

- [x] Signed approval grant design + implementation stub
- [ ] Approval request UI + review of fully resolved targets
- [ ] Single constrained mutation: create GitHub PR in non-prod repo
- [ ] Grant re-check before invoke; arg change ⇒ deny

**Exit:** one write tool works end-to-end with exact-argument binding.

## Week 7 — Cursor plugin packaging

- [x] agent-ops Rules / Skills / Hooks / MCP config
- [ ] Point project MCP solely at gateway URL
- [ ] Pre-tool hook → policy service; post-tool → audit
- [ ] Cloud-agent hook verification

**Exit:** disposable repo install works; hooks fail closed when gateway down for high-risk tools.

## Week 8 — Controlled production readiness

- [ ] Production project allowlists
- [ ] Emergency quarantine workflow
- [ ] Budget hard-stops + on-call runbooks
- [ ] Enable only read-heavy production workflows until denial/audit SLOs hold

**Exit:** definition of done for registry+gateway satisfied for the top-10 read-only stack.

## Definition of done (platform)

- Registry knows versions, owners, tools, certifications, scopes, provenance, health, and allowed environments.
- Gateway is the authority for invoke decisions (not hooks alone).
- Approvals bind to exact normalized `args_hash` with short TTL.
- Every call emits an immutable audit event with correlation ID.
- Medium/high-risk actions fail closed if policy/approval services are unavailable.
- No direct production mutation connectors are registered as `certified` without quarantine and dual-control.
