#!/bin/bash
# n8n MCP Server Setup Script
# Run this from any directory on your Mac
# Usage: bash setup_n8n_mcp.sh

set -e

N8N_API_URL="https://mmurawala.app.n8n.cloud"
N8N_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MzM5OTU4NS00ODBiLTQ2NjEtOWFiOS1jMGI2NTYyNzM0ZTkiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMGI4Mjg4ZDUtOThlNy00NzU3LWJjOTktMzY0ZjMxOTZiMTJiIiwiaWF0IjoxNzcxMjc4Nzk0fQ.GnTPw6ht1S5hV5eCZxfSJo1wRy0ojt3peOIPEtu5eaY"

echo "=== n8n MCP Server Setup ==="
echo ""

# Step 1: Check Node.js version and connectivity
echo "[1/5] Testing Node.js connectivity to n8n cloud..."
CONN_TEST=$(node -e "
fetch('${N8N_API_URL}/api/v1/workflows', {
  headers: {'X-N8N-API-KEY': '${N8N_API_KEY}'}
}).then(r => {
  if (r.ok) console.log('OK');
  else console.log('HTTP_' + r.status);
}).catch(e => console.log('FAIL:' + e.code));
" 2>&1)

if [ "$CONN_TEST" = "OK" ]; then
  echo "  Node.js connects to n8n cloud successfully."
  NODE_CMD="node"
elif [[ "$CONN_TEST" == FAIL:* ]]; then
  echo "  Node.js $(node -v) cannot connect: $CONN_TEST"
  echo "  Trying Node 22 LTS via nvm..."

  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

  if command -v nvm &>/dev/null; then
    nvm install 22 2>/dev/null || true
    nvm use 22

    CONN_TEST2=$(node -e "
fetch('${N8N_API_URL}/api/v1/workflows', {
  headers: {'X-N8N-API-KEY': '${N8N_API_KEY}'}
}).then(r => {
  if (r.ok) console.log('OK');
  else console.log('HTTP_' + r.status);
}).catch(e => console.log('FAIL:' + e.code));
" 2>&1)

    if [ "$CONN_TEST2" = "OK" ]; then
      echo "  Node 22 connects successfully."
      NODE_CMD="node"
      NODE_VERSION="22"
    else
      echo "  ERROR: Node 22 also fails: $CONN_TEST2"
      echo "  Please check your network or firewall settings."
      exit 1
    fi
  else
    echo "  ERROR: nvm not found. Install Node 22 LTS and retry."
    exit 1
  fi
else
  echo "  API returned: $CONN_TEST (auth may have issues)"
  echo "  Continuing anyway..."
  NODE_CMD="node"
fi

# Step 2: Remove any old MCP config
echo ""
echo "[2/5] Cleaning up old MCP configurations..."
claude mcp remove n8n-mcp 2>/dev/null && echo "  Removed old n8n-mcp config." || echo "  No old config found."

# Step 3: Install n8n-mcp globally
echo ""
echo "[3/5] Installing n8n-mcp globally..."
npm install -g n8n-mcp 2>&1 | tail -3

# Get the actual path to the n8n-mcp entry point
N8N_MCP_BIN=$(which n8n-mcp 2>/dev/null)
if [ -z "$N8N_MCP_BIN" ]; then
  echo "  ERROR: n8n-mcp binary not found after install."
  exit 1
fi
echo "  Installed at: $N8N_MCP_BIN"

# Resolve the actual JS entry point (follow the bin symlink)
N8N_MCP_JS=$(node -e "console.log(require.resolve('n8n-mcp/dist/mcp/index.js'))" 2>/dev/null || echo "")
if [ -z "$N8N_MCP_JS" ]; then
  N8N_MCP_JS=$(node -e "console.log(require.resolve('n8n-mcp'))" 2>/dev/null || echo "")
fi

# Determine the best command to use
if [ -n "$N8N_MCP_JS" ]; then
  MCP_COMMAND="node"
  MCP_ARGS="$N8N_MCP_JS"
  echo "  Entry point: $N8N_MCP_JS"
else
  MCP_COMMAND="$N8N_MCP_BIN"
  MCP_ARGS=""
  echo "  Using binary directly: $N8N_MCP_BIN"
fi

# Step 4: Register with Claude Code using the resolved path
echo ""
echo "[4/5] Registering MCP server with Claude Code..."

if [ -n "$MCP_ARGS" ]; then
  # Use node + resolved JS path (most reliable)
  if [ -n "$NODE_VERSION" ]; then
    # Need specific node version
    NODE_PATH=$(nvm which $NODE_VERSION 2>/dev/null || which node)
    claude mcp add n8n-mcp --scope user \
      -e MCP_MODE=stdio \
      -e LOG_LEVEL=error \
      -e DISABLE_CONSOLE_OUTPUT=true \
      -e N8N_API_URL="$N8N_API_URL" \
      -e N8N_API_KEY="$N8N_API_KEY" \
      -- "$NODE_PATH" "$MCP_ARGS"
  else
    claude mcp add n8n-mcp --scope user \
      -e MCP_MODE=stdio \
      -e LOG_LEVEL=error \
      -e DISABLE_CONSOLE_OUTPUT=true \
      -e N8N_API_URL="$N8N_API_URL" \
      -e N8N_API_KEY="$N8N_API_KEY" \
      -- node "$MCP_ARGS"
  fi
else
  claude mcp add n8n-mcp --scope user \
    -e MCP_MODE=stdio \
    -e LOG_LEVEL=error \
    -e DISABLE_CONSOLE_OUTPUT=true \
    -e N8N_API_URL="$N8N_API_URL" \
    -e N8N_API_KEY="$N8N_API_KEY" \
    -- "$MCP_COMMAND"
fi

echo "  Registered."

# Step 5: Verify
echo ""
echo "[5/5] Verifying setup..."
claude mcp list 2>/dev/null | grep -A2 n8n-mcp || echo "  (check with: claude mcp list)"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Start Claude Code and say: 'Use n8n_list_workflows to list my workflows'"
echo ""
