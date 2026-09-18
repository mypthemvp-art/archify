#!/usr/bin/env node
/**
 * Spec alias: afterShellExecution secret scan.
 * Scans output indicators without storing raw secrets; fail-open for postflight.
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

function readInput() {
  try {
    return JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  } catch {
    return {};
  }
}

const SECRET_HINT =
  /\b(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)\b/;

const event = readInput();
const output = String(event.result || event.output || event.stdout || '');
const cid = event.correlationId || crypto.randomUUID();
const hit = SECRET_HINT.test(output);

const record = {
  ts: new Date().toISOString(),
  correlation_id: cid,
  hook: 'secret-scan-output',
  secret_indicator: hit,
  output_hash: output
    ? crypto.createHash('sha256').update(output).digest('hex')
    : null,
};

const dir = path.join(process.cwd(), '.cursor', 'audit');
fs.mkdirSync(dir, { recursive: true });
fs.appendFileSync(path.join(dir, 'tool-events.jsonl'), `${JSON.stringify(record)}\n`);

// Postflight: never block; surface advisory in user_message when possible
if (hit) {
  process.stdout.write(
    `${JSON.stringify({
      continue: true,
      user_message: `[agent-ops] Secret-like material detected in command output (correlation_id=${cid}). Rotate if real.`,
    })}\n`,
  );
} else {
  process.stdout.write(`${JSON.stringify({ continue: true })}\n`);
}
