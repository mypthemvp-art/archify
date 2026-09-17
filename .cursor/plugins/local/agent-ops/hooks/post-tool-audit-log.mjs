#!/usr/bin/env node
/**
 * Post-tool audit log hook. Appends a structured JSONL event for evidence.
 * Never stores raw secrets; hashes argument payloads.
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

const event = readInput();
const cid =
  event.correlationId || event.conversation_id || event.session_id || crypto.randomUUID();
const tool = event.tool_name || event.toolName || event.tool || event.mcp_tool || event.command || 'unknown';
const args = event.tool_input || event.args || {};
const argsHash = crypto.createHash('sha256').update(JSON.stringify(args)).digest('hex');
const result = event.result || event.output || event.error || null;
const resultHash = result
  ? crypto.createHash('sha256').update(typeof result === 'string' ? result : JSON.stringify(result)).digest('hex')
  : null;

const record = {
  ts: new Date().toISOString(),
  correlation_id: cid,
  actor: event.actor || event.user || 'cursor-agent',
  tenant: event.tenant || args.tenant || null,
  tool,
  arguments_hash: argsHash,
  approval_id: event.approval?.token || event.approval_id || null,
  result_status: event.error ? 'error' : 'ok',
  result_hash: resultHash,
  evidence_uri: event.evidence_uri || null,
};

const dir = path.resolve('.cursor/audit');
fs.mkdirSync(dir, { recursive: true });
fs.appendFileSync(path.join(dir, 'tool-events.jsonl'), `${JSON.stringify(record)}\n`);

process.stdout.write(`${JSON.stringify({ continue: true, correlationId: cid })}\n`);
