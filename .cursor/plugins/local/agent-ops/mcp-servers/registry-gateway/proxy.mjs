#!/usr/bin/env node
/**
 * Thin MCP-shaped proxy that advertises registry gateway tools and forwards
 * evaluate/invoke/approvals to AGENT_OPS_GATEWAY_URL.
 *
 * Production deployments should terminate MCP at the gateway itself.
 */
import http from 'node:http';
import https from 'node:https';
import readline from 'node:readline';
import { URL } from 'node:url';

const base = (process.env.AGENT_OPS_GATEWAY_URL || 'http://127.0.0.1:8787').replace(/\/$/, '');

function post(path, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(base + path);
    const lib = url.protocol === 'https:' ? https : http;
    const data = JSON.stringify(body);
    const req = lib.request(
      {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname,
        method: 'POST',
        headers: { 'content-type': 'application/json', 'content-length': Buffer.byteLength(data) },
        timeout: 5000,
      },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString('utf8') }));
      },
    );
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function get(path) {
  return new Promise((resolve, reject) => {
    const url = new URL(base + path);
    const lib = url.protocol === 'https:' ? https : http;
    const req = lib.request(url, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    });
    req.on('error', reject);
    req.end();
  });
}

const tools = [
  {
    name: 'registry_list_connectors',
    description: 'List certified connectors from the Agent-Ops registry control plane.',
    inputSchema: { type: 'object', properties: { q: { type: 'string' } } },
  },
  {
    name: 'gateway_evaluate_policy',
    description: 'Ask the policy gateway whether a tool invocation is allowed.',
    inputSchema: {
      type: 'object',
      required: ['connector_slug', 'tool_name'],
      properties: {
        connector_slug: { type: 'string' },
        tool_name: { type: 'string' },
        arguments: { type: 'object' },
        environment: { type: 'string' },
        actor: { type: 'string' },
      },
    },
  },
];

function respond(id, result) {
  process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id, result })}\n`);
}

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on('line', async (line) => {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch {
    return;
  }
  if (msg.method === 'initialize') {
    respond(msg.id, {
      protocolVersion: '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'agent-ops-registry-gateway-proxy', version: '0.1.0' },
    });
    return;
  }
  if (msg.method === 'tools/list') {
    respond(msg.id, { tools });
    return;
  }
  if (msg.method === 'tools/call') {
    try {
      const name = msg.params?.name;
      const args = msg.params?.arguments || {};
      if (name === 'registry_list_connectors') {
        const q = args.q ? `?q=${encodeURIComponent(args.q)}` : '';
        const text = await get(`/api/v1/connectors${q}`);
        respond(msg.id, { content: [{ type: 'text', text }] });
        return;
      }
      if (name === 'gateway_evaluate_policy') {
        const { status, body } = await post('/api/v1/policy/evaluate', {
          actor: args.actor || 'cursor-agent',
          connector_slug: args.connector_slug,
          tool_name: args.tool_name,
          arguments: args.arguments || {},
          environment: args.environment || 'development',
        });
        respond(msg.id, {
          content: [{ type: 'text', text: body }],
          isError: status >= 400,
        });
        return;
      }
      respond(msg.id, { content: [{ type: 'text', text: 'unknown tool' }], isError: true });
    } catch (err) {
      respond(msg.id, {
        content: [{ type: 'text', text: `gateway proxy error: ${err.message}` }],
        isError: true,
      });
    }
  }
});
