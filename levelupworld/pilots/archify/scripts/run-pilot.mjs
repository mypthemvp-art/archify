#!/usr/bin/env node
/**
 * Orchestrate both Weeks 7–8 pilot runners.
 */
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));

function run(script) {
  const r = spawnSync(process.execPath, [path.join(here, script)], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    env: process.env,
  });
  if (r.stdout) process.stdout.write(r.stdout);
  if (r.stderr) process.stderr.write(r.stderr);
  if (r.status !== 0) {
    console.error(`Pilot runner failed: ${script}`);
    process.exit(r.status || 1);
  }
  return JSON.parse(r.stdout.trim().split('\n').filter(Boolean).at(-1) || '{}');
}

const pr = run('run-secure-pr-guardian.mjs');
const triage = run('run-production-triage.mjs');
console.log(
  JSON.stringify({
    ok: true,
    pilot: 'archify-weeks-7-8',
    secure_pr_guardian: pr,
    production_triage_copilot: triage,
  }),
);
