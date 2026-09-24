#!/usr/bin/env node
/**
 * Certification gate for connector manifests (CI).
 * Fails if YAML/JSON missing, digest empty, tools unlabeled, or write tools lack approval.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir = path.join(root, 'connectors');
const files = fs.readdirSync(dir).filter((f) => f.endsWith('.manifest.json'));

let failures = 0;
const requiredTop10 = [
  'github-readonly',
  'filesystem-sandbox',
  'git-repository',
  'cicd-observer',
  'docs-fetch-search',
  'postgres-readonly',
  'observability-reader',
  'browser-test-runner',
  'policy-approval-gateway',
  'audit-evidence-store',
];

const requiredSandboxedCategories = ['feature-flags-readonly'];

function fail(msg) {
  console.error(`FAIL: ${msg}`);
  failures += 1;
}

for (const slug of requiredTop10) {
  if (!files.includes(`${slug}.manifest.json`)) fail(`missing core connector ${slug}`);
  if (!fs.existsSync(path.join(dir, `${slug}.manifest.yaml`))) fail(`missing YAML for ${slug}`);
}

for (const slug of requiredSandboxedCategories) {
  if (!files.includes(`${slug}.manifest.json`)) fail(`missing sandboxed category connector ${slug}`);
  if (!fs.existsSync(path.join(dir, `${slug}.manifest.yaml`))) fail(`missing YAML for ${slug}`);
  const data = JSON.parse(fs.readFileSync(path.join(dir, `${slug}.manifest.json`), 'utf8'));
  if (data.trust_tier !== 'sandboxed') fail(`${slug}: trust_tier must be sandboxed for category onboarding`);
  if ((data.allowed_environments || []).includes('production')) {
    fail(`${slug}: sandboxed category must not allow production yet`);
  }
  for (const tool of data.tools || []) {
    if (tool.capability !== 'read') fail(`${slug}.${tool.name}: sandboxed onboarding is read-only`);
  }
}

for (const file of files) {
  const full = path.join(dir, file);
  const data = JSON.parse(fs.readFileSync(full, 'utf8'));
  const slug = data.slug;
  if (!data.version) fail(`${slug}: missing version`);
  if (!data.image_digest || !String(data.image_digest).startsWith('sha256:')) {
    fail(`${slug}: image_digest must be sha256:…`);
  }
  if (!data.owner_team || !data.escalation_contact) fail(`${slug}: owner/escalation required`);
  if (!Array.isArray(data.tools) || data.tools.length === 0) fail(`${slug}: tools required`);
  for (const tool of data.tools) {
    if (!['read', 'write', 'delete', 'external_communication'].includes(tool.capability)) {
      fail(`${slug}.${tool.name}: invalid capability`);
    }
    if (!tool.input_schema || tool.input_schema.type !== 'object') {
      fail(`${slug}.${tool.name}: input_schema object required`);
    }
    if (tool.capability !== 'read' && !tool.requires_approval) {
      // Control-plane connectors may perform gated internal writes without a human grant.
      if (!['policy-approval-gateway', 'audit-evidence-store'].includes(slug)) {
        fail(`${slug}.${tool.name}: non-read tools must require approval`);
      }
    }
  }
  if (data.certification_state === 'certified') {
    const yaml = fs.readFileSync(path.join(dir, `${slug}.manifest.yaml`), 'utf8');
    if (!yaml.includes(`slug: ${slug}`)) fail(`${slug}: YAML slug mismatch`);
    if (!yaml.includes('provenanceUri:') && !yaml.includes('provenance')) {
      // soft: warn only
      console.warn(`WARN: ${slug} YAML missing provenanceUri`);
    }
  }
  const hash = crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
  console.log(`OK ${slug}@${data.version} manifest_sha256=${hash.slice(0, 12)}… tools=${data.tools.length}`);
}

// github-write mutation connector must exist for weeks 5–6
const gw = path.join(dir, 'github-write.manifest.json');
if (!fs.existsSync(gw)) {
  fail('missing github-write.manifest.json (first constrained mutation)');
} else {
  const data = JSON.parse(fs.readFileSync(gw, 'utf8'));
  if ((data.allowed_environments || []).includes('production')) {
    fail('github-write must not allow production');
  }
  const tool = (data.tools || []).find((t) => t.name === 'create_pull_request');
  if (!tool || !tool.requires_approval || tool.capability !== 'write') {
    fail('github-write.create_pull_request must be write + approval required');
  }
}

if (failures) {
  console.error(`\nCertification gate failed with ${failures} issue(s).`);
  process.exit(1);
}
console.log(`\nCertification gate passed for ${files.length} connector manifests.`);
