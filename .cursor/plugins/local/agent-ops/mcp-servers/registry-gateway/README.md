# Registry Gateway MCP proxy

Forwards Cursor MCP tool calls to the Agent-Ops registry/gateway HTTP API.

```bash
export AGENT_OPS_GATEWAY_URL=http://127.0.0.1:8787
node proxy.mjs
```

Prefer terminating MCP at the gateway in production. This proxy exists so local Cursor projects can discover registry/policy tools during Weeks 3–7 of the build sequence.
