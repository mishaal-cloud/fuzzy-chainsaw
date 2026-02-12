# AI Due Diligence Agent Tool

A 7-agent sequential pipeline that autonomously researches any startup, analyzes the market, builds financial models, assesses risks, and generates professional investment reports — all powered by Claude and the Anthropic API.

## Architecture

```
Query → [1. Company Research] → [2. Market Analysis] → [3. Financial Modeling]
     → [4. Risk Assessment] → [5. Investor Memo] → [6. HTML Report] → [7. Infographic]
```

Each agent is a specialized Claude API call with a domain-specific system prompt. Agents run sequentially, with each stage's output passed to subsequent agents via shared state.

### The 7 Agents

| # | Agent | Tools | Output |
|---|-------|-------|--------|
| 1 | Company Research | Web Search | Structured company profile |
| 2 | Market Analysis | Web Search | TAM/SAM/SOM + competitive landscape |
| 3 | Financial Modeling | — | Bear/Base/Bull projections + charts |
| 4 | Risk Assessment | Web Search | Multi-dimensional risk matrix |
| 5 | Investor Memo | — | Professional investment thesis |
| 6 | Report Generator | — | McKinsey-style HTML report |
| 7 | Infographic Generator | — | Visual HTML/CSS summary |

## Setup

```bash
# Install dependencies
pip install -r due_diligence/requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-xxxxx
# or create due_diligence/.env with ANTHROPIC_API_KEY=sk-ant-xxxxx
```

## Usage

```bash
# Interactive mode
python -m due_diligence.main

# Direct query
python -m due_diligence.main "Analyze https://agno.com for Series A investment of $30-50M"

# More examples
python -m due_diligence.main "Due diligence on Stripe for a growth-stage investment"
python -m due_diligence.main "Research Anthropic for a $500M Series D evaluation"
```

## Output

The tool generates:
- **Investor Memo** (Markdown) — Professional investment thesis
- **HTML Report** — McKinsey-style formatted report
- **Infographic** — Visual one-page HTML summary
- **Financial Charts** (PNG) — Revenue projections, EBITDA, unit economics

All outputs are saved to `due_diligence/outputs/` with timestamps.

## API Server (Commercial)

The tool includes a FastAPI server with API key auth, async job processing, and integrations for Claude (MCP), ChatGPT (GPT Actions), and any REST client.

### Quick Start

```bash
# 1. Create an API key
python -m due_diligence.api.manage create-key --name "Your Name" --email "you@example.com" --tier pro

# 2. Start the API server
uvicorn due_diligence.api.server:app --host 0.0.0.0 --port 8000

# 3. Submit an analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer dd_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze Stripe for a growth-stage investment"}'

# 4. Poll for results
curl http://localhost:8000/api/v1/analyses/{analysis_id} \
  -H "Authorization: Bearer dd_your_api_key_here"

# 5. Get completed results
curl http://localhost:8000/api/v1/analyses/{analysis_id}/results \
  -H "Authorization: Bearer dd_your_api_key_here"
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/analyze` | Submit a company for analysis |
| `GET` | `/api/v1/analyses` | List your analyses |
| `GET` | `/api/v1/analyses/{id}` | Check analysis status |
| `GET` | `/api/v1/analyses/{id}/results` | Get full results (JSON) |
| `GET` | `/api/v1/analyses/{id}/report` | Download HTML report |
| `GET` | `/api/v1/analyses/{id}/memo` | Download investor memo |
| `GET` | `/api/v1/analyses/{id}/infographic` | Download HTML infographic |
| `GET` | `/api/v1/credits` | Check remaining credits |
| `GET` | `/api/v1/health` | Health check |

Interactive docs at `http://localhost:8000/docs` (Swagger UI).

### Claude Desktop / Claude Code (MCP)

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "due-diligence": {
      "command": "python",
      "args": ["-m", "due_diligence.mcp_server"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-xxxxx"
      }
    }
  }
}
```

Then in Claude: *"Analyze Stripe for a growth-stage investment"* — Claude will call the tool automatically.

### ChatGPT (Custom GPT Action)

1. Create a Custom GPT at chat.openai.com
2. Add an Action using the OpenAPI schema in `due_diligence/chatgpt_openapi.yaml`
3. Set the API server URL and authentication (API key)
4. Users can then ask the GPT to analyze companies

### API Key Management

```bash
# Create keys
python -m due_diligence.api.manage create-key --name "Acme Fund" --tier enterprise

# List all keys
python -m due_diligence.api.manage list-keys

# Revoke a key
python -m due_diligence.api.manage revoke-key <key-id>

# View analyses for a key
python -m due_diligence.api.manage list-analyses <key-id>
```

### Pricing Tiers

| Tier | Credits | Use Case |
|------|---------|----------|
| `free` | 5 analyses | Trial |
| `pro` | 100 analyses | Active investors |
| `enterprise` | Unlimited | VC firms, accelerators |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `RESEARCH_MODEL` | `claude-sonnet-4-20250514` | Model for research agents |
| `WRITING_MODEL` | `claude-sonnet-4-20250514` | Model for writing agents |
| `OUTPUT_DIR` | `./outputs` | Output directory for generated files |
| `DD_DATABASE_PATH` | `api/due_diligence.db` | SQLite database path |
