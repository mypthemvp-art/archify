## Delivery plan

### Week 1–2: registry read path

- [x] Registry schema, connector manifest ingestion, catalog UI, connector detail pages
- [x] Register the ten core connectors as metadata
- [ ] SSO, org/project RBAC, RLS wired to real IdP
- [x] Connector version pinning fields in manifests

### Week 3–4: test and observability plane

- [x] Sandbox test-run API stubs + certification suite list
- [ ] Live connector health probes and OpenTelemetry ingestion
- [x] Policy-decision and invocation audit tables/APIs
- [ ] Automated certification checks in GitHub Actions

### Week 5–6: gateway and approvals

- [x] MCP gateway with read-only connectors first (stub adapters)
- [x] JSON-schema path, output redaction, tool budgets, audit events
- [x] Approval requests and signed grants with exact args_hash binding
- [ ] First real mutation connector: GitHub PR create in non-prod

### Week 7–8: Cursor package

- [x] Cursor plugin Rules/Skills/hooks + project gateway config
- [x] Hooks inject correlation IDs and call gateway when configured
- [ ] Pilot Secure PR Guardian and Production Triage Copilot in one repository
- [ ] Certify the workflow before expanding

See [`IMPLEMENTATION-STARTER.md`](IMPLEMENTATION-STARTER.md) and [`CERTIFICATION.md`](CERTIFICATION.md).
