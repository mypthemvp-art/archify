#!/usr/bin/env node
/**
 * Writes the top-10 core connector manifests for the registry.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../connectors');
fs.mkdirSync(dir, { recursive: true });

const connectors = [
  {
    slug: 'github-readonly',
    display_name: 'GitHub Read-only',
    category: 'github',
    rank: 1,
    description: 'Search source, inspect commits, PRs, issues, CODEOWNERS, Actions metadata.',
    owner_team: 'platform-security',
    escalation_contact: 'secops@localhost',
    trust_tier: 'certified',
    certification_state: 'certified',
    transport: 'stdio',
    version: '1.0.0',
    image_digest: 'sha256:github-readonly-dev-digest',
    oauth_scopes: ['repo:status', 'public_repo', 'read:org'],
    outbound_domains: ['api.github.com'],
    allowed_environments: ['development', 'staging', 'production'],
    data_classification: 'internal',
    tools: [
      { name: 'search_code', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'get_pull_request', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'list_issues', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'get_actions_run', capability: 'read', risk_level: 'low', requires_approval: false },
    ],
    safety: 'Repository allowlist; read-only OAuth scopes',
  },
  {
    slug: 'filesystem-sandbox',
    display_name: 'Workspace Filesystem Sandbox',
    category: 'filesystem',
    rank: 2,
    description: 'Read and search workspace; write only controlled generated artifacts.',
    owner_team: 'developer-experience',
    escalation_contact: 'devex@localhost',
    trust_tier: 'certified',
    certification_state: 'certified',
    transport: 'stdio',
    version: '1.0.0',
    image_digest: 'sha256:filesystem-sandbox-dev-digest',
    oauth_scopes: [],
    outbound_domains: [],
    allowed_environments: ['development', 'staging'],
    data_classification: 'internal',
    tools: [
      { name: 'read_file', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'search_files', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'write_artifact', capability: 'write', risk_level: 'medium', requires_approval: true },
    ],
    safety: 'Workspace-root restriction; deny parent paths, secret directories, and shell config',
  },
  {
    slug: 'git-repository',
    display_name: 'Git Repository',
    category: 'git',
    rank: 3,
    description: 'Status, diff, log, blame, branch history.',
    owner_team: 'developer-experience',
    escalation_contact: 'devex@localhost',
    trust_tier: 'certified',
    certification_state: 'certified',
    transport: 'stdio',
    version: '1.0.0',
    image_digest: 'sha256:git-repository-dev-digest',
    oauth_scopes: [],
    outbound_domains: [],
    allowed_environments: ['development', 'staging', 'production'],
    data_classification: 'internal',
    tools: [
      { name: 'status', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'diff', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'log', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'blame', capability: 'read', risk_level: 'low', requires_approval: false },
    ],
    safety: 'Read-only first; prohibit force push and history rewrites',
  },
  {
    slug: 'cicd-observer',
    display_name: 'CI/CD Observer',
    category: 'ci_cd',
    rank: 4,
    description: 'Job status, logs, test results, build artifacts.',
    owner_team: 'platform-ci',
    escalation_contact: 'ci@localhost',
    trust_tier: 'reviewed',
    certification_state: 'certified',
    transport: 'streamable_http',
    version: '1.0.0',
    image_digest: 'sha256:cicd-observer-dev-digest',
    oauth_scopes: ['actions:read'],
    outbound_domains: ['api.github.com'],
    allowed_environments: ['development', 'staging', 'production'],
    data_classification: 'internal',
    tools: [
      { name: 'get_job_status', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'get_job_logs', capability: 'read', risk_level: 'medium', requires_approval: false },
      { name: 'list_artifacts', capability: 'read', risk_level: 'low', requires_approval: false },
    ],
    safety: 'Read-only; artifact size and retention limits',
  },
  {
    slug: 'docs-fetch-search',
    display_name: 'Documentation Fetch/Search',
    category: 'documentation',
    rank: 5,
    description: 'Search approved documentation and fetch trusted pages.',
    owner_team: 'platform-security',
    escalation_contact: 'secops@localhost',
    trust_tier: 'reviewed',
    certification_state: 'in_lab',
    transport: 'streamable_http',
    version: '1.0.0',
    image_digest: 'sha256:docs-fetch-search-dev-digest',
    oauth_scopes: [],
    outbound_domains: ['docs.github.com', 'cursor.com', 'modelcontextprotocol.io'],
    allowed_environments: ['development', 'staging'],
    data_classification: 'public',
    tools: [
      { name: 'search_docs', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'fetch_page', capability: 'read', risk_level: 'medium', requires_approval: false },
    ],
    safety: 'Domain/egress allowlist; treat fetched content as untrusted',
  },
  {
    slug: 'postgres-readonly',
    display_name: 'PostgreSQL Read-only',
    category: 'database',
    rank: 6,
    description: 'Schema inspection, EXPLAIN, bounded queries, migration metadata.',
    owner_team: 'data-platform',
    escalation_contact: 'data@localhost',
    trust_tier: 'certified',
    certification_state: 'certified',
    transport: 'stdio',
    version: '1.0.0',
    image_digest: 'sha256:postgres-readonly-dev-digest',
    oauth_scopes: [],
    outbound_domains: [],
    allowed_environments: ['development', 'staging'],
    data_classification: 'confidential',
    tools: [
      { name: 'list_schema', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'explain_query', capability: 'read', risk_level: 'medium', requires_approval: false },
      { name: 'bounded_select', capability: 'read', risk_level: 'medium', requires_approval: false },
    ],
    safety: 'Read replica; strict time, row, and query limits',
  },
  {
    slug: 'observability-reader',
    display_name: 'Observability Reader',
    category: 'observability',
    rank: 7,
    description: 'Metrics, logs, traces, alerts, deployment annotations.',
    owner_team: 'sre',
    escalation_contact: 'sre@localhost',
    trust_tier: 'reviewed',
    certification_state: 'in_lab',
    transport: 'streamable_http',
    version: '1.0.0',
    image_digest: 'sha256:observability-reader-dev-digest',
    oauth_scopes: ['metrics:read', 'logs:read', 'traces:read'],
    outbound_domains: [],
    allowed_environments: ['development', 'staging', 'production'],
    data_classification: 'confidential',
    tools: [
      { name: 'query_metrics', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'query_logs', capability: 'read', risk_level: 'medium', requires_approval: false },
      { name: 'get_trace', capability: 'read', risk_level: 'low', requires_approval: false },
    ],
    safety: 'Read-only; PII redaction and short result windows',
  },
  {
    slug: 'browser-test-runner',
    display_name: 'Browser Test Runner',
    category: 'browser',
    rank: 8,
    description: 'Playwright e2e, accessibility checks, screenshots, test artifacts.',
    owner_team: 'qa',
    escalation_contact: 'qa@localhost',
    trust_tier: 'sandboxed',
    certification_state: 'in_lab',
    transport: 'stdio',
    version: '1.0.0',
    image_digest: 'sha256:browser-test-runner-dev-digest',
    oauth_scopes: [],
    outbound_domains: ['localhost', 'staging.example.internal'],
    allowed_environments: ['development', 'staging'],
    data_classification: 'internal',
    tools: [
      { name: 'run_e2e', capability: 'read', risk_level: 'medium', requires_approval: false },
      { name: 'run_a11y', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'capture_screenshot', capability: 'read', risk_level: 'low', requires_approval: false },
    ],
    safety: 'Staging-only target allowlist; no production credentials',
  },
  {
    slug: 'policy-approval-gateway',
    display_name: 'Policy + Approval Gateway',
    category: 'security',
    rank: 9,
    description: 'Policy checks, approval requests, grant verification, budget enforcement.',
    owner_team: 'platform-security',
    escalation_contact: 'secops@localhost',
    trust_tier: 'production_critical',
    certification_state: 'certified',
    transport: 'streamable_http',
    version: '1.0.0',
    image_digest: 'sha256:policy-approval-gateway-dev-digest',
    oauth_scopes: ['internal:policy', 'internal:approval'],
    outbound_domains: [],
    allowed_environments: ['development', 'staging', 'production'],
    data_classification: 'restricted',
    tools: [
      { name: 'evaluate_policy', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'create_approval_request', capability: 'write', risk_level: 'high', requires_approval: false },
      { name: 'verify_grant', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'check_budget', capability: 'read', risk_level: 'low', requires_approval: false },
    ],
    safety: 'Internal authenticated service; exact-argument authorization',
  },
  {
    slug: 'audit-evidence-store',
    display_name: 'Audit/Evidence Store',
    category: 'compliance',
    rank: 10,
    description: 'Append audit records, retrieve evidence, attach artifact hashes.',
    owner_team: 'compliance',
    escalation_contact: 'compliance@localhost',
    trust_tier: 'production_critical',
    certification_state: 'certified',
    transport: 'streamable_http',
    version: '1.0.0',
    image_digest: 'sha256:audit-evidence-store-dev-digest',
    oauth_scopes: ['internal:audit:append', 'internal:audit:read'],
    outbound_domains: [],
    allowed_environments: ['development', 'staging', 'production'],
    data_classification: 'restricted',
    tools: [
      { name: 'append_event', capability: 'write', risk_level: 'medium', requires_approval: true },
      { name: 'get_evidence', capability: 'read', risk_level: 'low', requires_approval: false },
      { name: 'attach_artifact_hash', capability: 'write', risk_level: 'medium', requires_approval: true },
    ],
    safety: 'Append-only writes; signed/hash-linked audit records',
  },
  {
    slug: 'github-write',
    display_name: 'GitHub Write (non-prod PR create)',
    category: 'github',
    rank: 11,
    description: 'Create pull requests in allowlisted non-production repositories behind signed approval grants.',
    owner_team: 'platform-security',
    escalation_contact: 'secops@localhost',
    trust_tier: 'reviewed',
    certification_state: 'in_lab',
    transport: 'streamable_http',
    version: '1.0.0',
    image_digest: 'sha256:github-write-dev-digest',
    oauth_scopes: ['pull_requests:write', 'contents:read'],
    outbound_domains: ['api.github.com'],
    allowed_environments: ['development', 'staging'],
    data_classification: 'internal',
    tools: [
      {
        name: 'create_pull_request',
        capability: 'write',
        risk_level: 'high',
        requires_approval: true,
      },
    ],
    safety: 'Non-prod only; repo allowlist; signed grant; dry-run default',
  },
];

for (const c of connectors) {
  const tools = c.tools.map((t) => {
    const input_schema =
      c.slug === 'github-write' && t.name === 'create_pull_request'
        ? {
            type: 'object',
            additionalProperties: false,
            required: ['repository', 'head', 'base', 'title'],
            properties: {
              repository: { type: 'string' },
              head: { type: 'string' },
              base: { type: 'string' },
              title: { type: 'string' },
              body: { type: 'string' },
              draft: { type: 'boolean' },
            },
          }
        : {
            type: 'object',
            additionalProperties: false,
            properties: {
              correlation_id: { type: 'string' },
            },
          };
    return {
      ...t,
      description: `${t.name} for ${c.display_name}`,
      input_schema,
    };
  });
  const read = tools.filter((t) => t.capability === 'read').length;
  const write = tools.filter((t) => t.capability === 'write').length;
  const del = tools.filter((t) => t.capability === 'delete').length;
  const manifest = {
    ...c,
    tools,
    read_tool_count: read,
    write_tool_count: write,
    delete_tool_count: del,
    health: {
      success_rate_24h: 0.99,
      p95_latency_ms: 120,
      error_rate_24h: 0.01,
      policy_denial_rate_24h: 0.02,
      healthy: true,
      last_health_at: new Date().toISOString(),
    },
    active_in_production: ['github-readonly', 'git-repository', 'policy-approval-gateway', 'audit-evidence-store'].includes(
      c.slug,
    ),
  };
  fs.writeFileSync(path.join(dir, `${c.slug}.manifest.json`), `${JSON.stringify(manifest, null, 2)}\n`);

  // Signed registry.mcp manifest (YAML) for supply-chain activation checks
  const trustTier = {
    unverified: 0,
    sandboxed: 1,
    reviewed: 2,
    certified: 3,
    production_critical: 4,
  };
  const yamlTools = tools
    .map(
      (t) => `    - name: ${t.name}
      operation: ${t.capability}
      risk: ${t.risk_level}
      policy: ${c.slug}.${t.name}
${t.requires_approval ? '      approval: required\n' : ''}`,
    )
    .join('');
  const yaml = `apiVersion: registry.mcp.yourorg/v1
kind: MCPConnector
metadata:
  slug: ${c.slug}
  version: ${c.version}
  ownerTeam: ${c.owner_team}
  source:
    repository: https://github.com/your-org/mcp-${c.slug}
    commit: local-dev
  lifecycle: active
spec:
  transport:
    type: ${c.transport === 'stdio' ? 'stdio' : 'streamable-http'}
    endpoint: https://mcp-gateway.example.com/connectors/${c.slug}
  runtime:
    image: ghcr.io/your-org/mcp-${c.slug}@${c.image_digest}
    sbomUri: oci://ghcr.io/your-org/mcp-${c.slug}:sbom
    provenanceUri: oci://ghcr.io/your-org/mcp-${c.slug}:attestation
  trust:
    tier: ${trustTier[c.trust_tier] ?? 1}
    certification: ${c.certification_state}
    lastSecurityReviewAt: ${new Date().toISOString()}
  data:
    classifications: [${c.data_classification}]
    outboundDomains: [${c.outbound_domains.map((d) => d).join(', ')}]
    retention: none
  auth:
    mode: ${c.oauth_scopes.length ? 'oauth' : 'workload-identity'}
    scopes: [${c.oauth_scopes.join(', ')}]
    credentialSource: workload-identity
  tools:
${yamlTools}  limits:
    timeoutSeconds: 30
    maxCallsPerRun: 20
    maxCallsPerMinute: 60
    maxResponseBytes: 1048576
  environments: [${c.allowed_environments.join(', ')}]
  status:
    health: healthy
    activated: ${manifest.active_in_production}
`;
  fs.writeFileSync(path.join(dir, `${c.slug}.manifest.yaml`), yaml);
}

fs.writeFileSync(path.join(dir, 'index.json'), `${JSON.stringify({ version: '1.0.0', connectors: connectors.map((c) => c.slug) }, null, 2)}\n`);
console.log(`Wrote ${connectors.length} connector manifests`);
