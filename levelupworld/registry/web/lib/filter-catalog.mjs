/** Client-side catalog filters. Mirrors gateway query names so saved views stay shareable. */

const TRUST_RANK = {
  unverified: 1,
  sandboxed: 2,
  reviewed: 3,
  certified: 4,
  production_critical: 5,
};

function read(params, key) {
  if (!params) return '';
  if (typeof params.get === 'function') return params.get(key) || '';
  const value = params[key];
  return value == null ? '' : String(value);
}

function split(value) {
  return String(value || '')
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean);
}

function operationsOf(item) {
  const ops = [];
  if (item.read_tool_count) ops.push('read');
  if (item.write_tool_count) ops.push('write');
  if (item.delete_tool_count) ops.push('delete');
  if (item.external_tool_count) ops.push('external_communication');
  return ops;
}

function healthStatus(item) {
  return item.health?.status || (item.health?.healthy ? 'healthy' : 'unknown');
}

export function filterAndSort(items, params) {
  const q = read(params, 'q').trim().toLowerCase();
  const categories = split(read(params, 'category'));
  const operations = split(read(params, 'operation'));
  const tiers = split(read(params, 'trustTier') || read(params, 'trust_tier'));
  const environments = split(read(params, 'environment'));
  const health = split(read(params, 'health'));
  const transports = split(read(params, 'transport'));
  const classes = split(read(params, 'data_classification'));
  const certs = split(read(params, 'certification_state') || read(params, 'lifecycle'));
  const postures = split(read(params, 'posture'));
  const sort = read(params, 'sort') || 'rank';

  const tierRanks = new Set();
  const tierNames = new Set();
  for (const tier of tiers) {
    if (/^\d+$/.test(tier)) tierRanks.add(Number(tier));
    else tierNames.add(tier);
  }

  let out = items.filter((item) => {
    if (q) {
      const blob = [
        item.slug,
        item.display_name,
        item.description,
        item.owner_team,
        item.category,
        ...(item.tools || []).map((t) => t.name),
      ]
        .join(' ')
        .toLowerCase();
      if (!blob.includes(q)) return false;
    }
    if (categories.length && !categories.includes(item.category)) return false;
    if (operations.length) {
      const ops = operationsOf(item);
      if (!operations.some((op) => ops.includes(op))) return false;
      if (operations.length === 1 && operations[0] === 'read') {
        if (item.write_tool_count || item.delete_tool_count || item.external_tool_count) return false;
      }
    }
    if (tierRanks.size || tierNames.size) {
      const rank = TRUST_RANK[item.trust_tier] || 0;
      if (!tierRanks.has(rank) && !tierNames.has(item.trust_tier)) return false;
    }
    if (environments.length && !environments.some((env) => (item.allowed_environments || []).includes(env))) {
      return false;
    }
    if (health.length && !health.includes(healthStatus(item))) return false;
    if (transports.length && !transports.includes(item.transport)) return false;
    if (classes.length && !classes.includes(item.data_classification)) return false;
    if (certs.length && !certs.includes(item.certification_state)) return false;
    if (postures.length && !postures.includes(item.security?.posture)) return false;
    return true;
  });

  const desc = sort.startsWith('-');
  const key = sort.replace(/^-/, '');
  const valueOf = (item) => {
    if (key === 'name') return item.display_name.toLowerCase();
    if (key === 'activity_24h') return Number(item.health?.calls_24h || 0);
    if (key === 'success_rate_24h') return Number(item.health?.success_rate_24h || 0);
    if (key === 'p95_latency_ms' || key === 'p95_latency') return Number(item.health?.p95_latency_ms || 0);
    return Number(item.rank || 0);
  };
  out = [...out].sort((a, b) => {
    const av = valueOf(a);
    const bv = valueOf(b);
    if (av < bv) return desc ? 1 : -1;
    if (av > bv) return desc ? -1 : 1;
    return String(a.slug).localeCompare(String(b.slug));
  });
  return out;
}

export const SAVED_VIEWS = [
  { id: 'all', label: 'All connectors', query: '' },
  {
    id: 'certified-readonly-prod',
    label: 'Certified, read-only, production-active',
    query: 'operation=read&trustTier=4,5&environment=production&health=healthy,degraded',
  },
  {
    id: 'write-requires-approval',
    label: 'Write-capable connectors',
    query: 'operation=write,delete,external_communication',
  },
  { id: 'quarantined', label: 'Quarantined / revoked', query: 'certification_state=quarantined' },
  { id: 'cve-review', label: 'CVE or failed signature posture', query: 'posture=review_required,blocked' },
  { id: 'staging-candidates', label: 'Staging candidates', query: 'trustTier=2,3&environment=staging' },
];
