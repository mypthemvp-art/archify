/**
 * Rails for the Agents Window "Needs Attention" bucket.
 *
 * That bucket is a UI grouping (approvals, questions, pending plans, unread
 * finished work, blocked subagents). It is not a Cloud Agent API status.
 * These decisions use only documented run fields and hook payloads.
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const railsPath = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../../.cursor/needs-attention/rails.json',
);

const TASK_DENY = [
  { code: 'production_apply', re: /\b(kubectl\s+apply|helm\s+upgrade|terraform\s+apply)\b/i },
  { code: 'force_push', re: /\bgit\s+push\b[^\n]*--force\b/i },
  { code: 'production_apply', re: /\bcurl\b[^\n]*\|\s*(sh|bash)\b/i },
  { code: 'secret', re: /\b(print|reveal|dump)\b[^\n]{0,40}\b(secret|token|api[_ -]?key|private key)\b/i },
  { code: 'policy_bypass', re: /\b(ignore|disable|bypass)\b[^\n]{0,40}\b(hooks?|rails|policy|instructions)\b/i },
];

const STALL = [
  /\bneeds attention\b/i,
  /\bwaiting for (you|approval|the user|a human|subagent|allow)\b/i,
  /\bplease confirm\b/i,
  /\bshould i\b/i,
  /\bdo you want\b/i,
  /\blet me know\b/i,
  /\bpending plan\b/i,
  /\bclick allow\b/i,
  /\bblocked on\b/i,
];

const HUMAN_ONLY_TEXT = [
  { code: 'secret', re: /\b(secret|api[_ -]?key|private key|password|credential)\b/i },
  { code: 'production_apply', re: /\b(kubectl\s+apply|terraform\s+apply|helm\s+upgrade|production apply)\b/i },
  { code: 'external_message', re: /\b(send|post)\b[^\n]{0,24}\b(email|slack|message)\b/i },
  { code: 'payment', re: /\bpayment\b/i },
  { code: 'force_push', re: /\bforce[- ]?push\b/i },
  { code: 'mcp_auth', re: /\b(mcp auth|reconnect)\b/i },
  { code: 'environment_setup', re: /\benvironment setup\b/i },
  { code: 'delete', re: /\b(delete production|drop table)\b/i },
];

export const CONTINUE_FOLLOWUP =
  'Subagent finished by asking instead of deciding. Apply .cursor/needs-attention/rails.json. Do not ask the user. If the blocker is environment setup, MCP authentication, a secret, production apply, an external message, a payment, a delete, or a force-push, stop and name that blocker in one sentence. Otherwise continue the task.';

export const ERROR_FOLLOWUP =
  'The previous turn ended with an error. Continue from the last successful step. Do not ask the user. If you are blocked on environment setup, MCP authentication, a secret, production apply, an external message, a payment, a delete, or a force-push, stop and name that blocker in one sentence. Otherwise finish the task.';

export function loadRails(file = railsPath) {
  const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.subagentAllowlist)) {
    throw new Error('needs-attention rails.json is missing version 1 allowlist');
  }
  return parsed;
}

export function correlationId(prefix = 'needs-attention') {
  return `${prefix}-${crypto.randomUUID()}`;
}

function humanOnlyCode(text) {
  const source = String(text || '');
  for (const rule of HUMAN_ONLY_TEXT) {
    if (rule.re.test(source)) return rule.code;
  }
  return null;
}

function taskDenyCode(task) {
  const source = String(task || '');
  for (const rule of TASK_DENY) {
    if (rule.re.test(source)) return rule.code;
  }
  return null;
}

export function decideSubagentStart(event, rails = loadRails()) {
  const cid = correlationId();
  if (!event || typeof event !== 'object') {
    return {
      permission: 'deny',
      user_message: `[needs-attention rail] Unreadable subagent start; failing closed. (correlation_id=${cid})`,
    };
  }
  const type = String(event.subagent_type || '');
  const task = String(event.task || '');
  if (!type || !task.trim()) {
    return {
      permission: 'deny',
      user_message: `[needs-attention rail] Subagent type and task are required. (correlation_id=${cid})`,
    };
  }
  const denied = taskDenyCode(task);
  if (denied) {
    return {
      permission: 'deny',
      user_message: `[needs-attention rail] Denied subagent task (${denied}). (correlation_id=${cid})`,
    };
  }
  if (!rails.subagentAllowlist.includes(type)) {
    return {
      permission: 'deny',
      user_message: `[needs-attention rail] Subagent type "${type}" is not on the allowlist. (correlation_id=${cid})`,
    };
  }
  return { permission: 'allow' };
}

export function decideSubagentStop(event, rails = loadRails()) {
  if (!event || event.status !== 'completed') return {};
  const loopCount = Number(event.loop_count || 0);
  if (loopCount >= Number(rails.subagentLoopLimit || 3)) return {};
  const summary = String(event.summary || '');
  if (humanOnlyCode(`${event.task || ''}\n${summary}`)) return {};
  if (!STALL.some((re) => re.test(summary))) return {};
  return { followup_message: CONTINUE_FOLLOWUP };
}

export function decideAgentStop(event, rails = loadRails()) {
  if (!event || event.status !== 'error') return {};
  const loopCount = Number(event.loop_count || 0);
  if (loopCount >= Number(rails.errorRetries || 2)) return {};
  return { followup_message: ERROR_FOLLOWUP };
}

function ageMs(agent, now) {
  const stamp = agent.lastMessageActivityAtMs || agent.updatedAtMs || agent.createdAtMs || now;
  return Math.max(0, now - Number(stamp));
}

export function classifyAgent(agent, { events = [], now = Date.now(), rails = loadRails() } = {}) {
  const evidence = {
    bcId: agent?.bcId || null,
    url: agent?.url || null,
    status: agent?.status || null,
    setupStatus: agent?.setupStatus ?? null,
    source: agent?.source || null,
  };
  const base = { evidence, human_only: null, action: 'none' };
  if (!agent || typeof agent !== 'object') {
    return { ...base, disposition: 'ignore', reason: 'missing_agent' };
  }
  if (agent.isArchived || agent.isKilled || agent.status === 'ARCHIVED' || agent.status === 'EXPIRED') {
    return { ...base, disposition: 'ignore', reason: 'closed' };
  }
  if (agent.setupStatus === 'INSTALL_FAILED') {
    return {
      ...base,
      disposition: 'page_human',
      reason: 'environment_setup_failed',
      human_only: 'environment_setup',
      action: 'notify_slack',
    };
  }
  const kinds = new Set(events.map((event) => event?.kind).filter(Boolean));
  if (kinds.has('mcp_auth_error')) {
    return {
      ...base,
      disposition: 'page_human',
      reason: 'mcp_auth',
      human_only: 'mcp_auth',
      action: 'notify_slack',
    };
  }
  if (agent.status === 'ERROR') {
    return { ...base, disposition: 'continue', reason: 'run_error', action: 'followup_run' };
  }
  if (agent.status === 'WAITING_FOR_BACKGROUND_WORK') {
    return { ...base, disposition: 'watch', reason: 'background_work', action: 'subscribe_timer' };
  }
  if (agent.status === 'RUNNING' || agent.status === 'NOT_YET_STARTED') {
    if (ageMs(agent, now) > Number(rails.stallAfterMs)) {
      return { ...base, disposition: 'continue', reason: 'stalled_running', action: 'followup_run' };
    }
    return { ...base, disposition: 'watch', reason: 'in_progress', action: 'none' };
  }
  if (agent.status === 'IDLE') {
    if (agent.didCreatePullRequest) {
      return { ...base, disposition: 'ignore', reason: 'delivered_pr' };
    }
    if (!agent.didMakeCodeChanges && ageMs(agent, now) > Number(rails.unopenedAfterMs)) {
      return { ...base, disposition: 'continue', reason: 'idle_without_delivery', action: 'followup_run' };
    }
    return { ...base, disposition: 'watch', reason: 'idle_recent' };
  }
  return { ...base, disposition: 'watch', reason: 'unspecified' };
}

export function triageFleet({ agents = [], eventsById = {}, now = Date.now(), tenant = null, rails = loadRails() } = {}) {
  const correlation_id = correlationId();
  const results = agents.map((agent) => {
    const id = agent?.bcId;
    const classified = classifyAgent(agent, {
      events: id ? eventsById[id] || [] : [],
      now,
      rails,
    });
    return { ...classified, tenant: tenant || null };
  });
  return {
    correlation_id,
    tenant: tenant || null,
    tenant_missing: !tenant,
    mutate_blocked: !tenant,
    results,
  };
}
