# Registry gateway MCP server

Prefer **Streamable HTTP termination on the gateway** itself:

```json
{
  "mcpServers": {
    "org-mcp-gateway": {
      "url": "http://127.0.0.1:8787/mcp",
      "headers": {
        "X-Project-ID": "agent-platform",
        "X-Requested-Environment": "development"
      }
    }
  }
}
```

`POST /mcp` accepts JSON-RPC (`initialize`, `tools/list`, `tools/call`). Tool names are `mcp__{slug}__{tool}` and are authorized by the policy engine. Clients must not supply raw connector URLs.

This directory’s `proxy.mjs` remains a **stdio fallback** for local Cursor profiles that cannot yet speak Streamable HTTP to the gateway.
