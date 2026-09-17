#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'levelupworld/docs/catalog.json'), 'utf8'));

assert.equal(catalog.version, '2.0.0');
assert.equal(catalog.automations.length, 100);
assert.equal(catalog.plugins.length, 12);

const skills = ['levelupworld-catalog-router', ...catalog.plugins.map((p) => p.id)];
for (const name of skills) {
  const skillPath = path.join(root, '.cursor/skills/levelupworld', name, 'SKILL.md');
  assert.ok(fs.existsSync(skillPath), `missing skill ${skillPath}`);
}

const blueprints = fs
  .readdirSync(path.join(root, '.cursor/automations'))
  .filter((f) => /^a\d{3}-.+\.md$/.test(f));
assert.equal(blueprints.length, 100);

for (const required of [
  'levelupworld/registry/README.md',
  'levelupworld/registry/docs/BLUEPRINT.md',
  'levelupworld/registry/docs/BUILD-SEQUENCE.md',
  'levelupworld/registry/docs/APPROVAL-TOKENS.md',
  'levelupworld/registry/schema/001_init.sql',
  'levelupworld/registry/gateway/app/main.py',
  'levelupworld/registry/connectors/index.json',
  'levelupworld/registry/connectors/github-readonly.manifest.json',
  '.cursor/plugins/local/agent-ops/mcp-servers/registry-gateway/proxy.mjs',
  '.cursor/hooks/policy-pre-tool.mjs',
  '.cursor/hooks/post-tool-audit-log.mjs',
]) {
  assert.ok(fs.existsSync(path.join(root, required)), `missing ${required}`);
}

const manifests = fs
  .readdirSync(path.join(root, 'levelupworld/registry/connectors'))
  .filter((f) => f.endsWith('.manifest.json'));
assert.equal(manifests.length, 10);

const policy = path.join(root, '.cursor/hooks/policy-pre-tool.mjs');
function run(input) {
  const result = spawnSync(process.execPath, [policy], {
    input: JSON.stringify(input),
    encoding: 'utf8',
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

assert.equal(run({ command: 'kubectl apply -f x' }).permission, 'deny');
assert.equal(run({ tool_name: 'search_docs' }).permission, 'allow');
assert.equal(run({ tool_name: 'apply_x' }).permission, 'ask');
assert.equal(
  run({
    tool_name: 'apply_x',
    approval: {
      token: 't',
      args_hash: 'h',
      tenant: 'a',
      environment: 'staging',
      idempotency_key: 'k',
      expires_at: '2099-01-01T00:00:00Z',
    },
  }).permission,
  'allow',
);

console.log('levelupworld agent-ops + registry contract checks passed');
