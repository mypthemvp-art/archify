# Multi-Tenant Interactive MCP Registry Dashboard

**Status:** summary index — the authoritative full product specification is:

→ [`INTERACTIVE-MCP-REGISTRY-DASHBOARD.md`](INTERACTIVE-MCP-REGISTRY-DASHBOARD.md)

That document is the complete Product, Security, Data, API, and Cursor Hook Specification for a self-hosted multi-tenant registry and control plane for 100+ MCP connectors.

## Central security position

> A connector registry is not just a marketplace. It is a capability-management system. The registry records allowed capabilities; the runtime gateway independently enforces them.

| Plane | Role |
|---|---|
| Registry / dashboard | Control plane: catalog, certify, activate, monitor, quarantine |
| Policy gateway | Authoritative enforcement: authz, schema, approvals, budgets, redaction, audit |
| Cursor hooks | Local preflight/postflight only |

## Executable companions

| Artifact | Path |
|---|---|
| Full DDL target | [`../schema/005_full_product_model.sql`](../schema/005_full_product_model.sql) |
| Additive teams/meta | [`../schema/004_multi_tenant_dashboard.sql`](../schema/004_multi_tenant_dashboard.sql) |
| Filter TypeScript model | [`../types/connector-filters.ts`](../types/connector-filters.ts) |
| Security test lab | [`SECURITY-TEST-LAB.md`](SECURITY-TEST-LAB.md) |
| Approval grants | [`APPROVAL-TOKENS.md`](APPROVAL-TOKENS.md) |
| Build sequence / milestones | [`BUILD-SEQUENCE.md`](BUILD-SEQUENCE.md) |
