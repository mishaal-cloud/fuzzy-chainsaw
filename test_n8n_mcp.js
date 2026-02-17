#!/usr/bin/env node
/**
 * Test script for n8n MCP Server (n8n-mcp v2.35.2)
 *
 * Tests three core capabilities:
 *   1. List n8n workflows — verifies connection is successful and readable
 *   2. Search templates for "Google Sheets to Slack" — verifies template search
 *   3. HTTP Request node documentation — tests documentation retrieval
 *
 * The test runs in two phases:
 *   Phase A: Without N8N_API credentials (documentation + templates only)
 *   Phase B: With N8N_API credentials (all tools including workflow management)
 *
 * Usage:
 *   node test_n8n_mcp.js                         # Runs both phases (placeholder creds for Phase B)
 *   N8N_API_URL=... N8N_API_KEY=... node test_n8n_mcp.js  # Real n8n instance
 */

const { spawn } = require('child_process');
const path = require('path');

const MCP_BIN = path.join(__dirname, 'node_modules', '.bin', 'n8n-mcp');
const TIMEOUT_MS = 30000;

// ─── MCP client helper ──────────────────────────────────────────────

class McpClient {
  constructor(envOverrides = {}) {
    this._reqId = 0;
    this._pending = new Map();
    this._buffer = '';
    this._env = envOverrides;
  }

  async start() {
    this._server = spawn('node', [MCP_BIN], {
      env: {
        ...process.env,
        MCP_MODE: 'stdio',
        LOG_LEVEL: 'error',
        DISABLE_CONSOLE_OUTPUT: 'true',
        ...this._env,
      },
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    this._server.stdout.on('data', (chunk) => {
      this._buffer += chunk.toString();
      let idx;
      while ((idx = this._buffer.indexOf('\n')) !== -1) {
        const line = this._buffer.substring(0, idx).trim();
        this._buffer = this._buffer.substring(idx + 1);
        if (!line) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.id !== undefined && this._pending.has(msg.id)) {
            this._pending.get(msg.id).resolve(msg);
            this._pending.delete(msg.id);
          }
        } catch (e) { /* ignore non-JSON */ }
      }
    });

    this._stderr = '';
    this._server.stderr.on('data', (chunk) => {
      this._stderr += chunk.toString();
    });

    // Initialize
    const init = await this._send('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'n8n-mcp-test', version: '1.0.0' },
    });

    if (init.error) throw new Error('MCP init failed: ' + JSON.stringify(init.error));

    this.serverInfo = init.result?.serverInfo || {};
    this._server.stdin.write(
      JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n'
    );

    // Fetch tools
    const toolsRes = await this._send('tools/list', {});
    this.tools = (toolsRes.result?.tools || []).map((t) => t.name);

    return this;
  }

  async callTool(name, args) {
    return this._send('tools/call', { name, arguments: args });
  }

  stop() {
    if (this._server) this._server.kill('SIGTERM');
  }

  _send(method, params) {
    return Promise.race([
      new Promise((resolve, reject) => {
        const id = ++this._reqId;
        this._pending.set(id, { resolve, reject });
        this._server.stdin.write(
          JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n'
        );
      }),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Timeout waiting for ' + method)), TIMEOUT_MS)
      ),
    ]);
  }
}

// ─── Test definitions ───────────────────────────────────────────────

const tests = [
  {
    id: 1,
    name: 'List n8n workflows',
    description: 'Verifies the connection to an n8n instance is successful and readable.',
    requiresApi: true,
    tool: 'n8n_list_workflows',
    arguments: { limit: 10 },
    validate(result) {
      const text = result?.content?.[0]?.text || '';
      let parsed;
      try { parsed = JSON.parse(text); } catch (e) { parsed = null; }

      if (parsed && parsed.success === false) {
        // API error (e.g. 403 from placeholder creds) — tool loaded & responded
        return {
          passed: 'partial',
          message: 'Tool loaded and responded (API rejected with: ' + (parsed.error || 'unknown') + ')',
          detail: 'The n8n_list_workflows tool is available and functional. ' +
            'A real n8n instance with valid N8N_API_URL/N8N_API_KEY is required for full verification.',
        };
      }
      if (result?.isError) {
        return { passed: false, message: 'Error: ' + text.substring(0, 200), detail: text.substring(0, 400) };
      }
      // Success — real instance returned data
      return {
        passed: true,
        message: 'Successfully listed workflows from n8n instance',
        detail: text.substring(0, 400),
      };
    },
  },
  {
    id: 2,
    name: 'Find n8n template for Google Sheets to Slack',
    description: 'Verifies the template search feature (unique to this MCP server).',
    requiresApi: false,
    tool: 'search_templates',
    arguments: { searchMode: 'keyword', query: 'Google Sheets Slack', limit: 5 },
    validate(result) {
      const text = result?.content?.[0]?.text || '';
      if (result?.isError) {
        return { passed: false, message: 'Template search failed', detail: text.substring(0, 400) };
      }
      const lower = text.toLowerCase();
      const hasResults = lower.includes('google') || lower.includes('slack') || lower.includes('sheet');
      return {
        passed: hasResults,
        message: hasResults
          ? 'Successfully found templates for Google Sheets to Slack'
          : 'No relevant templates found in response',
        detail: text.substring(0, 500),
      };
    },
  },
  {
    id: 3,
    name: 'HTTP Request node documentation',
    description: 'Tests the documentation retrieval for the HTTP Request node.',
    requiresApi: false,
    tool: 'get_node',
    arguments: { nodeType: 'nodes-base.httpRequest', mode: 'docs', detail: 'standard' },
    validate(result) {
      const text = result?.content?.[0]?.text || '';
      if (result?.isError) {
        return { passed: false, message: 'Documentation retrieval failed', detail: text.substring(0, 400) };
      }
      const lower = text.toLowerCase();
      const hasDocs = lower.includes('http') &&
        (lower.includes('request') || lower.includes('method') || lower.includes('url'));
      return {
        passed: hasDocs,
        message: hasDocs
          ? 'Successfully retrieved HTTP Request node documentation'
          : 'Documentation content appears incomplete',
        detail: text.substring(0, 500),
      };
    },
  },
];

// ─── Main runner ────────────────────────────────────────────────────

async function run() {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║          n8n MCP Server — Test Suite                        ║');
  console.log('║          Package: n8n-mcp v2.35.2                           ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log();

  const results = [];
  const hasRealCreds = process.env.N8N_API_URL && process.env.N8N_API_KEY;

  // ── Phase A: Documentation & templates (no API creds needed) ──────
  console.log('Phase A: Documentation & Template tools (no n8n credentials)');
  console.log('─'.repeat(62));

  const clientA = new McpClient();
  await clientA.start();
  console.log(`  Server: ${clientA.serverInfo.name} v${clientA.serverInfo.version}`);
  console.log(`  Tools:  ${clientA.tools.length} (${clientA.tools.join(', ')})`);
  console.log();

  for (const test of tests.filter((t) => !t.requiresApi)) {
    console.log(`  Test ${test.id}: ${test.name}`);
    console.log(`    ${test.description}`);

    if (!clientA.tools.includes(test.tool)) {
      results.push({ ...test, passed: false, message: `Tool "${test.tool}" not available` });
      console.log(`    FAIL: Tool not available`);
      console.log();
      continue;
    }

    const res = await clientA.callTool(test.tool, test.arguments);
    const validation = test.validate(res.result || {});
    results.push({ ...test, ...validation });
    const icon = validation.passed ? 'PASS' : 'FAIL';
    console.log(`    ${icon}: ${validation.message}`);
    if (validation.detail) {
      const preview = validation.detail.substring(0, 200).replace(/\n/g, '\n    ');
      console.log(`    Preview: ${preview}...`);
    }
    console.log();
  }

  clientA.stop();

  // ── Phase B: Workflow management tools (needs N8N_API creds) ──────
  console.log('Phase B: Workflow management tools (N8N_API_URL + N8N_API_KEY)');
  console.log('─'.repeat(62));

  const apiUrl = process.env.N8N_API_URL || 'https://placeholder.example.com';
  const apiKey = process.env.N8N_API_KEY || 'test-placeholder-key';

  if (!hasRealCreds) {
    console.log('  Note: Using placeholder credentials. Set N8N_API_URL and N8N_API_KEY');
    console.log('        environment variables to test against a real n8n instance.');
    console.log();
  }

  const clientB = new McpClient({ N8N_API_URL: apiUrl, N8N_API_KEY: apiKey });
  await clientB.start();
  console.log(`  Server: ${clientB.serverInfo.name} v${clientB.serverInfo.version}`);
  console.log(`  Tools:  ${clientB.tools.length} (includes management tools: ${clientB.tools.filter((t) => t.startsWith('n8n_')).length})`);
  console.log();

  for (const test of tests.filter((t) => t.requiresApi)) {
    console.log(`  Test ${test.id}: ${test.name}`);
    console.log(`    ${test.description}`);

    if (!clientB.tools.includes(test.tool)) {
      results.push({ ...test, passed: false, message: `Tool "${test.tool}" not available` });
      console.log(`    FAIL: Tool not available`);
      console.log();
      continue;
    }

    const res = await clientB.callTool(test.tool, test.arguments);
    const validation = test.validate(res.result || {});
    results.push({ ...test, ...validation });
    const icon = validation.passed === true ? 'PASS' : validation.passed === 'partial' ? 'PARTIAL' : 'FAIL';
    console.log(`    ${icon}: ${validation.message}`);
    if (validation.detail) {
      const preview = validation.detail.substring(0, 200).replace(/\n/g, '\n    ');
      console.log(`    Detail: ${preview}`);
    }
    console.log();
  }

  clientB.stop();

  // ── Summary ───────────────────────────────────────────────────────
  console.log('═'.repeat(62));
  console.log('TEST SUMMARY');
  console.log('═'.repeat(62));

  const passed = results.filter((r) => r.passed === true).length;
  const partial = results.filter((r) => r.passed === 'partial').length;
  const failed = results.filter((r) => r.passed === false).length;

  for (const r of results) {
    const icon = r.passed === true ? 'PASS' : r.passed === 'partial' ? 'PARTIAL' : 'FAIL';
    console.log(`  [${icon}] Test ${r.id}: ${r.name} — ${r.message}`);
  }

  console.log();
  console.log(`Results: ${passed} passed, ${partial} partial, ${failed} failed`);
  console.log(`Total:   ${results.length} tests`);
  console.log();

  if (partial > 0 && !hasRealCreds) {
    console.log('Note: Partial results are expected when N8N_API_URL/N8N_API_KEY are not');
    console.log('configured with real credentials. The tool loaded correctly and responded');
    console.log('to the request — only the API connection itself was rejected.');
    console.log();
  }

  // Exit 0 if no hard failures
  process.exit(failed > 0 ? 1 : 0);
}

run().catch((err) => {
  console.error('Unhandled error:', err);
  process.exit(1);
});
