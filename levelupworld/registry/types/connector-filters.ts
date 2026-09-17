/**
 * Catalog filter model for the Interactive MCP Registry Dashboard.
 * Keep these fields mirrored in URL query params for shareable saved views.
 * @see docs/INTERACTIVE-MCP-REGISTRY-DASHBOARD.md §2.5
 */

export type ConnectorOperation =
  | "read"
  | "write"
  | "delete"
  | "external_communication"
  | "exec";

export type ConnectorFilters = {
  query?: string;
  categories?: string[];
  operations?: ConnectorOperation[];
  trustTiers?: number[];
  lifecycle?: string[];
  environments?: string[];
  transports?: string[];
  dataClassifications?: string[];
  authModes?: string[];
  health?: string[];
  ownerIds?: string[];
  hasWriteTools?: boolean;
  hasCurrentCve?: boolean;
  certificationExpiringBefore?: string;
  outboundDomains?: string[];
  sort?: "name" | "activity_24h" | "error_rate" | "p95_latency" | "cert_expiry" | "rank";
  direction?: "asc" | "desc";
  cursor?: string;
  pageSize?: number;
};

/** Built-in saved views (§2.2). */
export const BUILTIN_SAVED_VIEWS: Record<string, Partial<ConnectorFilters>> = {
  "certified-readonly-prod": {
    operations: ["read"],
    trustTiers: [3, 4],
    environments: ["production"],
    health: ["healthy", "degraded"],
  },
  "cert-expiring-30d": {
    trustTiers: [3, 4],
    environments: ["production"],
    // certificationExpiringBefore set by client to now+30d
  },
  "write-requires-approval": {
    operations: ["write", "delete", "external_communication", "exec"],
  },
  "quarantined": {
    lifecycle: ["quarantined", "revoked"],
  },
  "staging-candidates": {
    trustTiers: [2, 3],
    environments: ["staging"],
  },
};

export function filtersToQuery(filters: ConnectorFilters): string {
  const params = new URLSearchParams();
  if (filters.query) params.set("q", filters.query);
  if (filters.categories?.length) params.set("category", filters.categories.join(","));
  if (filters.operations?.length) params.set("operation", filters.operations.join(","));
  if (filters.trustTiers?.length) params.set("trustTier", filters.trustTiers.join(","));
  if (filters.environments?.length) params.set("environment", filters.environments.join(","));
  if (filters.health?.length) params.set("health", filters.health.join(","));
  if (filters.transports?.length) params.set("transport", filters.transports.join(","));
  if (filters.dataClassifications?.length) {
    params.set("data_classification", filters.dataClassifications.join(","));
  }
  if (filters.certificationExpiringBefore) {
    params.set("certExpiresBefore", filters.certificationExpiringBefore);
  }
  if (filters.sort) {
    const prefix = filters.direction === "desc" ? "-" : "";
    params.set("sort", `${prefix}${filters.sort}`);
  }
  if (filters.pageSize) params.set("pageSize", String(filters.pageSize));
  if (filters.cursor) params.set("cursor", filters.cursor);
  return params.toString();
}
