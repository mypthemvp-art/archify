#!/usr/bin/env node
/**
 * Classify a cloud-agent fleet snapshot.
 * stdin: { tenant, now, agents, eventsById }
 * stdout: triage JSON. Read-only. Does not resume agents.
 */
import fs from 'node:fs';
import { triageFleet } from './lib/needs-attention-rails.mjs';

let input;
try {
  input = JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
} catch {
  process.stderr.write('needs-attention triage: stdin must be JSON\n');
  process.exit(1);
}

const now = typeof input.now === 'number' ? input.now : Date.parse(input.now || '') || Date.now();
const report = triageFleet({
  agents: Array.isArray(input.agents) ? input.agents : [],
  eventsById: input.eventsById && typeof input.eventsById === 'object' ? input.eventsById : {},
  now,
  tenant: typeof input.tenant === 'string' && input.tenant.trim() ? input.tenant.trim() : null,
});
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
