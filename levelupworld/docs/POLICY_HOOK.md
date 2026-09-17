# Pre-tool policy hook

Project implementation: [`.cursor/hooks/policy-pre-tool.mjs`](../../.cursor/hooks/policy-pre-tool.mjs)  
Post-tool audit: [`.cursor/hooks/post-tool-audit-log.mjs`](../../.cursor/hooks/post-tool-audit-log.mjs)  
Wired from [`.cursor/hooks.json`](../../.cursor/hooks.json).

## Pseudocode (catalog baseline)

```ts
export async function beforeToolCall(ctx: ToolCallContext) {
  const risk = classifyToolRisk(ctx.tool.name, ctx.arguments);
  denyIfContainsSecret(ctx.arguments);
  denyIfOutsideTenantScope(ctx.identity, ctx.arguments);
  requireReadOnlyByDefault(ctx.tool);
  requireApprovalForMutation(ctx, risk);
  enforceBudget(ctx.runId, { maxTools: 20, maxDurationSeconds: 900 });
  return { allow: true, correlationId: crypto.randomUUID() };
}
```

## Runtime behavior

```text
on hook_event(event):
  cid ← event.correlation_id or new_uuid()
  deny if arguments embed raw secret-looking material
  deny if shell matches kubectl apply / helm upgrade / terraform apply / DROP / force-push / curl|sh ...
  deny absolute denylist tools (prod_shell, unrestricted_http, db_superuser, cloud_admin)
  if mutation-shaped tool or high risk:
      allow only with bound approval {token, args_hash, tenant, environment, idempotency_key, expires_at}
      otherwise ask
  ask if privileged prod database context is detected
  allow + return correlationId
```

## Approval binding

Valid approval objects require all of:

- `token`, `args_hash`, `tenant`, `environment`, `idempotency_key`, `expires_at` (future)

## Audit evidence

`post-tool-audit-log.mjs` appends JSONL records under `.cursor/audit/tool-events.jsonl` with:

`correlation_id`, `actor`, `tenant`, `tool`, `arguments_hash`, `approval_id`, `result_status`, `result_hash`, `evidence_uri`
