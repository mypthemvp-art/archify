#!/usr/bin/env node
/**
 * Minimal policy-engine stub MCP-shaped process.
 * Real deployments should replace this with an authenticated OpenAI MCPKit / FastMCP server.
 * This stub only answers stdio initialize/tools/list with read-only policy helpers.
 */
import readline from 'node:readline';

const tools = [
  {
    name: 'policy_classify_risk',
    description: 'Classify a tool name and arguments as low/medium/high risk (read-only stub).',
    inputSchema: {
      type: 'object',
      properties: {
        tool: { type: 'string' },
        arguments: { type: 'object' },
      },
      required: ['tool'],
    },
  },
  {
    name: 'policy_check_allowlist',
    description: 'Check whether a tool is on the project allowlist (read-only stub).',
    inputSchema: {
      type: 'object',
      properties: { tool: { type: 'string' } },
      required: ['tool'],
    },
  },
];

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on('line', (line) => {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch {
    return;
  }
  const id = msg.id;
  if (msg.method === 'initialize') {
    respond(id, {
      protocolVersion: '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'agent-ops-policy-stub', version: '2.0.0' },
    });
    return;
  }
  if (msg.method === 'tools/list') {
    respond(id, { tools });
    return;
  }
  if (msg.method === 'tools/call') {
    const name = msg.params?.name;
    const tool = msg.params?.arguments?.tool || '';
    if (name === 'policy_classify_risk') {
      const risk = /apply_|delete_|deploy_|publish_/i.test(tool) ? 'high' : 'low';
      respond(id, { content: [{ type: 'text', text: JSON.stringify({ risk, mode: process.env.POLICY_MODE || 'enforce' }) }] });
      return;
    }
    if (name === 'policy_check_allowlist') {
      const allowed = !/cloud_admin|prod_shell|unrestricted_http/i.test(tool);
      respond(id, { content: [{ type: 'text', text: JSON.stringify({ allowed }) }] });
      return;
    }
    respond(id, { content: [{ type: 'text', text: 'unknown tool' }], isError: true });
  }
});

function respond(id, result) {
  process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id, result })}\n`);
}
