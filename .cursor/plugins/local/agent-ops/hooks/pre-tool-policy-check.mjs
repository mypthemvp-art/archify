#!/usr/bin/env node
/**
 * LevelUpWorld / agent-ops pre-tool policy hook.
 *
 * Local denylist first, then optional server-side gateway preflight when
 * AGENT_OPS_GATEWAY_URL is set (control plane authority).
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import https from 'node:https';
import { URL } from 'node:url';

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

const DENY_TOOL_NAME = [/prod(?:uction)?_shell/i, /unrestricted_http/i, /db_superuser/i, /cloud_admin/i];

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

function postJson(urlString, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlString);
    const lib = url.protocol === 'https:' ? https : http;
    const data = JSON.stringify(body);
    const req = lib.request(
      {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname + url.search,
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'content-length': Buffer.byteLength(data),
        },
        timeout: 2500,
      },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          try {
            resolve({ status: res.statusCode || 0, body: JSON.parse(text || '{}') });
          } catch {
            resolve({ status: res.statusCode || 0, body: { raw: text } });
          }
        });
      },
    );
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('gateway timeout'));
    });
    req.write(data);
    req.end();
  });
}

function hasBoundApproval(event) {
  const auth = event?.approval || event?.tool_input?.approval || event?.args?.approval;
  if (!auth || typeof auth !== 'object') return false;
  const required = ['token', 'args_hash', 'tenant', 'environment', 'idempotency_key', 'expires_at'];
  if (!required.every((k) => auth[k])) return false;
  if (Date.parse(auth.expires_at) < Date.now()) return false;
  return true;
}

function parseConnectorTool(toolName) {
  // Prefer mcp__connector__tool or connector.tool shapes
  const mcp = /^mcp__([^_]+)__(.+)$/i.exec(toolName);
  if (mcp) return { connector_slug: mcp[1], tool_name: mcp[2] };
  const dotted = /^([a-z0-9-]+)\.([a-z0-9_]+)$/i.exec(toolName);
  if (dotted) return { connector_slug: dotted[1], tool_name: dotted[2] };
  return null;
}

async function main() {
  const event = readInput();
  const cid = correlationId(event || {});
  if (!event) {
    deny('Unable to parse hook input; failing closed.', cid);
    return;
  }

  const command = String(event.command || event.shell_command || event.args?.command || '');
  const toolName = String(event.tool_name || event.toolName || event.tool || event.mcp_tool || '');
  const args = event.tool_input || event.args || {};
  const argsText = JSON.stringify(args);

  if (SECRET_ARG.test(argsText) || SECRET_ARG.test(command)) {
    deny('Refusing tool call that appears to embed raw secret material in arguments.', cid);
    return;
  }
  for (const re of DENY_SHELL) {
    if (re.test(command)) {
      deny(`Blocked dangerous shell/pattern: ${re}`, cid);
      return;
    }
  }
  for (const re of DENY_TOOL_NAME) {
    if (toolName && re.test(toolName)) {
      deny(`Blocked denylisted tool: ${toolName}`, cid);
      return;
    }
  }

  const gateway = process.env.AGENT_OPS_GATEWAY_URL;
  const parsed = parseConnectorTool(toolName);
  if (gateway && parsed) {
    try {
      const { status, body } = await postJson(`${gateway.replace(/\/$/, '')}/api/v1/policy/evaluate`, {
        actor: event.actor || event.user || 'cursor-agent',
        org_id: process.env.AGENT_OPS_ORG_ID || 'org_local',
        tenant_id: process.env.AGENT_OPS_TENANT_ID || 'tenant_local',
        project_id: process.env.AGENT_OPS_PROJECT_ID || 'project_local',
        environment: process.env.AGENT_OPS_ENVIRONMENT || 'development',
        connector_slug: parsed.connector_slug,
        tool_name: parsed.tool_name,
        arguments: args,
        correlation_id: cid,
        idempotency_key: event.idempotency_key || args.idempotency_key || null,
        approval_grant: event.approval_grant || args.approval_grant || null,
      });
      if (status >= 500) {
        deny('Gateway unavailable; failing closed for MCP tool preflight.', cid);
        return;
      }
      const decision = body.decision;
      if (decision === 'deny') {
        deny(body.reason || 'gateway deny', body.correlation_id || cid);
        return;
      }
      if (decision === 'require_approval') {
        ask(body.reason || 'gateway requires approval grant', body.correlation_id || cid);
        return;
      }
      allow(body.correlation_id || cid);
      return;
    } catch {
      // Fail closed for identifiable MCP tools when gateway is configured but unreachable.
      deny('Gateway unreachable; failing closed for MCP tool preflight.', cid);
      return;
    }
  }

  if (MUTATION_HINT.test(toolName)) {
    if (hasBoundApproval(event)) {
      allow(cid);
      return;
    }
    ask(
      `${toolName || 'mutation'} requires a bound human approval token (args hash, TTL, tenant, environment, idempotency key).`,
      cid,
    );
    return;
  }

  if (/connectionString.*(postgres|mysql).*prod/i.test(argsText) || /"role"\s*:\s*"(superuser|owner)"/i.test(argsText)) {
    ask('Privileged database context detected. Confirm read-replica / least-privilege credentials.', cid);
    return;
  }

  allow(cid);
}

await main();
