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

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `RESEARCH_MODEL` | `claude-sonnet-4-20250514` | Model for research agents |
| `WRITING_MODEL` | `claude-sonnet-4-20250514` | Model for writing agents |
| `OUTPUT_DIR` | `./outputs` | Output directory for generated files |
