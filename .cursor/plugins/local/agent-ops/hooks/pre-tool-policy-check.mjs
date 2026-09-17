#!/usr/bin/env node
/**
 * LevelUpWorld / agent-ops pre-tool policy hook.
 *
 * Mirrors the catalog pseudocode:
 *   classify risk → deny secrets → tenant scope → read-only default →
 *   approval for mutation → enforce budget → emit correlation id
 */
import crypto from 'node:crypto';
import fs from 'node:fs';

const DENY_SHELL = [
  /\bkubectl\s+apply\b/i,
  /\bhelm\s+upgrade\b/i,
  /\bterraform\s+apply\b/i,
  /\bDROP\s+(TABLE|DATABASE)\b/i,
  /\bTRUNCATE\b/i,
  /\bgit\s+push\s+.*--force\b/i,
  /\brm\s+-rf\s+\/\b/,
  /\bcurl\b.*\|\s*(sh|bash)\b/i,
  /\baws\s+iam\b/i,
  /\bchmod\s+777\b/i,
];

const MUTATION_HINT =
  /^(apply_|rollback_|write_|delete_|deploy_|publish_|rotate_|message_|payment_)/i;

const DENY_TOOL_NAME = [
  /prod(?:uction)?_shell/i,
  /unrestricted_http/i,
  /db_superuser/i,
  /cloud_admin/i,
];

const SECRET_ARG =
  /(api[_-]?key|password|private[_-]?key|secret|token|connection[_-]?string)\s*[:=]\s*['\"]?[^'\"\s]{8,}/i;

function readInput() {
  try {
    return JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  } catch {
    return null;
  }
}

function correlationId(event) {
  return event?.correlationId || event?.conversation_id || event?.session_id || crypto.randomUUID();
}

function respond(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

function deny(message, cid) {
  respond({
    permission: 'deny',
    continue: false,
    user_message: `[agent-ops policy] ${message} (correlation_id=${cid})`,
  });
}

function ask(message, cid) {
  respond({
    permission: 'ask',
    user_message: `[agent-ops policy] ${message} (correlation_id=${cid})`,
  });
}

function allow(cid) {
  respond({ permission: 'allow', continue: true, correlationId: cid });
}

function hasBoundApproval(event) {
  const auth = event?.approval || event?.tool_input?.approval || event?.args?.approval;
  if (!auth || typeof auth !== 'object') return false;
  const required = ['token', 'args_hash', 'tenant', 'environment', 'idempotency_key', 'expires_at'];
  if (!required.every((k) => auth[k])) return false;
  if (Date.parse(auth.expires_at) < Date.now()) return false;
  return true;
}

function classifyToolRisk(toolName, command) {
  if (MUTATION_HINT.test(toolName) || DENY_SHELL.some((re) => re.test(command))) return 'high';
  if (/flag|issue|pr_create|comment|notify/i.test(toolName)) return 'medium';
  return 'low';
}

const event = readInput();
const cid = correlationId(event || {});

if (!event) {
  deny('Unable to parse hook input; failing closed.', cid);
  process.exit(0);
}

const command = String(event.command || event.shell_command || event.args?.command || '');
const toolName = String(event.tool_name || event.toolName || event.tool || event.mcp_tool || '');
const argsText = JSON.stringify(event.tool_input || event.args || {});

// denyIfContainsSecret
if (SECRET_ARG.test(argsText) || SECRET_ARG.test(command)) {
  deny('Refusing tool call that appears to embed raw secret material in arguments.', cid);
  process.exit(0);
}

// deny dangerous shell
for (const re of DENY_SHELL) {
  if (re.test(command)) {
    deny(`Blocked dangerous shell/pattern: ${re}`, cid);
    process.exit(0);
  }
}

// denylisted absolute tools
for (const re of DENY_TOOL_NAME) {
  if (toolName && re.test(toolName)) {
    deny(`Blocked denylisted tool: ${toolName}`, cid);
    process.exit(0);
  }
}

// requireApprovalForMutation / read-only by default
const risk = classifyToolRisk(toolName, command);
if (MUTATION_HINT.test(toolName) || risk === 'high') {
  if (hasBoundApproval(event)) {
    allow(cid);
    process.exit(0);
  }
  ask(
    `${toolName || 'mutation'} requires a bound human approval token (args hash, TTL, tenant, environment, idempotency key).`,
    cid,
  );
  process.exit(0);
}

// soft tenant / privileged DB guard
if (/connectionString.*(postgres|mysql).*prod/i.test(argsText) || /"role"\s*:\s*"(superuser|owner)"/i.test(argsText)) {
  ask('Privileged database context detected. Confirm read-replica / least-privilege credentials.', cid);
  process.exit(0);
}

// Budget enforcement is best-effort in-process; gateway owns hard caps.
allow(cid);
