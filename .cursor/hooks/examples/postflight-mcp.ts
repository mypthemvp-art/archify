/**
 * Reference TypeScript postflight for MCP calls — emit audit completion, never store raw secrets.
 */

export type PostflightEvent = {
  correlationId?: string;
  tool_name?: string;
  tool_input?: unknown;
  result?: unknown;
  error?: unknown;
};

export function postflightMcp(
  event: PostflightEvent,
  deps: { hash: (v: unknown) => string; appendAudit: (row: object) => void; uuid: () => string },
): { continue: true } {
  const cid = event.correlationId || deps.uuid();
  deps.appendAudit({
    ts: new Date().toISOString(),
    correlation_id: cid,
    tool: event.tool_name || 'unknown',
    arguments_hash: deps.hash(event.tool_input || {}),
    result_hash: event.result != null ? deps.hash(event.result) : null,
    result_status: event.error ? 'error' : 'ok',
  });
  return { continue: true };
}
