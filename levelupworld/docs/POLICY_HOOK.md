# Pre-tool policy hook (pseudocode)

Project implementation: [`.cursor/hooks/policy-pre-tool.mjs`](../../.cursor/hooks/policy-pre-tool.mjs)  
Wired from [`.cursor/hooks.json`](../../.cursor/hooks.json) on `preToolUse`, `beforeShellExecution`, `beforeMCPExecution`, and `beforeSubmitPrompt`.

```text
on hook_event(event):
  cid ← event.correlation_id or new_uuid()

  if event.command matches DENY_SHELL_PATTERNS:
      return deny("dangerous shell", cid)
      # examples: kubectl apply, helm upgrade, terraform apply,
      #           DROP/TRUNCATE, force-push, curl|sh, aws iam

  if event.tool_name matches DENY_TOOL_NAMES:
      if tool is apply_* or rollback_*:
          if has_bound_approval(event.approval):
              # token, args_hash, tenant, environment,
              # idempotency_key, expires_at (not expired)
              return allow()
          else:
              return ask("approval required", cid)
      else:
          return deny("denylisted tool", cid)

  if args suggest privileged prod database:
      return ask("confirm least-privilege / replica", cid)

  return allow()
```

## Approval binding

An approval object is valid only when all fields are present and `expires_at` is in the future:

- `token` — short-lived human approval token
- `args_hash` — hash of the exact tool arguments
- `tenant` — tenant binding
- `environment` — e.g. `staging` / `production`
- `idempotency_key` — dedupe key for the mutation
- `expires_at` — ISO-8601 expiry

## Design intent

Hooks are the last line of defense inside the agent loop. They complement MCP Security Gateway allowlists and Cursor Rules; they do not replace them.
