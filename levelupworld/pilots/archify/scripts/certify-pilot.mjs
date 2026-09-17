#!/usr/bin/env node
/**
 * Certify the Weeks 7–8 pilot before expanding to more plugins.
 */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const pilotRoot = path.resolve(here, '..');
const repoRoot = path.resolve(pilotRoot, '../../..');
const manifest = JSON.parse(fs.readFileSync(path.join(pilotRoot, 'pilot.manifest.json'), 'utf8'));
const schema = JSON.parse(fs.readFileSync(path.join(pilotRoot, 'evidence', 'schema.json'), 'utf8'));

let failures = 0;
function fail(msg) {
  console.error(`FAIL: ${msg}`);
  failures += 1;
}
function ok(msg) {
  console.log(`OK: ${msg}`);
}

// 1) Pilot exit automations have blueprints
for (const plugin of manifest.plugins) {
  for (const id of plugin.pilot_exit_automations) {
    const files = fs
      .readdirSync(path.join(repoRoot, '.cursor/automations'))
      .filter((f) => f.startsWith(`${id.toLowerCase()}-`) && f.endsWith('.md'));
    if (!files.length) fail(`missing blueprint for ${id}`);
    else ok(`blueprint ${id} → ${files[0]}`);
  }
  const skill = path.join(repoRoot, `.cursor/skills/levelupworld/${plugin.id}/SKILL.md`);
  if (!fs.existsSync(skill)) fail(`missing skill ${skill}`);
  else ok(`skill ${plugin.id}`);
}

// 2) Pilot MCP config must not register mutate connectors
const mcpPilot = path.join(repoRoot, '.cursor/mcp.pilot.json');
if (!fs.existsSync(mcpPilot)) fail('missing .cursor/mcp.pilot.json');
else {
  const mcp = JSON.parse(fs.readFileSync(mcpPilot, 'utf8'));
  const names = Object.keys(mcp.mcpServers || {});
  for (const denied of ['github-write', 'kubectl', 'terraform', 'prod-shell']) {
    if (names.some((n) => n.toLowerCase().includes(denied))) {
      fail(`pilot MCP registers denied server hint: ${denied}`);
    }
  }
  if (!names.includes('agent-ops-gateway')) fail('pilot MCP must include agent-ops-gateway');
  else ok(`pilot MCP servers: ${names.join(', ')}`);
}

// 3) Plugin mcp.json files stay empty or read-only (no write servers)
for (const plugin of ['secure-pr-guardian', 'production-triage-copilot']) {
  const mcpPath = path.join(repoRoot, `levelupworld/plugins/${plugin}/mcp.json`);
  const mcp = JSON.parse(fs.readFileSync(mcpPath, 'utf8'));
  const servers = mcp.mcpServers || {};
  for (const [name, cfg] of Object.entries(servers)) {
    const blob = JSON.stringify(cfg).toLowerCase();
    if (blob.includes('github-write') || name.includes('write')) {
      fail(`${plugin} mcp.json must not enable write connectors`);
    }
  }
  ok(`${plugin} mcp.json mutation-free (${Object.keys(servers).length} servers)`);
}

// 4) Denied connectors never in allowlist
for (const d of manifest.connectors_denied) {
  if (manifest.connectors_allowed.includes(d)) fail(`denied connector ${d} also allowed`);
}
ok('connector allow/deny disjoint');

// 5) Policy hook still fail-closed for mutations / denylist
function runHook(input) {
  const r = spawnSync(process.execPath, [path.join(repoRoot, '.cursor/hooks/policy-pre-tool.mjs')], {
    input: JSON.stringify(input),
    encoding: 'utf8',
  });
  assert.equal(r.status, 0, r.stderr);
  return JSON.parse(r.stdout);
}
assert.equal(runHook({ command: 'kubectl apply -f x' }).permission, 'deny');
assert.equal(runHook({ tool_name: 'apply_migration' }).permission, 'ask');
assert.equal(runHook({ tool_name: 'search_docs' }).permission, 'allow');
ok('policy hook deny/ask/allow');

// 6) Run pilots and validate evidence schema (required fields)
function runRunner(script) {
  const r = spawnSync(process.execPath, [path.join(here, script)], {
    encoding: 'utf8',
    env: { ...process.env, PILOT_ENV: 'development' },
  });
  if (r.status !== 0) {
    fail(`${script} exited ${r.status}: ${r.stderr}`);
    return null;
  }
  const text = r.stdout.trim();
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end < start) {
    fail(`${script} produced no JSON summary`);
    return null;
  }
  return JSON.parse(text.slice(start, end + 1));
}

const pr = runRunner('run-secure-pr-guardian.mjs');
const triage = runRunner('run-production-triage.mjs');
if (pr?.evidence_json) {
  const bundle = JSON.parse(fs.readFileSync(path.join(repoRoot, pr.evidence_json), 'utf8'));
  for (const key of schema.required) {
    if (!(key in bundle)) fail(`PR evidence missing ${key}`);
  }
  if (bundle.mutation !== 'none') fail('PR evidence mutation must be none');
  if (!['A003', 'A004', 'A021'].every((a) => bundle.automations.includes(a))) {
    fail('PR evidence missing exit automations');
  }
  ok(`secure-pr-guardian evidence ${pr.evidence_json} status=${bundle.result_status}`);
}
if (triage?.evidence_json) {
  const bundle = JSON.parse(fs.readFileSync(path.join(repoRoot, triage.evidence_json), 'utf8'));
  for (const key of schema.required) {
    if (!(key in bundle)) fail(`triage evidence missing ${key}`);
  }
  if (bundle.mutation !== 'none') fail('triage evidence mutation must be none');
  if (!bundle.timeline?.length) fail('triage evidence missing timeline');
  if (!bundle.hypotheses?.length) fail('triage evidence missing hypotheses');
  ok(`production-triage-copilot evidence ${triage.evidence_json} status=${bundle.result_status}`);
}

// 7) Cursor pilot rule present
const rule = path.join(repoRoot, '.cursor/rules/pilot-secure-pr-and-triage.mdc');
if (!fs.existsSync(rule)) fail('missing pilot rule');
else ok('pilot Cursor rule present');

// 8) Definition of done checklist documented
const certDoc = path.join(pilotRoot, 'CERTIFICATION.md');
if (!fs.existsSync(certDoc)) fail('missing pilot CERTIFICATION.md');
else ok('pilot CERTIFICATION.md present');

if (failures) {
  console.error(`\nPilot certification failed with ${failures} issue(s). Do not expand plugins.`);
  process.exit(1);
}
console.log('\nPilot certification PASSED — Secure PR Guardian + Production Triage Copilot ready for controlled expansion.');
