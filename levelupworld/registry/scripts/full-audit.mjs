#!/usr/bin/env node
/**
 * Full registry audit before any ship.
 * Runs certification, hook proof, catalog stress, gateway tests, and live stress.
 * Prints one JSON receipt. Exits non-zero if any gate fails.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const registryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = path.resolve(registryRoot, '../..');
const venvPy = path.join(registryRoot, 'gateway/.venv/bin/python');
const py = fs.existsSync(venvPy) ? venvPy : 'python3';
const pyEnv = {
  AUTH_MODE: 'disabled',
  GITHUB_WRITE_DRY_RUN: '1',
  PYTHONPATH: path.join(registryRoot, 'gateway'),
};

const steps = [
  ['certify-connectors', 'node', ['levelupworld/registry/scripts/certify-connectors.mjs']],
  ['ingest-supply-chain', 'node', ['levelupworld/registry/scripts/ingest-supply-chain.mjs']],
  ['catalog-window', 'node', ['levelupworld/registry/scripts/test-catalog-window.mjs']],
  ['catalog-stress', 'node', ['levelupworld/registry/scripts/stress-catalog.mjs']],
  ['ephemeral-lab', 'node', ['levelupworld/registry/scripts/ephemeral-lab-runner.mjs', 'github-readonly', 'full']],
  ['contract', 'node', ['levelupworld/scripts/check-contract.mjs']],
  ['hooks-bypass', 'node', ['levelupworld/scripts/prove-hooks-fail-closed.mjs']],
  ['pytest', py, ['-m', 'pytest', '-q', 'levelupworld/registry/gateway/tests'], pyEnv],
  ['gateway-stress', py, ['levelupworld/registry/scripts/stress-gateway.py'], pyEnv],
];

const results = [];
let failed = false;
for (const [name, cmd, args, extraEnv] of steps) {
  const started = Date.now();
  const result = spawnSync(cmd, args, {
    cwd: repoRoot,
    encoding: 'utf8',
    env: { ...process.env, ...(extraEnv || {}) },
  });
  const ok = result.status === 0;
  if (!ok) failed = true;
  const tail = `${result.stdout || ''}${result.stderr || ''}`.trim().split('\n').slice(-3).join(' | ');
  results.push({ name, ok, ms: Date.now() - started, tail });
  console.error(`${ok ? 'PASS' : 'FAIL'} ${name} (${Date.now() - started}ms)`);
  if (!ok) console.error(result.stderr || result.stdout);
}

const receipt = {
  ok: !failed,
  audited_at: new Date().toISOString(),
  commit: process.env.AUDIT_COMMIT || null,
  gates: results,
};
console.log(JSON.stringify(receipt));
process.exit(failed ? 1 : 0);
