# AI Due Diligence Agent Tool — Product Documentation

> Investment due diligence in minutes, not weeks.

---

## Table of Contents

1. [What This Product Does](#1-what-this-product-does)
2. [System Architecture](#2-system-architecture)
3. [The 7-Agent Pipeline: Queries & Logic](#3-the-7-agent-pipeline-queries--logic)
4. [Database Schema & Queries](#4-database-schema--queries)
5. [API Surface](#5-api-surface)
6. [What This Product Does NOT Do](#6-what-this-product-does-not-do)
7. [Phase 2 Roadmap](#7-phase-2-roadmap)

---

## 1. What This Product Does

The AI Due Diligence Agent Tool is an autonomous investment research platform. A user provides a company URL or name, and the system runs a **7-agent sequential pipeline** — each agent is a specialized Claude API call with a domain-specific system prompt — that:

- Researches the company across the open web (team, funding, traction, news)
- Sizes the market (TAM/SAM/SOM) and maps the competitive landscape
- Builds 5-year financial projections across Bear/Base/Bull scenarios
- Assesses risk across 5 dimensions with severity ratings
- Synthesizes everything into a professional investor memo
- Generates a McKinsey-quality HTML report
- Creates a one-page visual infographic

**Three deliverables are produced per analysis:**

| Output | Format | Length | Purpose |
|---|---|---|---|
| Investor Memo | Markdown | ~2,000 words | Partnership meeting discussion doc |
| HTML Report | Self-contained HTML/CSS | ~30 pages | Full analysis with tables, heat maps, financials |
| Infographic | Self-contained HTML/CSS | 1 page | Board deck / executive snapshot |

**Three access modes:**

| Mode | Auth | Use Case |
|---|---|---|
| Web App | None (public) | Quick one-off analysis via browser |
| REST API | API key (`Bearer dd_xxx`) | Programmatic access, integrations |
| MCP Server | Auto-provisioned | Claude Desktop / Claude Code native tool |

**Typical runtime:** 3–7 minutes per analysis.

---

## 2. System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│                                                                     │
│   ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐  │
│   │   Web App     │   │  REST API    │   │  MCP Server (stdio)   │  │
│   │  (Browser)    │   │  (curl/SDK)  │   │  (Claude Desktop)     │  │
│   │              │   │              │   │                       │  │
│   │  index.html   │   │  Bearer auth  │   │  JSON-RPC 2.0        │  │
│   │  analysis.html│   │  dd_xxx keys  │   │  analyze_company()   │  │
│   └──────┬───────┘   └──────┬───────┘   └───────────┬───────────┘  │
│          │                  │                        │              │
└──────────┼──────────────────┼────────────────────────┼──────────────┘
           │                  │                        │
           ▼                  ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                            │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    FastAPI Server                            │   │
│   │                                                             │   │
│   │  POST /api/analyze          → enqueue job                   │   │
│   │  GET  /api/status/{id}      → poll progress (2s interval)   │   │
│   │  GET  /api/results/{id}     → fetch deliverables            │   │
│   │  POST /api/v1/analyze       → API key + credit check        │   │
│   │  POST /admin/create-key     → admin: provision keys          │   │
│   └─────────────────────┬───────────────────────────────────────┘   │
│                         │                                           │
│                         ▼                                           │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │               Worker Pool (max 3 concurrent)                │   │
│   │                                                             │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐                    │   │
│   │   │ Thread 1│  │ Thread 2│  │ Thread 3│  ← FIFO queue      │   │
│   │   └────┬────┘  └────┬────┘  └────┬────┘                    │   │
│   └────────┼────────────┼────────────┼──────────────────────────┘   │
│            │            │            │                               │
│            ▼            ▼            ▼                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                  ORCHESTRATOR                                │   │
│   │                                                             │   │
│   │   Sequential 7-Stage Pipeline (shared state dict)           │   │
│   │                                                             │   │
│   │   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐           │   │
│   │   │Agent 1│──▶│Agent 2│──▶│Agent 3│──▶│Agent 4│           │   │
│   │   │Company│   │Market │   │Finance│   │Risk   │           │   │
│   │   │Research│  │Analysis│  │Model  │   │Assess │           │   │
│   │   └───────┘   └───────┘   └───┬───┘   └───────┘           │   │
│   │                               │                             │   │
│   │                               ▼                             │   │
│   │                        ┌─────────────┐                      │   │
│   │                        │Chart Gen    │                      │   │
│   │                        │(matplotlib) │                      │   │
│   │                        └─────────────┘                      │   │
│   │                                                             │   │
│   │   ┌───────┐   ┌───────┐   ┌───────┐                        │   │
│   │   │Agent 5│──▶│Agent 6│──▶│Agent 7│                        │   │
│   │   │Memo   │   │Report │   │Info-  │                        │   │
│   │   │Writer │   │Gen    │   │graphic│                        │   │
│   │   └───────┘   └───────┘   └───────┘                        │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                  │
│                                                                     │
│   ┌────────────────────┐    ┌────────────────────────────────────┐  │
│   │  SQLite (WAL mode) │    │  Anthropic Claude API              │  │
│   │                    │    │                                    │  │
│   │  api_keys table    │    │  claude-sonnet-4 (all 7 agents)    │  │
│   │  analyses table    │    │  Web Search tool (agents 1,2,4)    │  │
│   │                    │    │  Up to 10 searches per agent       │  │
│   └────────────────────┘    └────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12 |
| Web Framework | FastAPI + Uvicorn |
| LLM | Anthropic Claude Sonnet 4 via `anthropic` SDK |
| Database | SQLite with WAL journaling |
| Templating | Jinja2 |
| Frontend | Vanilla HTML/CSS/JS |
| Charts | Matplotlib (Agg backend, headless) |
| Containerization | Docker (python:3.12-slim) |
| Deployment | Google Cloud Run |
| Secrets | GCP Secret Manager |

### Data Flow

Each analysis creates a **shared state dictionary** that accumulates outputs:

```
state = {}

Agent 1 → state["company_research"]   (text)
Agent 2 → state["market_analysis"]     (text)
Agent 3 → state["financial_modeling"]  (text + JSON block)
          → state["charts"]            (PNG file paths)
Agent 4 → state["risk_assessment"]     (text + JSON block)
Agent 5 → state["investor_memo"]       (markdown)
Agent 6 → state["report"]             (HTML)
Agent 7 → state["infographic"]        (HTML)
```

Each agent receives the full output of all preceding agents as context in its prompt. This means Agent 7 has visibility into everything produced by Agents 1–6.

---

## 3. The 7-Agent Pipeline: Queries & Logic

### Stage 1: Company Research

**Goal:** Build a comprehensive profile of the target company from public information.

**Model:** `claude-sonnet-4` | **Max tokens:** 8,192 | **Tools:** Web Search (up to 10 queries)

**What the agent is told (system prompt):**
> "You are a senior venture capital analyst specializing in company research and due diligence."

**Input:** The user's raw query (e.g., `"Analyze https://agno.com for Series A investment of $30-50M"`)

**Web searches the agent performs (up to 10):**

| Search Intent | Example Query |
|---|---|
| What the company does | `agno.com what does Agno do` |
| Founding team backgrounds | `Agno founders team LinkedIn` |
| Funding rounds and investors | `Agno funding raised investors Crunchbase` |
| Product and technology details | `Agno product features technology stack` |
| Customer traction and metrics | `Agno customers users revenue traction` |
| Recent news and press | `Agno news 2025 2026 announcements` |

For early-stage companies with limited results, the agent falls back to:
- LinkedIn company page, Twitter/X, Product Hunt, GitHub
- Founder podcast appearances, blog posts
- Local tech news, press releases

**Output structure:**
1. Company Overview — what they do, founding date, HQ, mission
2. Product/Service — core offering, tech stack, features, advantages
3. Team — founders + backgrounds, executives, team size, advisors
4. Funding History — all rounds, amounts, investors, latest valuation
5. Traction & Metrics — revenue signals, ARR/MRR, user counts, growth
6. Recent News — press, launches, strategic moves, hiring signals

**Key design decision:** The agent explicitly labels data as CONFIRMED (sourced) vs. ESTIMATED (inferred). This prevents hallucinated metrics from propagating through the pipeline.

---

### Stage 2: Market Analysis

**Goal:** Size the market and map the competitive landscape.

**Model:** `claude-sonnet-4` | **Max tokens:** 8,192 | **Tools:** Web Search (up to 10 queries)

**What the agent is told:**
> "You are a senior market research analyst at a top-tier investment bank."

**Input:** The user's query + the full output of Agent 1 (company research).

**Web searches the agent performs:**

| Search Intent | Example Query |
|---|---|
| Total market size | `AI infrastructure market size 2025 TAM` |
| Market growth rate | `AI infrastructure CAGR forecast 2030` |
| Direct competitors | `Agno competitors AI agent framework` |
| Indirect competitors | `alternative approaches to AI agent orchestration` |
| Industry reports | `Gartner IDC AI infrastructure market report` |
| Regulatory landscape | `AI regulation enterprise compliance 2025` |

**Output structure:**
1. **Market Sizing (with methodology)**
   - TAM — total revenue opportunity with calculation approach
   - SAM — target segment the company can realistically address
   - SOM — near-term capturable share
   - CAGR projections
2. **Competitive Landscape**
   - Direct competitors (same product/market)
   - Indirect competitors (different approach, same problem)
   - Positioning matrix
   - Moats and differentiators
3. **Industry Trends**
   - Macro drivers, regulatory shifts, technology changes, customer behavior
4. **Market Dynamics**
   - Barriers to entry, buyer/supplier power, substitution threats, network effects

---

### Stage 3: Financial Modeling

**Goal:** Build 5-year financial projections across three scenarios and derive valuation.

**Model:** `claude-sonnet-4` | **Max tokens:** 8,192 | **Tools:** None (pure reasoning)

**What the agent is told:**
> "You are a senior financial analyst at a top venture capital firm."

**Input:** User query + company research + market analysis.

**This agent uses no web search.** It synthesizes the research and market data from Agents 1–2 into quantitative projections. This is a deliberate design choice: financial modeling requires consistent assumptions, not more data.

**Output structure:**

1. **Revenue Model** — identifies type (SaaS, marketplace, transactional), key drivers, pricing
2. **5-Year Projections (3 scenarios):**

   | Metric | Bear | Base | Bull |
   |---|---|---|---|
   | Revenue (Y1–Y5) | Conservative | Expected | Optimistic |
   | Revenue growth % | Slow | Moderate | Accelerated |
   | Gross margin % | Lower | Target | Best-case |
   | Operating expenses | High relative | Balanced | Efficient |
   | EBITDA (Y1–Y5) | Breakeven late | Breakeven Y2–3 | Profitable early |

3. **Unit Economics:**
   - CAC (Customer Acquisition Cost)
   - LTV (Lifetime Value)
   - LTV/CAC ratio (target: 3x+)
   - Payback period in months
   - Gross margin %

4. **Return Analysis:**
   - Revenue multiples (from comparable companies)
   - Exit valuations at 10x, 15x, 25x ARR
   - MOIC (Multiple on Invested Capital) per scenario
   - IRR (Internal Rate of Return) assuming 5-year hold

**Critical structured output** — the agent must embed a JSON block:

```json
{
  "revenue_projections": {
    "bear": {"year1": 2.5, "year2": 5.0, "year3": 8.5, "year4": 12.0, "year5": 16.0},
    "base": {"year1": 5.0, "year2": 12.0, "year3": 25.0, "year4": 45.0, "year5": 75.0},
    "bull": {"year1": 8.0, "year2": 20.0, "year3": 45.0, "year4": 85.0, "year5": 150.0}
  },
  "ebitda_projections": { ... },
  "unit_economics": {
    "cac": 500, "ltv": 2500, "ltv_cac_ratio": 5.0,
    "payback_months": 3, "gross_margin_pct": 75
  },
  "valuation": {
    "current_implied": 50, "year5_bear": 80, "year5_base": 375,
    "year5_bull": 750, "revenue_multiple": 5
  }
}
```

**Chart generation** — immediately after Agent 3 completes, the orchestrator parses this JSON and generates three matplotlib charts:

| Chart | Type | What It Shows |
|---|---|---|
| Revenue Projections | Line chart (3 lines + shaded range) | Bear/Base/Bull revenue Y1–Y5 |
| EBITDA Projections | Grouped bar chart | Bear/Base/Bull EBITDA Y1–Y5 |
| Unit Economics | 3-panel chart | LTV vs CAC bars, LTV/CAC ratio, Gross Margin % |

---

### Stage 4: Risk Assessment

**Goal:** Identify and rate risks across 5 dimensions.

**Model:** `claude-sonnet-4` | **Max tokens:** 8,192 | **Tools:** Web Search (up to 10 queries)

**What the agent is told:**
> "You are a senior risk analyst at a major institutional investment firm."

**Input:** User query + company research + market analysis + financial projections.

**Web searches target specific risk vectors:**

| Search Intent | Example Query |
|---|---|
| Regulatory risk | `AI regulation compliance requirements 2025` |
| Competitive threats | `largest AI infrastructure acquisitions 2025` |
| Team/key person risk | `[founder name] previous ventures track record` |
| Financial comparables | `AI startup failure rate Series A` |
| Exit comparables | `AI infrastructure company acquisitions IPOs` |

**5 Risk Dimensions (each rated LOW / MEDIUM / HIGH / CRITICAL):**

| Dimension | What It Evaluates |
|---|---|
| **Market Risk** | Size validation, timing, demand uncertainty, macro sensitivity, policy risk |
| **Execution Risk** | Team gaps, technical complexity, GTM challenges, scaling, key person dependency |
| **Financial Risk** | Burn rate, revenue model validation, unit economics, funding dependency, FX risk |
| **Regulatory & Legal** | Compliance, anticipated changes, IP protection, data privacy, industry-specific legal |
| **Exit Risk** | Liquidity path clarity, comparable exits, timeline, acquirer universe, public market receptivity |

**Output includes:**
- Overall risk rating (LOW–CRITICAL) with numeric score (1–10)
- Top 3 risks that could prevent success
- Key mitigants already in place
- **Recommended Protective Terms** — board seat, milestone tranches, liquidation preferences, anti-dilution, information rights

**Structured JSON output:**
```json
{
  "market_risk": "MEDIUM",
  "execution_risk": "HIGH",
  "financial_risk": "MEDIUM",
  "regulatory_risk": "LOW",
  "exit_risk": "MEDIUM",
  "overall_risk": "MEDIUM"
}
```

---

### Stage 5: Investor Memo

**Goal:** Synthesize all prior analysis into a single decision document.

**Model:** `claude-sonnet-4` | **Max tokens:** 16,384 | **Tools:** None

**What the agent is told:**
> "You are a senior partner at a top-tier venture capital firm writing an investment memo for your partnership meeting."

**Input:** User query + all 4 prior agent outputs.

**Output structure (professional markdown):**
1. Executive Summary (1 paragraph — company, ask, recommendation)
2. Investment Thesis (3–5 defensible bullet points)
3. Company Overview (product, team, traction summary)
4. Market Opportunity (size, growth, why now)
5. Competitive Advantage (moats, differentiation, why this team wins)
6. Financial Summary (Base case projections, unit economics, return profile)
7. Risk Factors & Mitigants (top 3–5 with counterpoints)
8. Investment Recommendation: **INVEST / PASS / MORE DILIGENCE NEEDED**
   - Suggested terms (amount, target ownership)
   - Key conditions or milestones

**Style:** Direct, opinionated, data-backed. No hedging or filler.

---

### Stage 6: Report Generator

**Goal:** Produce a polished, self-contained HTML report.

**Model:** `claude-sonnet-4` | **Max tokens:** 16,384 | **Tools:** None

**What the agent is told:**
> "You are a professional report designer who creates McKinsey-quality investment reports."

**Input:** User query + all 5 prior agent outputs.

**Design system:**
- Typography: `-apple-system, BlinkMacSystemFont, 'Segoe UI'` (system fonts)
- Color: Navy `#1a365d` headers, green `#2d8a4e` positive, red `#c53030` negative
- No external dependencies — all CSS embedded inline
- Print-ready layout

**Report sections:**
1. Title page with company name and analysis date
2. Executive summary callout box with key metrics
3. Company overview
4. Market analysis with TAM/SAM/SOM visualization
5. Financial projections table (Bear/Base/Bull)
6. Risk assessment heat map
7. Investment recommendation
8. Appendix with detailed data

**Output:** Raw HTML (`<!DOCTYPE html>` to `</html>`).

---

### Stage 7: Infographic Generator

**Goal:** Create a one-page visual summary for board decks.

**Model:** `claude-sonnet-4` | **Max tokens:** 16,384 | **Tools:** None

**What the agent is told:**
> "You are an expert infographic designer who creates stunning visual summaries using HTML and CSS."

**Input:** User query + all 5 prior agent outputs (same as Agent 6).

**Design principles:**
- Dark navy (`#0f172a`) or white background
- CSS Grid/Flexbox layouts, no JavaScript
- Unicode symbols for visual interest
- Color-coded: green = strengths, red = risks, blue = market
- CSS-based data visualizations (progress bars, bar charts via `div` widths)

**Must include:**
1. Company name + one-liner (large header)
2. Key metrics dashboard (4–6 metric cards)
3. TAM/SAM/SOM visualization
4. Financial projection snapshot (Base case Y1–Y5 bar chart)
5. Risk dashboard (5 categories, color-coded severity)
6. Investment recommendation badge
7. Top 3 strengths + Top 3 risks

**Output:** Raw HTML, single page, print-ready.

---

## 4. Database Schema & Queries

The application uses **SQLite with WAL (Write-Ahead Logging)** for safe concurrent access from multiple worker threads.

### Tables

#### `api_keys`

```sql
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,                    -- UUID
    key_hash TEXT UNIQUE NOT NULL,          -- SHA-256 hash of the full key
    key_prefix TEXT NOT NULL,               -- First 10 chars (e.g., "dd_abc...")
    name TEXT NOT NULL,                     -- Organization or user name
    email TEXT,                             -- Contact email
    tier TEXT DEFAULT 'free',               -- free | pro | enterprise
    credits_remaining INTEGER DEFAULT 5,   -- Analysis quota
    created_at TEXT NOT NULL,               -- ISO-8601 UTC
    last_used_at TEXT,                      -- Updated on each validated request
    is_active INTEGER DEFAULT 1             -- 0 = revoked
);
```

#### `analyses`

```sql
CREATE TABLE analyses (
    id TEXT PRIMARY KEY,                    -- UUID
    api_key_id TEXT NOT NULL,               -- FK → api_keys
    query TEXT NOT NULL,                    -- User input
    status TEXT DEFAULT 'queued',           -- queued | running | completed | failed
    current_stage INTEGER DEFAULT 0,        -- 0–7 (pipeline progress)
    stage_name TEXT DEFAULT '',             -- Human-readable (e.g., "Market Analysis")
    created_at TEXT NOT NULL,
    started_at TEXT,                        -- Set when first stage begins
    completed_at TEXT,
    error TEXT,                             -- Error message if failed
    result_memo TEXT,                       -- Markdown investor memo
    result_report TEXT,                     -- Full HTML report
    result_infographic TEXT,                -- HTML infographic
    result_summary TEXT,                    -- JSON summary blob
    elapsed_seconds REAL,
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
);
```

### Indexes

```sql
CREATE INDEX idx_analyses_api_key ON analyses(api_key_id);  -- User's analysis list
CREATE INDEX idx_analyses_status ON analyses(status);        -- Worker queue polling
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);        -- Key validation
```

### Key Queries

| Operation | Query | When Used |
|---|---|---|
| **Validate API key** | `SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1` | Every authenticated API request |
| **Update last used** | `UPDATE api_keys SET last_used_at = ? WHERE id = ?` | After successful validation |
| **Decrement credit** | `UPDATE api_keys SET credits_remaining = credits_remaining - 1 WHERE id = ?` | When analysis is created (skipped for enterprise) |
| **Check credits** | `SELECT credits_remaining, tier FROM api_keys WHERE id = ?` | Before decrement — returns false if 0 |
| **Create analysis** | `INSERT INTO analyses (id, api_key_id, query, status, created_at) VALUES (?, ?, ?, 'queued', ?)` | When user submits analysis request |
| **Get next queued** | `SELECT * FROM analyses WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1` | Worker poll loop (every 2 seconds) |
| **Update stage** | `UPDATE analyses SET current_stage = ?, stage_name = ?, status = 'running', started_at = COALESCE(started_at, ?) WHERE id = ?` | Each pipeline stage transition |
| **Complete analysis** | `UPDATE analyses SET status = 'completed', current_stage = 7, stage_name = 'Complete', completed_at = ?, result_memo = ?, result_report = ?, result_infographic = ?, result_summary = ?, elapsed_seconds = ? WHERE id = ?` | Pipeline success |
| **Fail analysis** | `UPDATE analyses SET status = 'failed', error = ?, completed_at = ? WHERE id = ?` | Pipeline error |
| **User's analyses** | `SELECT ... FROM analyses WHERE api_key_id = ? ORDER BY created_at DESC LIMIT ?` | List endpoint (default limit 20) |

### Credit System

| Tier | Credits | Behavior |
|---|---|---|
| `free` | 5 | Decremented per analysis; blocked at 0 |
| `pro` | 100 | Decremented per analysis; blocked at 0 |
| `enterprise` | 10,000 (effectively unlimited) | Decrement check skipped entirely |

---

## 5. API Surface

### Web App Endpoints (no auth)

| Method | Path | Purpose |
|---|---|---|
| `GET /` | Landing page | |
| `GET /analysis/{job_id}` | Analysis progress + results page | |
| `POST /api/analyze` | Submit URL, get `job_id` | |
| `GET /api/status/{job_id}` | Poll progress (status, stage, %) | |
| `GET /api/results/{job_id}` | Fetch memo + report + infographic | |
| `GET /api/results/{job_id}/report` | Raw HTML report | |
| `GET /api/results/{job_id}/infographic` | Raw HTML infographic | |

### REST API Endpoints (Bearer auth)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET /api/v1/health` | API key | Health check |
| `POST /api/v1/analyze` | API key | Submit analysis (deducts 1 credit) |
| `GET /api/v1/analyses` | API key | List user's analyses (limit 20) |
| `GET /api/v1/analyses/{id}` | API key | Check analysis status |
| `GET /api/v1/analyses/{id}/results` | API key | Fetch all results |
| `GET /api/v1/analyses/{id}/memo` | API key | Download markdown memo |
| `GET /api/v1/analyses/{id}/report` | API key | Render HTML report |
| `GET /api/v1/analyses/{id}/infographic` | API key | Render HTML infographic |
| `GET /api/v1/credits` | API key | Check remaining credits |

### Admin Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST /admin/create-key` | `X-Admin-Secret` header | Provision new API keys |

### MCP Tools (Claude Desktop / Claude Code)

| Tool | Input | Output |
|---|---|---|
| `analyze_company` | `{query: string}` | `{analysis_id, status: "queued"}` |
| `check_analysis_status` | `{analysis_id: string}` | `{status, current_stage, stage_name, progress}` |
| `get_analysis_results` | `{analysis_id, format?: "memo"\|"report"\|"all"}` | Results in requested format |
| `list_analyses` | — | Array of all analyses |

---

## 6. What This Product Does NOT Do

This section is critical for setting expectations. The tool has clear boundaries.

### Data & Research Limitations

| What It Does NOT Do | Why |
|---|---|
| **Access proprietary databases** (PitchBook, Crunchbase Pro, Bloomberg, Capital IQ) | No API integrations with paid data providers. All research comes from Claude's web search hitting public sources. |
| **Read uploaded documents** (pitch decks, data rooms, term sheets) | No file upload or document parsing. The input is a URL or company name — nothing else. |
| **Access private company financials** | No data room integration. Financial projections are modeled from public signals, not actual P&L / balance sheets. |
| **Verify claims or cross-reference SEC filings** | No EDGAR or regulatory filing integration. |
| **Track real-time data** (stock prices, live metrics) | No streaming data feeds. Analysis is a point-in-time snapshot. |

### Analysis Limitations

| What It Does NOT Do | Why |
|---|---|
| **Replace human judgment** | The tool produces a starting point. It cannot assess founder character, company culture, or strategic intuition. |
| **Guarantee accuracy of projections** | Financial models are estimates based on public data and LLM reasoning. They are not validated against actuals. |
| **Perform legal due diligence** | No contract review, IP audit, or cap table analysis. |
| **Conduct technical due diligence** | No code review, architecture assessment, or security audit. |
| **Provide real-time competitor monitoring** | Analysis is a one-time run, not a continuous feed. |
| **Account for insider information** | All analysis is based on publicly available data. |

### Infrastructure Limitations

| What It Does NOT Do | Why |
|---|---|
| **Run analyses in parallel per pipeline** | The 7 agents run sequentially (each depends on prior outputs). Parallelism is only across independent analyses. |
| **Cache or reuse research** | Every analysis starts from scratch. There is no knowledge graph or company database that persists across runs. |
| **Support user accounts or analysis history** (web app) | The web app uses in-memory job storage. Closing the browser loses results. The API mode persists to SQLite. |
| **Generate PDF exports** | Reports are HTML. No PDF rendering pipeline exists. |
| **Support multi-language output** | All analysis is in English. |
| **Provide confidence scores on individual claims** | The LLM does not output calibrated probabilities for factual statements. |

---

## 7. Phase 2 Roadmap

> Depth over width. Phase 2 does not add more agent types — it makes the existing pipeline dramatically more reliable, verifiable, and useful for real investment workflows.

---

### 7.1 Source-Grounded Research with Citations & Confidence Scores

**Problem today:** Agent 1 (Company Research) and Agent 2 (Market Analysis) perform web searches and produce narrative text, but the connection between specific claims and specific sources is loose. A reader cannot click through to verify a funding amount or market size number.

**Phase 2 design:**

Every factual claim in the pipeline output gets tagged with:
- **Source URL** — the specific page the claim was found on
- **Confidence tier** — `CONFIRMED` (directly stated in source), `INFERRED` (derived from source), `ESTIMATED` (modeled by the agent)
- **Retrieval timestamp** — when the source was accessed

**Implementation approach:**

1. **Structured web search result capture.** The `BaseAgent.run()` method currently discards `web_search_tool_result` blocks. Phase 2 parses these blocks, extracting URLs, titles, and snippets for every search result the model used.

2. **Citation injection prompt engineering.** Agent system prompts are updated to require inline citations: `"Revenue was $12M ARR as of Q3 2025 [Source: TechCrunch, 2025-09-15]"`. The orchestrator post-processes to convert these into hyperlinks in the report.

3. **Confidence scoring layer.** A lightweight post-processing step (not a full agent — a single API call with structured output) reviews the memo and classifies each major claim into the three confidence tiers. The HTML report renders these as visual badges: green (CONFIRMED), yellow (INFERRED), orange (ESTIMATED).

4. **Source appendix.** The report generator (Agent 6) includes a numbered reference section at the bottom. Every `[Source: ...]` tag maps to a full URL, access date, and relevant excerpt.

**User impact:** Investors can verify claims in seconds instead of re-doing the research. The confidence scoring surfaces where the analysis is speculative, which is exactly where human judgment should focus.

---

### 7.2 Document Ingestion: Pitch Decks, Data Rooms, Term Sheets

**Problem today:** The tool only takes a URL or company name. Real due diligence involves reviewing the company's own materials — pitch decks (PDF), financial models (Excel), data room documents, and term sheets.

**Phase 2 design:**

A new **document ingestion layer** sits between the user input and Agent 1:

```
User uploads files
       ↓
┌──────────────────────┐
│  Document Processor   │
│                       │
│  PDF → text + tables  │
│  PPTX → text + imgs  │
│  XLSX → structured    │
│  DOCX → text          │
└──────────┬────────────┘
           ↓
   Extracted context injected
   into Agent 1–4 prompts
```

**Implementation approach:**

1. **File upload endpoint.** `POST /api/v1/analyze` accepts `multipart/form-data` with up to 10 files (max 50MB total). Supported types: PDF, PPTX, XLSX, DOCX, CSV.

2. **Document processing pipeline.**
   - **PDF:** Use `pymupdf` (or `pdfplumber`) for text extraction + table detection. For pitch decks with heavy graphics, use Claude's vision capability to read slides as images.
   - **XLSX/CSV:** Extract sheet names, column headers, and data. Detect common financial model structures (revenue tabs, cap tables, P&L).
   - **PPTX:** Extract slide text, speaker notes, and embedded tables.

3. **Context injection.** The extracted document content is injected as a new section in each agent's prompt:
   ```
   **Company-Provided Materials**:
   [Extracted pitch deck content]
   [Extracted financial model data]
   ```
   This is especially critical for Agent 3 (Financial Modeling), which currently has to guess at financials from public data. With an actual financial model uploaded, it can validate and extend the company's own projections instead of fabricating them.

4. **Document-aware risk assessment.** Agent 4 gains the ability to flag inconsistencies between the company's claims (in their pitch deck) and public data (from web search). For example: "The pitch deck claims $5M ARR, but no public source corroborates revenue above $2M."

**User impact:** Transforms the tool from "public data analysis" to "actual due diligence workflow." Investors can upload the materials they received from a startup and get an analysis that's grounded in both the company's narrative and independent research.

---

### 7.3 Persistent Company Knowledge Graph

**Problem today:** Every analysis starts from scratch. If you analyze Stripe today and Stripe tomorrow, the tool runs the exact same web searches twice. There is no institutional memory.

**Phase 2 design:**

A **company knowledge graph** that persists across analyses:

```
┌─────────────────────────────────────────────────┐
│                Knowledge Graph                   │
│                                                  │
│  Companies ──< Funding Rounds                   │
│      │──< Team Members                           │
│      │──< Metrics (timestamped)                  │
│      │──< News Events                            │
│      │──< Competitors (edges)                    │
│      │──< Market Segments                        │
│      │──< Risk Assessments (timestamped)         │
│      │──< Analyses (linked)                      │
└─────────────────────────────────────────────────┘
```

**Implementation approach:**

1. **Entity extraction post-processor.** After Agent 1 completes, a structured extraction step pulls out entities: company name, founders (with roles), funding rounds (date, amount, investors), metrics (with timestamps), and news events. These are stored in a normalized PostgreSQL schema (Phase 2 migrates from SQLite).

2. **Incremental research.** When a company is analyzed again, Agent 1's prompt includes the prior knowledge: "This company was last analyzed on [date]. Prior findings: [summary]. Focus your research on what has changed since then." This reduces redundant searches and lets the agent focus on delta — new funding, new hires, new metrics.

3. **Cross-company intelligence.** The knowledge graph enables queries like: "Show me all companies in the AI infrastructure space that raised Series A in the last 6 months." This creates a portfolio-level view that individual analyses cannot provide.

4. **Competitor graph.** Market Analysis (Agent 2) populates competitor edges. Over time, this builds a map of who competes with whom, enabling richer competitive analysis that draws on prior research of those competitors.

**User impact:** The tool gets smarter with use. Repeat analyses are faster and more focused. Portfolio firms can track their investment universe over time instead of running one-off snapshots.

---

### 7.4 Financial Model Validation & Sensitivity Analysis

**Problem today:** Agent 3 (Financial Modeling) produces projections based on LLM reasoning, but there is no validation layer. The numbers could be wildly optimistic or internally inconsistent (e.g., claiming 90% gross margins for a hardware company). The user has no way to stress-test assumptions.

**Phase 2 design:**

A **financial validation and sensitivity layer** that runs after Agent 3:

1. **Internal consistency checks.** Automated validation rules:
   - Revenue growth rate should decline over time (not accelerate indefinitely)
   - EBITDA margins should be plausible for the industry (compare against sector benchmarks)
   - CAC payback period should be shorter than average customer lifetime
   - Bull case should not exceed 3x the base case in Year 1 (a heuristic for reasonableness)
   - If the company has actual financials (from document ingestion), projections must be anchored to the latest actuals

2. **Comparable company benchmarking.** A dedicated data lookup (web search or cached knowledge graph) finds 3–5 comparable public or late-stage companies and compares:
   - Revenue growth trajectory at similar stages
   - Gross margin profile
   - Operating expense ratios
   - Valuation multiples

   The report includes a "how does this compare?" section with a table showing the target company's projections alongside real comparables.

3. **Sensitivity analysis.** The system generates a sensitivity table showing how the valuation changes when key assumptions vary:

   ```
   Base case valuation: $375M

   Sensitivity to revenue growth rate:
   +5% growth  → $450M (+20%)
   -5% growth  → $310M (-17%)

   Sensitivity to gross margin:
   +5% margin  → $410M (+9%)
   -5% margin  → $340M (-9%)

   Sensitivity to exit multiple:
   20x ARR     → $500M (+33%)
   10x ARR     → $250M (-33%)
   ```

4. **Monte Carlo simulation.** For enterprise-tier users, run 1,000 randomized scenarios varying key assumptions within defined ranges. Output a probability distribution of returns (e.g., "70% chance of 3x+ MOIC, 15% chance of loss").

**User impact:** Financial projections become defensible rather than speculative. Investors can present sensitivity analysis to their partners and LPs, which is table stakes for institutional decision-making.

---

### 7.5 Structured Deal Comparison & Portfolio View

**Problem today:** Each analysis is an island. An investor evaluating 5 companies for the same check has to read 5 separate reports and mentally compare them.

**Phase 2 design:**

A **deal comparison dashboard** and **portfolio analytics layer:**

1. **Side-by-side comparison.** Select 2–4 analyses and get a unified comparison view:

   | Metric | Company A | Company B | Company C |
   |---|---|---|---|
   | TAM | $50B | $120B | $30B |
   | Base case Y5 revenue | $75M | $200M | $45M |
   | Overall risk | MEDIUM | HIGH | LOW |
   | LTV/CAC | 5.0x | 2.1x | 8.0x |
   | Recommendation | INVEST | MORE DD | INVEST |

2. **Ranking algorithm.** A scoring function weights the key outputs (market size, risk rating, unit economics, return profile) to produce a ranked list. Weights are configurable per investor's preferences (e.g., "I care more about team risk than market size").

3. **Portfolio construction.** For users who mark analyses as "invested," the dashboard tracks:
   - Total portfolio exposure by sector
   - Aggregate risk profile
   - Projected portfolio returns across scenarios
   - Concentration risk warnings

4. **Persistent analysis history.** All analyses are stored with full results. Users can revisit, re-run (with updated data), or annotate with their own notes and decisions.

**User impact:** Transforms the tool from "analyze one company" to "manage a deal pipeline." This is the workflow VCs actually live in — they're always comparing deals, not evaluating them in isolation.

---

### 7.6 Human-in-the-Loop Feedback & Calibration

**Problem today:** The agents cannot learn from user corrections. If the tool consistently overestimates market sizes or underweights regulatory risk for a particular sector, there is no mechanism to improve.

**Phase 2 design:**

1. **Inline feedback UI.** Each section of the report gets a thumbs-up/thumbs-down + free-text correction field. Users can flag:
   - "This market size number is wrong — it should be $X based on [source]"
   - "This risk was rated LOW but should be HIGH because [reason]"
   - "Missing competitor: [company name]"

2. **Correction propagation.** When a user corrects a factual claim, the correction is stored in the knowledge graph and used in future analyses of the same company or market segment.

3. **Prompt calibration.** Aggregated feedback (across users, with consent) identifies systematic biases:
   - "Market sizes are consistently 2x too high for healthcare startups"
   - "Risk assessment underweights regulatory risk for fintech"

   These patterns are used to adjust agent system prompts with calibration instructions (e.g., "When analyzing healthcare markets, historical analyses have overestimated TAM by approximately 2x. Apply conservative adjustments.").

4. **Outcome tracking.** For invested deals, users can log actual outcomes (follow-on rounds, failures, exits). Over time, this creates a dataset that measures the tool's predictive accuracy and identifies where it adds vs. destroys value.

**User impact:** The tool improves over time — not just from model upgrades, but from the collective intelligence of its user base. This creates a moat: the more it's used, the better it gets, and the harder it is to replicate.

---

### Phase 2 Summary: Depth Map

| Feature | Core Improvement | Effort |
|---|---|---|
| Source-Grounded Citations | Every claim is traceable and verifiable | Medium |
| Document Ingestion | Analyze the company's own materials, not just public data | High |
| Knowledge Graph | Institutional memory across analyses | High |
| Financial Validation | Projections are benchmarked and stress-tested | Medium |
| Deal Comparison | Compare companies side-by-side, manage pipeline | Medium |
| Human Feedback Loop | Tool improves from user corrections over time | High |

**Phase 2 does not make the tool wider (more agent types, more surface area). It makes it deeper: more trustworthy outputs, richer inputs, persistent intelligence, and real workflow integration.**
