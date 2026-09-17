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
assert.equal(catalog.automations[0].title, 'Repository architecture map');
assert.equal(catalog.automations[99].title, 'Multi-agent release commander');

const skills = [
  'levelupworld-catalog-router',
  ...catalog.plugins.map((p) => p.id),
];
for (const name of skills) {
  const skillPath = path.join(root, '.cursor/skills/levelupworld', name, 'SKILL.md');
  assert.ok(fs.existsSync(skillPath), `missing skill ${skillPath}`);
  const body = fs.readFileSync(skillPath, 'utf8');
  assert.match(body, new RegExp(`^name:\\s*${name}\\s*$`, 'm'));

  const agentOpsSkill = path.join(root, '.cursor/plugins/local/agent-ops/skills', name, 'SKILL.md');
  assert.ok(fs.existsSync(agentOpsSkill), `missing agent-ops skill ${agentOpsSkill}`);
}

const blueprints = fs
  .readdirSync(path.join(root, '.cursor/automations'))
  .filter((f) => /^a\d{3}-.+\.md$/.test(f));
assert.equal(blueprints.length, 100);

for (const required of [
  '.cursor/rules/levelupworld-agent-ops-safety.mdc',
  '.cursor/rules/levelupworld-secrets.mdc',
  '.cursor/rules/levelupworld-database.mdc',
  '.cursor/rules/levelupworld-infrastructure.mdc',
  '.cursor/hooks.json',
  '.cursor/hooks/policy-pre-tool.mjs',
  '.cursor/hooks/post-tool-audit-log.mjs',
  '.cursor/mcp.json',
  '.cursor/plugins/local/agent-ops/plugin.json',
]) {
  assert.ok(fs.existsSync(path.join(root, required)), `missing ${required}`);
}

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

const audit = path.join(root, '.cursor/hooks/post-tool-audit-log.mjs');
const auditRun = spawnSync(process.execPath, [audit], {
  input: JSON.stringify({ tool_name: 'search_docs', args: { q: 'x' } }),
  encoding: 'utf8',
  cwd: root,
});
assert.equal(auditRun.status, 0, auditRun.stderr);
assert.equal(JSON.parse(auditRun.stdout).continue, true);

console.log('levelupworld agent-ops contract checks passed');
