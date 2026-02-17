#!/usr/bin/env node
/**
 * Minimal n8n MCP Server — zero dependencies
 * Uses Node.js built-in fetch (works with Node 18+)
 * Provides full workflow management for n8n cloud/self-hosted instances.
 */

const N8N_API_URL = (process.env.N8N_API_URL || '').replace(/\/+$/, '');
const N8N_API_KEY = process.env.N8N_API_KEY || '';
const API_BASE = N8N_API_URL.endsWith('/api/v1') ? N8N_API_URL : `${N8N_API_URL}/api/v1`;

// ─── n8n API client ─────────────────────────────────────────────────

async function n8nFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'X-N8N-API-KEY': N8N_API_KEY,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) {
    throw new Error(`n8n API ${res.status}: ${typeof data === 'object' ? JSON.stringify(data) : data}`);
  }
  return data;
}

// ─── Tool definitions ───────────────────────────────────────────────

const tools = [
  {
    name: 'n8n_list_workflows',
    description: 'List all workflows. Returns id, name, active status, created/updated dates, and tags.',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Max results (1-100, default 100)' },
        active: { type: 'boolean', description: 'Filter by active status' },
        cursor: { type: 'string', description: 'Pagination cursor' },
      },
    },
    handler: async (args) => {
      const params = new URLSearchParams();
      if (args.limit) params.set('limit', args.limit);
      if (args.active !== undefined) params.set('active', args.active);
      if (args.cursor) params.set('cursor', args.cursor);
      const qs = params.toString();
      return n8nFetch(`/workflows${qs ? '?' + qs : ''}`);
    },
  },
  {
    name: 'n8n_get_workflow',
    description: 'Get a workflow by ID. Returns the full workflow definition including nodes and connections.',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Workflow ID (required)' },
      },
      required: ['id'],
    },
    handler: async (args) => n8nFetch(`/workflows/${args.id}`),
  },
  {
    name: 'n8n_create_workflow',
    description: 'Create a new workflow. Provide name, nodes array, and connections object. Created inactive by default.',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Workflow name (required)' },
        nodes: { type: 'array', description: 'Array of workflow nodes' },
        connections: { type: 'object', description: 'Node connections object' },
        settings: { type: 'object', description: 'Optional workflow settings' },
      },
      required: ['name', 'nodes', 'connections'],
    },
    handler: async (args) => {
      return n8nFetch('/workflows', {
        method: 'POST',
        body: JSON.stringify({
          name: args.name,
          nodes: args.nodes,
          connections: args.connections,
          settings: args.settings || { executionOrder: 'v1' },
        }),
      });
    },
  },
  {
    name: 'n8n_update_workflow',
    description: 'Update an existing workflow. Provide the workflow ID and the fields to update.',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Workflow ID (required)' },
        name: { type: 'string', description: 'New workflow name' },
        nodes: { type: 'array', description: 'Updated nodes array' },
        connections: { type: 'object', description: 'Updated connections' },
        settings: { type: 'object', description: 'Updated settings' },
      },
      required: ['id'],
    },
    handler: async (args) => {
      const { id, ...body } = args;
      return n8nFetch(`/workflows/${id}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      });
    },
  },
  {
    name: 'n8n_delete_workflow',
    description: 'Permanently delete a workflow. Cannot be undone.',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Workflow ID (required)' },
      },
      required: ['id'],
    },
    handler: async (args) => n8nFetch(`/workflows/${args.id}`, { method: 'DELETE' }),
  },
  {
    name: 'n8n_activate_workflow',
    description: 'Activate a workflow so it runs on its trigger.',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Workflow ID (required)' },
      },
      required: ['id'],
    },
    handler: async (args) => n8nFetch(`/workflows/${args.id}/activate`, { method: 'POST' }),
  },
  {
    name: 'n8n_deactivate_workflow',
    description: 'Deactivate a workflow.',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Workflow ID (required)' },
      },
      required: ['id'],
    },
    handler: async (args) => n8nFetch(`/workflows/${args.id}/deactivate`, { method: 'POST' }),
  },
  {
    name: 'n8n_list_executions',
    description: 'List workflow executions. Optionally filter by workflow ID or status.',
    inputSchema: {
      type: 'object',
      properties: {
        workflowId: { type: 'string', description: 'Filter by workflow ID' },
        status: { type: 'string', enum: ['success', 'error', 'waiting'], description: 'Filter by status' },
        limit: { type: 'number', description: 'Max results (1-100, default 100)' },
      },
    },
    handler: async (args) => {
      const params = new URLSearchParams();
      if (args.workflowId) params.set('workflowId', args.workflowId);
      if (args.status) params.set('status', args.status);
      if (args.limit) params.set('limit', args.limit);
      const qs = params.toString();
      return n8nFetch(`/executions${qs ? '?' + qs : ''}`);
    },
  },
  {
    name: 'n8n_get_execution',
    description: 'Get details of a specific execution by ID.',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Execution ID (required)' },
      },
      required: ['id'],
    },
    handler: async (args) => n8nFetch(`/executions/${args.id}`),
  },
];

// ─── MCP stdio server ───────────────────────────────────────────────

const toolMap = Object.fromEntries(tools.map((t) => [t.name, t]));

function makeResponse(id, result) {
  return JSON.stringify({ jsonrpc: '2.0', id, result });
}

function makeError(id, code, message) {
  return JSON.stringify({ jsonrpc: '2.0', id, error: { code, message } });
}

function handleRequest(msg) {
  const { id, method, params } = msg;

  if (method === 'initialize') {
    return makeResponse(id, {
      protocolVersion: '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'n8n-direct-mcp', version: '1.0.0' },
    });
  }

  if (method === 'tools/list') {
    return makeResponse(id, {
      tools: tools.map(({ name, description, inputSchema }) => ({
        name,
        description,
        inputSchema,
      })),
    });
  }

  if (method === 'tools/call') {
    const tool = toolMap[params?.name];
    if (!tool) {
      return makeResponse(id, {
        isError: true,
        content: [{ type: 'text', text: `Unknown tool: ${params?.name}` }],
      });
    }

    return tool
      .handler(params?.arguments || {})
      .then((result) =>
        makeResponse(id, {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
        })
      )
      .catch((err) =>
        makeResponse(id, {
          isError: true,
          content: [{ type: 'text', text: `Error: ${err.message}` }],
        })
      );
  }

  // Notifications (no response needed)
  if (!id) return null;

  return makeError(id, -32601, `Method not found: ${method}`);
}

// ─── stdin/stdout transport ─────────────────────────────────────────

let buffer = '';

process.stdin.setEncoding('utf8');
process.stdin.on('data', async (chunk) => {
  buffer += chunk;
  let idx;
  while ((idx = buffer.indexOf('\n')) !== -1) {
    const line = buffer.substring(0, idx).trim();
    buffer = buffer.substring(idx + 1);
    if (!line) continue;

    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      continue;
    }

    const response = await handleRequest(msg);
    if (response) {
      const resolved = await response;
      process.stdout.write(resolved + '\n');
    }
  }
});

process.stdin.on('end', () => process.exit(0));
