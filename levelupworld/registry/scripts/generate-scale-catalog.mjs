#!/usr/bin/env node
/**
 * Deterministic 120-connector scale catalog for the Next.js virtualized table.
 * Does not add certified manifests — the gateway portfolio stays at 11.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'web/fixtures/scale-catalog.json');

const CATEGORIES = [
  'source_control',
  'workspace',
  'ci_cd',
  'documentation',
  'database',
  'analytics',
  'observability',
  'browser',
  'cloud',
  'kubernetes',
  'iac',
  'security',
  'compliance',
  'messaging',
  'product_analytics',
  'feature_flags',
  'financial',
];
const TIERS = ['unverified', 'sandboxed', 'reviewed', 'certified', 'production_critical'];
const OWNERS = ['platform-security', 'data-platform', 'sre', 'app-eng'];
const TRANSPORTS = ['stdio', 'streamable_http', 'sse_legacy', 'gateway_proxy'];
const CLASSES = ['public', 'internal', 'confidential', 'regulated', 'internal', 'confidential'];

function title(slug) {
  return slug
    .split('_')
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(' ');
}

const connectors = [];
for (let i = 0; i < 120; i += 1) {
  const category = CATEGORIES[i % CATEGORIES.length];
  const trust = TIERS[i % TIERS.length];
  const write = i % 7 === 0 ? 1 + (i % 2) : 0;
  const del = i % 19 === 0 ? 1 : 0;
  const external = i % 11 === 0 ? 1 : 0;
  const read = 2 + (i % 5);
  const healthCycle = ['healthy', 'healthy', 'healthy', 'degraded', 'failing', 'unknown'][i % 6];
  const cveCritical = i % 29 === 0 ? 1 : 0;
  const cveHigh = !cveCritical && i % 11 === 0 ? 1 : 0;
  const signed = i % 17 !== 0;
  const posture = cveCritical > 0 ? 'blocked' : cveHigh > 0 ? 'review_required' : signed ? 'ok' : 'unknown';
  const envs =
    i % 5 === 0
      ? ['development', 'staging', 'production']
      : i % 5 === 1
        ? ['staging']
        : ['development', 'staging'];

  const tools = [{ name: `list_${category}`, capability: 'read' }];
  if (write) tools.push({ name: `apply_${category}`, capability: 'write' });
  if (del) tools.push({ name: `delete_${category}_row`, capability: 'delete' });
  if (external) tools.push({ name: `notify_${category}`, capability: 'external_communication' });

  const item = {
    slug: `${category}-${String(i).padStart(3, '0')}`,
    display_name: `${title(category)} ${String(i).padStart(3, '0')}`,
    category,
    rank: i + 1,
    description: `Scale-catalog ${category} connector. Tools: ${tools.map((t) => t.name).join(', ')}.`,
    owner_team: OWNERS[i % OWNERS.length],
    escalation_contact: 'secops@localhost',
    trust_tier: trust,
    certification_state:
      i % 23 === 0 ? 'quarantined' : write ? 'reviewed' : trust === 'certified' || trust === 'production_critical' ? 'certified' : 'in_lab',
    transport: TRANSPORTS[i % TRANSPORTS.length],
    version: '1.0.0',
    image_digest: `sha256:scale-${category}-${String(i).padStart(3, '0')}`,
    allowed_environments: envs,
    data_classification: CLASSES[i % CLASSES.length],
    outbound_domains: [`${category}.internal`],
    read_tool_count: read,
    write_tool_count: write,
    delete_tool_count: del,
    external_tool_count: external,
    tools,
    health: {
      status: healthCycle,
      healthy: healthCycle === 'healthy',
      success_rate_24h: healthCycle === 'failing' ? 0.72 : healthCycle === 'degraded' ? 0.94 : 0.995,
      p95_latency_ms: 20 + (i % 40) * 5,
      calls_24h: (i * 37) % 8000,
    },
    security: {
      signed,
      sbom: signed,
      cve_critical: cveCritical,
      cve_high: cveHigh,
      posture,
    },
    active_in_production: envs.includes('production') && !write && healthCycle === 'healthy',
    synthetic: true,
  };

  if (i < 10) {
    item.category = i % 2 === 0 ? 'database' : 'observability';
    item.display_name = `${title(item.category)} RO ${String(i).padStart(3, '0')}`;
    item.slug = `${item.category}-ro-${String(i).padStart(3, '0')}`;
    item.trust_tier = i % 2 === 0 ? 'certified' : 'production_critical';
    item.certification_state = 'certified';
    item.read_tool_count = 4;
    item.write_tool_count = 0;
    item.delete_tool_count = 0;
    item.external_tool_count = 0;
    item.tools = [{ name: `list_${item.category}`, capability: 'read' }];
    item.allowed_environments = ['development', 'staging', 'production'];
    item.active_in_production = true;
    item.health = {
      status: i % 4 === 0 ? 'degraded' : 'healthy',
      healthy: i % 4 !== 0,
      success_rate_24h: 0.99,
      p95_latency_ms: 35,
      calls_24h: 4000 + i,
    };
    item.security = { signed: true, sbom: true, cve_critical: 0, cve_high: 0, posture: 'ok' };
    item.data_classification = 'confidential';
  }

  connectors.push(item);
}

const doc = {
  generated_at: '2026-09-18T00:00:00Z',
  purpose: 'Next.js virtualized catalog fixture. Not a certification source. Gateway enforces the certified portfolio.',
  count: connectors.length,
  connectors,
};

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, `${JSON.stringify(doc, null, 2)}\n`);
console.log(JSON.stringify({ ok: true, count: connectors.length, output: path.relative(path.resolve(root, '../..'), out) }));
