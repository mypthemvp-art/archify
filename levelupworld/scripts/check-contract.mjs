#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'levelupworld/docs/catalog.json'), 'utf8'));

assert.equal(catalog.automations.length, 100);
assert.equal(catalog.plugins.length, 10);

const skills = [
  'levelupworld-catalog-router',
  'secure-pr-guardian',
  'mcp-security-gateway',
  'production-triage-copilot',
  'database-change-guardian',
  'gitops-release-controller',
  'compliance-evidence-engine',
];
for (const name of skills) {
  const skillPath = path.join(root, '.cursor/skills/levelupworld', name, 'SKILL.md');
  assert.ok(fs.existsSync(skillPath), `missing skill ${skillPath}`);
  const body = fs.readFileSync(skillPath, 'utf8');
  assert.match(body, new RegExp(`^name:\\s*${name}\\s*$`, 'm'));
}

const blueprints = fs
  .readdirSync(path.join(root, '.cursor/automations'))
  .filter((f) => /^a\d{3}-.+\.md$/.test(f));
assert.equal(blueprints.length, 100);

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

console.log('levelupworld contract checks passed');
