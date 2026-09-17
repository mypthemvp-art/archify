#!/usr/bin/env node
/**
 * LevelUpWorld pre-tool / before-shell / before-MCP policy hook.
 *
 * Cursor sends one JSON object on stdin. We respond with JSON on stdout.
 * Fail closed on parse errors for mutate-shaped tools; otherwise allow with a warning.
 *
 * Mandatory checks:
 *   1. Parse event + tool/command
 *   2. Deny denylisted shell / MCP patterns
 *   3. Require approval token metadata for apply_/rollback_ tools
 *   4. Attach correlation ID advice in user_message when blocking
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

const DENY_TOOL_NAME = [
  /^apply_/i,
  /^rollback_/i,
  /prod(?:uction)?_shell/i,
  /unrestricted_http/i,
  /db_superuser/i,
  /cloud_admin/i,
];

const ALLOW_APPLY_IF_APPROVED = true;

function readInput() {
  try {
    return JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  } catch {
    return null;
  }
}

function correlationId(event) {
  return (
    event?.correlationId ||
    event?.conversation_id ||
    event?.session_id ||
    crypto.randomUUID()
  );
}

function deny(message, cid) {
  const payload = {
    permission: 'deny',
    continue: false,
    user_message: `[LevelUpWorld policy] ${message} (correlation_id=${cid})`,
  };
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

function ask(message, cid) {
  process.stdout.write(
    `${JSON.stringify({
      permission: 'ask',
      user_message: `[LevelUpWorld policy] ${message} (correlation_id=${cid})`,
    })}\n`,
  );
}

function allow() {
  process.stdout.write(`${JSON.stringify({ permission: 'allow', continue: true })}\n`);
}

function hasBoundApproval(event) {
  const auth = event?.approval || event?.tool_input?.approval || event?.args?.approval;
  if (!auth || typeof auth !== 'object') return false;
  const required = ['token', 'args_hash', 'tenant', 'environment', 'idempotency_key', 'expires_at'];
  if (!required.every((k) => auth[k])) return false;
  if (Date.parse(auth.expires_at) < Date.now()) return false;
  return true;
}

const event = readInput();
const cid = correlationId(event || {});

if (!event) {
  deny('Unable to parse hook input; failing closed for safety.', cid);
  process.exit(0);
}

const command = String(event.command || event.shell_command || event.args?.command || '');
const toolName = String(event.tool_name || event.toolName || event.tool || event.mcp_tool || '');
const combined = `${toolName} ${command}`;

for (const re of DENY_SHELL) {
  if (re.test(command) || re.test(combined)) {
    deny(`Blocked dangerous shell/pattern: ${re}`, cid);
    process.exit(0);
  }
}

for (const re of DENY_TOOL_NAME) {
  if (toolName && re.test(toolName)) {
    if (ALLOW_APPLY_IF_APPROVED && /^(apply_|rollback_)/i.test(toolName) && hasBoundApproval(event)) {
      allow();
      process.exit(0);
    }
    if (/^(apply_|rollback_)/i.test(toolName)) {
      ask(
        `${toolName} requires a bound human approval token (args hash, TTL, tenant, environment, idempotency key).`,
        cid,
      );
      process.exit(0);
    }
    deny(`Blocked denylisted tool: ${toolName}`, cid);
    process.exit(0);
  }
}

// Soft-ask on generic broad network or privileged DB hints in arguments
const argsText = JSON.stringify(event.tool_input || event.args || {});
if (/connectionString.*(postgres|mysql).*prod/i.test(argsText) || /role":"(superuser|owner)"/i.test(argsText)) {
  ask('Privileged database context detected. Confirm read-replica / least-privilege credentials.', cid);
  process.exit(0);
}

allow();
