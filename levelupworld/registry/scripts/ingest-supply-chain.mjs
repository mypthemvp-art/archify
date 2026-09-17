#!/usr/bin/env node
/**
 * Ingest SBOM / signature / CVE posture for connector versions (Milestone 2).
 *
 * Reads:
 *   - connectors/*.manifest.json
 *   - optional supply-chain/feed.json (overrides / live scanner output)
 *
 * Writes:
 *   - connectors/supply-chain-index.json
 *
 * Feed schema (optional):
 * {
 *   "connectors": {
 *     "github-readonly": {
 *       "cve_critical": 0, "cve_high": 1, "signed": true,
 *       "sbom_uri": "...", "signature_uri": "...", "last_scanned_at": "..."
 *     }
 *   }
 * }
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const registryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const connectorsDir = path.join(registryRoot, 'connectors');
const feedPath = path.join(registryRoot, 'supply-chain', 'feed.json');
const outPath = path.join(connectorsDir, 'supply-chain-index.json');

const manifests = fs
  .readdirSync(connectorsDir)
  .filter((f) => f.endsWith('.manifest.json'));

let feed = { connectors: {} };
if (fs.existsSync(feedPath)) {
  feed = JSON.parse(fs.readFileSync(feedPath, 'utf8'));
}

const index = {
  generated_at: new Date().toISOString(),
  feed_present: fs.existsSync(feedPath),
  connectors: {},
};

for (const file of manifests) {
  const data = JSON.parse(fs.readFileSync(path.join(connectorsDir, file), 'utf8'));
  const slug = data.slug;
  const override = (feed.connectors || {})[slug] || {};
  const digest = data.image_digest || '';
  const signed = Boolean(override.signed ?? (digest && String(digest).startsWith('sha256:')));
  const sbomUri =
    override.sbom_uri || `oci://ghcr.io/your-org/mcp-${slug}:sbom`;
  const signatureUri =
    override.signature_uri || `oci://ghcr.io/your-org/mcp-${slug}:attestation`;
  const cveCritical = Number(override.cve_critical ?? 0);
  const cveHigh = Number(override.cve_high ?? 0);
  const posture =
    cveCritical > 0 ? 'blocked' : cveHigh > 0 ? 'review_required' : signed ? 'ok' : 'unknown';

  const record = {
    slug,
    version: data.version,
    image_digest: digest,
    signed,
    sbom_uri: sbomUri,
    signature_uri: signatureUri,
    provenance_uri: override.provenance_uri || signatureUri,
    cve_critical: cveCritical,
    cve_high: cveHigh,
    posture,
    last_scanned_at: override.last_scanned_at || new Date().toISOString(),
    source: override.source || (fs.existsSync(feedPath) ? 'feed' : 'manifest-inferred'),
  };
  record.record_sha256 = crypto.createHash('sha256').update(JSON.stringify(record)).digest('hex');
  index.connectors[slug] = record;
}

fs.writeFileSync(outPath, `${JSON.stringify(index, null, 2)}\n`);
console.log(
  JSON.stringify({
    ok: true,
    connectors: Object.keys(index.connectors).length,
    output: path.relative(path.resolve(registryRoot, '../..'), outPath),
    blocked: Object.values(index.connectors).filter((c) => c.posture === 'blocked').map((c) => c.slug),
    review_required: Object.values(index.connectors)
      .filter((c) => c.posture === 'review_required')
      .map((c) => c.slug),
  }),
);
