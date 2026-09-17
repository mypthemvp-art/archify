/**
 * Reference TypeScript preflight for MCP calls (documentation / future compile target).
 * Runtime project hooks use the .mjs implementations — Cursor hook payloads vary by release.
 *
 * Principle: send tool name + args_hash to the gateway; never treat the IDE as authz authority.
 */

export type HookEvent = {
  tool_name?: string;
  toolName?: string;
  mcp_tool?: string;
  tool_input?: Record<string, unknown>;
  args?: Record<string, unknown>;
  actor?: string;
  correlationId?: string;
  approval_grant?: string;
};

export type PreflightResult =
  | { permission: 'allow'; continue: true; correlationId: string }
  | { permission: 'deny'; continue: false; user_message: string }
  | { permission: 'ask'; user_message: string };

export async function preflightMcp(
  event: HookEvent,
  deps: {
    gatewayUrl?: string;
    fetchJson: (url: string, body: unknown) => Promise<{ status: number; body: any }>;
    hashArgs: (args: unknown) => string;
    uuid: () => string;
  },
): Promise<PreflightResult> {
  const cid = event.correlationId || deps.uuid();
  const tool = event.tool_name || event.toolName || event.mcp_tool || '';
  const args = event.tool_input || event.args || {};
  const argsHash = deps.hashArgs(args);

  if (!deps.gatewayUrl) {
    return {
      permission: 'ask',
      user_message: `[agent-ops] GATEWAY_URL unset; refusing to treat local hook as authority (args_hash=${argsHash.slice(0, 12)}…)`,
    };
  }

  const { status, body } = await deps.fetchJson(`${deps.gatewayUrl.replace(/\/$/, '')}/api/v1/policy/evaluate`, {
    actor: event.actor || 'cursor-agent',
    connector_slug: tool.split('__')[1] || 'unknown',
    tool_name: tool.split('__')[2] || tool,
    arguments: args,
    correlation_id: cid,
    approval_grant: event.approval_grant,
  });

  if (status >= 500) {
    return { permission: 'deny', continue: false, user_message: `[agent-ops] gateway unavailable (${cid})` };
  }
  if (body.decision === 'deny') {
    return { permission: 'deny', continue: false, user_message: `[agent-ops] ${body.reason} (${cid})` };
  }
  if (body.decision === 'require_approval') {
    return { permission: 'ask', user_message: `[agent-ops] approval grant required (${cid})` };
  }
  return { permission: 'allow', continue: true, correlationId: body.correlation_id || cid };
}
