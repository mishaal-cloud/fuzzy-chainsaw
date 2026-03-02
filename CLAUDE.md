# CLAUDE.md - AI Assistant Persistent Memory

> **Purpose:** This file is automatically read by Claude Code (and other AI assistants) at the
> start of every session. It eliminates the "20-minute explanation problem" by giving Claude
> immediate context about what this project is and what APIs are available.

---

## Project Overview

This is the **AI Due Diligence Agent Tool** -- a 7-agent sequential pipeline built with
Python/FastAPI that autonomously researches startups, analyzes markets, builds financial models,
assesses risks, and generates professional investment reports. Powered by Claude and the
Anthropic API.

**Tech Stack:** Python 3.11+, FastAPI, Claude API (Anthropic), SQLite, Docker, Google Cloud Run

**Key directories:**
- `due_diligence/` -- Core application (agents, API server, tools, webapp)
- `due_diligence/agents/` -- 7 specialized Claude-powered agents
- `due_diligence/api/` -- FastAPI server with auth, async jobs, database
- `due_diligence/tools/` -- File writer, chart generator utilities
- `due_diligence/webapp/` -- Web application layer
- `n8n/` -- n8n workflow definitions, configs, schemas, and deployment tooling
- `docs/` -- Project documentation

---

## n8n Integration Layer

### YOU HAVE FULL ACCESS TO n8n

This project includes an **n8n cloud instance** that serves as a **Universal API Gateway**.
You (Claude) have **FULL access** to create, modify, activate, deactivate, and delete workflows.
You can call any webhook endpoint to execute API calls through n8n on behalf of the user.

**n8n Cloud Instance:** https://mmurawala.app.n8n.cloud
**n8n REST API Base:** https://mmurawala.app.n8n.cloud/api/v1
**Webhook Base URL:** https://mmurawala.app.n8n.cloud/webhook/

### Authentication

- **n8n Management API:** Uses header `X-N8N-API-KEY` with the value from environment variable `N8N_API_KEY`
- **API Gateway Webhooks:** Uses header `X-API-KEY` with the gateway API key

The API key is stored in the project root `.env` file (gitignored, never committed).
At the start of each session, load it with: `source .env` or `export $(cat .env | grep -v '^#' | xargs)`
Always use `$N8N_API_KEY` for n8n management API calls.

---

## Step 1: Always Start with API Discovery

**Before making any API calls through n8n, ALWAYS call the discovery endpoint first:**

```bash
curl -s https://mmurawala.app.n8n.cloud/webhook/api-discovery \
  -H "X-API-KEY: $N8N_API_KEY"
```

This returns a JSON listing of **ALL available APIs**, their supported actions, required
parameters, and example payloads. Use this response to understand what is available before
attempting any API call.

---

## Step 2: Execute API Calls via the Universal Gateway

All API calls go through a single gateway endpoint. n8n handles authentication, rate limiting,
error handling, and response normalization for every API.

**Endpoint:** `POST https://mmurawala.app.n8n.cloud/webhook/api-gateway`

**Headers:**
```
Content-Type: application/json
X-API-KEY: <gateway-api-key>
```

**Request Body Format:**
```json
{
  "client": "claude",
  "api": "<api_name>",
  "action": "<action_name>",
  "params": {
    "key": "value"
  }
}
```

**Example -- Get Google Ads Campaigns:**
```json
{
  "client": "claude",
  "api": "google_ads",
  "action": "campaigns",
  "params": {
    "customer_id": "123-456-7890",
    "status": "ENABLED"
  }
}
```

**Example -- Get HubSpot Contacts:**
```json
{
  "client": "claude",
  "api": "hubspot",
  "action": "contacts",
  "params": {
    "limit": 100,
    "properties": ["email", "firstname", "lastname", "company"]
  }
}
```

**Example -- Get GA4 Report:**
```json
{
  "client": "claude",
  "api": "ga4",
  "action": "report",
  "params": {
    "property_id": "properties/123456",
    "date_range": "last_30_days",
    "metrics": ["sessions", "conversions"],
    "dimensions": ["date", "source"]
  }
}
```

---

## Available APIs — Full Status (45 APIs across 12 categories)

### WORKING NOW (20 n8n credentials + 8 env keys + 3 free = 31 ready)

| API | Status | Auth | Key Name |
|-----|--------|------|----------|
| Google Ads | CONNECTED | OAuth2 | `google_ads` |
| Google Analytics 4 | CONNECTED | OAuth2 | `ga4` |
| Google Search Console | CONNECTED | OAuth2 | `search_console` |
| Google Sheets | CONNECTED | OAuth2 | `sheets` |
| Gmail | CONNECTED | OAuth2 | `gmail` |
| Google Calendar | CONNECTED | OAuth2 | `calendar` |
| YouTube | CONNECTED | OAuth2 | `youtube` |
| HubSpot | CONNECTED | App Token | `hubspot` |
| Salesforce (Ascend GTM) | CONNECTED | OAuth2 | `salesforce` |
| Salesforce (Kahuna Prod) | CONNECTED | OAuth2 | `salesforce_kahuna_prod` |
| Microsoft Graph (Teams/OneDrive/SharePoint) | CONNECTED | OAuth2 | `microsoft_graph` |
| Microsoft Outlook | CONNECTED | OAuth2 | `microsoft_outlook` |
| Slack | CONNECTED | OAuth2 | `slack` |
| Apollo.io | CONNECTED | HTTP Header | `apollo_io` |
| LinkedIn Community | CONNECTED | OAuth2 | `linkedin_community` |
| OpenAI | CONNECTED | API Key | `openai` |
| Azure OpenAI | CONNECTED | API Key | `azure_openai` |
| Google Gemini | CONNECTED | API Key | `google_gemini` |
| Perplexity AI | CONNECTED | HTTP Header | `perplexity` |
| WordPress (Kahuna) | CONNECTED | App Password | `wordpress` |
| SMTP | CONNECTED | SMTP | `smtp` |
| SEMrush | ENV_KEY | API Key (.env) | `semrush` |
| Gong | ENV_KEY | API Key (.env) | `gong` |
| Microsoft Clarity | ENV_KEY | API Key (.env) | `microsoft_clarity` |
| FRED | ENV_KEY | API Key (.env) | `fred` |
| Census Bureau | ENV_KEY | API Key (.env) | `census` |
| Financial Modeling Prep | ENV_KEY | API Key (.env) | `financial_modeling_prep` |
| NewsAPI.ai | ENV_KEY | API Key (.env) | `newsapi_ai` |
| QuickBooks | ENV_KEY | OAuth2 (.env) | `quickbooks` |
| SEC EDGAR | FREE | None | `sec_edgar` |
| Crossref | FREE | None | `crossref` |
| World Bank | FREE | None | `world_bank` |

### NOT CONFIGURED (10 APIs — need credentials if you want to use them)

| API | What's Needed |
|-----|---------------|
| Meta/Facebook Ads | Facebook Business Manager OAuth2 in n8n |
| LinkedIn Ads | LinkedIn Campaign Manager OAuth2 in n8n |
| TikTok Ads | TikTok Business Center access token |
| Twitter/X Ads | Twitter/X Ads API OAuth2 in n8n |
| Hotjar | Hotjar API key |
| Google Drive | Google Drive OAuth2 (may share with Sheets) |
| Twilio | Twilio Account SID + Auth Token |
| Anthropic (n8n) | Anthropic API key in n8n credential |
| Shopify | Shopify custom app access token |
| Stripe | Stripe restricted API key |

### PENDING VERIFICATION (5)
- **BLS:** Registration submitted — CAPTCHA completion needed
- **Semantic Scholar:** API key request submitted — reCAPTCHA needed
- **Reddit:** API access request submitted — pending approval
- **Visualping:** Account created — pending email verification
- **Growjo:** Contact form submitted — awaiting response

> **Full details:** See `n8n/config/api-registry.json` for exact endpoints, rate limits,
> and credential IDs for all 45 APIs.

---

## n8n Management Commands

You can directly manage the n8n instance via its REST API. All management calls use the
`X-N8N-API-KEY` header.

### List All Workflows
```bash
curl -s https://mmurawala.app.n8n.cloud/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Get a Specific Workflow
```bash
curl -s https://mmurawala.app.n8n.cloud/api/v1/workflows/{id} \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Create a New Workflow
```bash
curl -s -X POST https://mmurawala.app.n8n.cloud/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workflow", "nodes": [...], "connections": {...}, "settings": {...}}'
```

### Activate a Workflow
```bash
curl -s -X POST https://mmurawala.app.n8n.cloud/api/v1/workflows/{id}/activate \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Deactivate a Workflow
```bash
curl -s -X POST https://mmurawala.app.n8n.cloud/api/v1/workflows/{id}/deactivate \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Delete a Workflow
```bash
curl -s -X DELETE https://mmurawala.app.n8n.cloud/api/v1/workflows/{id} \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### List Tags
```bash
curl -s https://mmurawala.app.n8n.cloud/api/v1/tags \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Create a Tag
```bash
curl -s -X POST https://mmurawala.app.n8n.cloud/api/v1/tags \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Infrastructure"}'
```

### List Credentials (metadata only)
```bash
curl -s https://mmurawala.app.n8n.cloud/api/v1/credentials \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### List Executions
```bash
curl -s "https://mmurawala.app.n8n.cloud/api/v1/executions?limit=20" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

---

## n8n Enterprise Architecture

The n8n layer follows a modular enterprise architecture (defined in `n8n/IMPLEMENTATION_PLAN.md`):

```
n8n/
├── workflows/
│   ├── gateways/           # API routing workflows
│   │   ├── api-discovery.json
│   │   ├── marketing-ads-gateway.json
│   │   ├── crm-gateway.json
│   │   ├── analytics-gateway.json (includes SEMrush)
│   │   └── google-suite-gateway.json
│   ├── infrastructure/     # Core services
│   │   ├── error-handler.json
│   │   ├── rate-limiter.json
│   │   ├── request-logger.json
│   │   ├── health-check.json
│   │   └── credential-rotator.json
│   ├── monitoring/         # Observability
│   │   ├── metrics-collector.json
│   │   ├── alert-manager.json
│   │   └── daily-summary.json
│   ├── seo-pipeline/       # SEO optimization for kahunaworkforce.com
│   │   ├── seo-pipeline-master.json    # Orchestrator — run any step
│   │   ├── seo-data-collection.json    # GA4 + GSC + SEMrush data pull
│   │   ├── seo-content-optimizer.json  # Claude rewrite + keyword intent matching
│   │   └── seo-monitoring.json         # Daily position tracking + weekly site audit
│   └── testing/            # Quality assurance
│       ├── test-runner.json
│       └── smoke-tests.json
├── schemas/                # OpenAPI spec, validation schemas
├── config/
│   ├── project-config.json # ★ SINGLE SOURCE OF TRUTH — all IDs, URLs, credential refs
│   ├── api-registry.json   # 31 APIs registered (includes SEMrush)
│   ├── credential-inventory.json
│   └── rate-limits.json
├── docs/                   # Architecture docs and runbooks
└── deploy-to-n8n.sh       # One-command deployment (auto-loads .env, syncs variables)
```

---

## Quick Reference for Claude

| Task | Command |
|------|---------|
| Discover available APIs | `GET /webhook/api-discovery` |
| Call any API | `POST /webhook/api-gateway` with `{client, api, action, params}` |
| List n8n workflows | `GET /api/v1/workflows` with `X-N8N-API-KEY` |
| Create workflow | `POST /api/v1/workflows` with JSON body |
| Activate workflow | `POST /api/v1/workflows/{id}/activate` |
| Check credentials | `GET /api/v1/credentials` |
| Check executions | `GET /api/v1/executions` |
| Run due diligence | `python -m due_diligence.main "Analyze <company>"` |
| Start API server | `uvicorn due_diligence.api.server:app --host 0.0.0.0 --port 8000` |

---

## CRITICAL: Project Configuration — NEVER ASK FOR THESE VALUES

**All configuration is persisted. Do NOT ask the user for API keys, property IDs, or credential IDs.
Read them from the files below.**

### Where everything lives:

| What | File | Committed? |
|------|------|-----------|
| All API keys & secrets | `.env` (project root) | NO — gitignored |
| All n8n credential IDs, property IDs, URLs | `n8n/config/project-config.json` | YES |
| Full API registry (45 APIs with status) | `n8n/config/api-registry.json` | YES |
| n8n credential audit + gap analysis | `n8n/config/credential-inventory.json` | YES |

### Multi-client support:

`project-config.json` supports multiple clients. Current active client: **kahuna**.
To add a new client, copy the `kahuna` block in the `clients` section, change the `client_id`,
fill in the new client's IDs/URLs, then set `active_client` to switch contexts.

### Key values (from project-config.json — DO NOT ASK FOR THESE):

| Value | Location |
|-------|----------|
| **Domain** | `kahunaworkforce.com` |
| **GA4 Property ID** | `273714189` |
| **GA4 Account ID** | `106559456` |
| **GSC Site URL** | `sc-domain:kahunaworkforce.com` |
| **Google Ads Customer ID** | `4320252036` |
| **Google Ads Login Customer ID** | `7980471764` |
| **SEMrush API Key** | In `.env` as `SEMRUSH_API_KEY` |
| **Alert Email** | `mishaal12000@gmail.com` |

### n8n Credential IDs (already configured in n8n UI — reference only):

| Service | n8n Credential ID |
|---------|-------------------|
| Google Ads OAuth2 | `euQhyKgs68cdwZvF` |
| Google Analytics OAuth2 | `cYYciNg6xMKkfDMS` |
| Google Sheets OAuth2 | `oUDxAs0PlSvP3n9e` |
| Gmail OAuth2 | `0qXbdYRtwneXvwEO` |
| Google Calendar OAuth2 | `YBOTpjWlWA1UhvaV` |
| HubSpot (Kahuna Prod) | `n897XkdylqY96hx8` |
| Salesforce OAuth2 | `WlkDj04MLYU1SyVD` |
| Salesforce (Kahuna Prod) | `ABbOdZjXtx2J8mDv` |
| Microsoft Graph OAuth2 | `z23FXnEJjnjbuInH` |
| Microsoft Outlook OAuth2 | `Lu7gp8pIUhM6b8G2` |
| Slack OAuth2 | `Td6a13CD9P2O5K2U` |
| Apollo.io | `AFIHmkvz3sIS1Bsu` |
| LinkedIn Community | `hM6JaaSBePWuzl6y` |
| Azure OpenAI | `EAHLPCcfWwtUgIbD` |
| SMTP | `gaDwb35iC3dImmKu` |
| OpenAI | `BPsL1P1JIsxrhA64` |
| Google Gemini | `gFUoNWMqYRabWDai` |
| YouTube OAuth2 | `53ZQcqJt7zddcm3P` |
| Perplexity | `RubShqStvGuK97fO` |
| WordPress (Kahuna) | `jIBRhrEDzCgVi5ru` |

### Deployment — ONE command, zero manual steps:

```bash
cd ~/Documents/GitHub/fuzzy-chainsaw && ./n8n/deploy-to-n8n.sh
```

This script:
1. Auto-loads `.env` (no arguments needed)
2. Syncs all variables to n8n (SEMRUSH_API_KEY, GA4_PROPERTY_ID, etc.)
3. Deploys all workflows
4. Activates them
5. Tags them

**NEVER tell the user to manually add variables in the n8n UI or look up property IDs.**
**ALWAYS use full absolute paths in commands (e.g. `cd ~/Documents/GitHub/fuzzy-chainsaw && ...`).**

---

## Environment Variables

All environment variables are in `.env` (project root, gitignored). Key ones:

| Variable | Purpose |
|----------|---------|
| `N8N_API_KEY` | n8n instance management API key (header: `X-N8N-API-KEY`) |
| `N8N_INSTANCE_URL` | n8n Cloud URL |
| `SEMRUSH_API_KEY` | SEMrush API for SEO pipeline |
| `GA4_PROPERTY_ID` | Google Analytics 4 property for kahunaworkforce.com |
| `GSC_SITE_URL` | Google Search Console site identifier |
| `GOOGLE_ADS_CUSTOMER_ID` | Google Ads customer account |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads API developer token |
| `APOLLO_API_KEY` | Apollo.io for prospecting |
| `GONG_ACCESS_KEY` | Gong API access key |
| `GONG_CLIENT_SECRET` | Gong API client secret |
| `FRED_API_KEY` | Federal Reserve Economic Data |
| `CENSUS_API_KEY` | US Census Bureau |
| `FMP_API_KEY` | Financial Modeling Prep |
| `NEWSAPI_AI_KEY` | NewsAPI.ai |
| `CLARITY_API_TOKEN` | Microsoft Clarity |
| `ALERT_EMAIL` | Email for monitoring alerts |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key for due diligence agents |
| `ADMIN_SECRET` | Admin secret for `/admin/create-key` endpoint |
| `RESEARCH_MODEL` | Model for research agents (default: `claude-sonnet-4-20250514`) |
| `WRITING_MODEL` | Model for writing agents (default: `claude-sonnet-4-20250514`) |

---

## Reliability & Self-Healing Infrastructure

The n8n layer includes automated monitoring so you never have to guess whether things work.

### Health Check Endpoints

| Endpoint | Method | What It Does |
|----------|--------|-------------|
| `/webhook/health-check` | GET | Tests real API credentials via the gateway — returns per-API status with `healthy`, `credential_expired`, or `unhealthy` |
| `/webhook/alert` | POST | Send alerts with `{severity, source, title, message, context}` — routes to Slack |

### Automated Monitoring (Runs Automatically)

| Workflow | Schedule | What It Does |
|----------|----------|-------------|
| Health Check (Scheduled) | Every 15 min | Tests 8 key API credentials via real gateway calls, alerts on failures |
| Credential Rotator | Daily 8 AM | Checks all 31 credentials against 90-day rotation policy, alerts on expired/expiring |
| Metrics Collector | Every 5 min | Queries n8n execution API, calculates error rates, alerts if >5% |
| Daily Summary | Daily 8 AM | Fetches 24h execution data from n8n API, reports real stats to Slack |
| Smoke Tests | Every hour | Pings the API discovery endpoint, alerts if unreachable |

### Before Making API Calls — Self-Check Procedure

1. **Call health check first** if you are unsure whether credentials work:
   ```bash
   curl -s https://mmurawala.app.n8n.cloud/webhook/health-check
   ```
2. If any API shows `credential_expired`, tell the user:
   *"The {service} credential has expired. Please re-authenticate in the n8n credentials UI
   at https://mmurawala.app.n8n.cloud."*
3. **Do NOT retry failed credential calls** — they will keep failing until the user
   re-authenticates. Move on to other APIs or inform the user.

### OAuth Token Lifecycle

- n8n handles OAuth2 token refresh automatically via refresh tokens
- Refresh tokens themselves expire after ~90 days
- When a refresh token expires, the only fix is manual re-authentication in the n8n UI
- The Credential Rotator workflow alerts 14 days before expiry

### Active Workflows on n8n Instance

The **Universal API Gateway** (ID: `WQCwEDVb2L6Xkuwd`) is the primary gateway.
It supports 30+ APIs and handles auth, rate limiting, and error handling.
Do NOT deploy a separate main-api-gateway — it conflicts with this one.

### n8n Cloud Variables

All workflows use `$vars.*` (n8n project variables) — NOT `$env.*` (server environment
variables), because n8n Cloud does not support `$env` through the UI.

| Variable | Where | Purpose |
|----------|-------|---------|
| `SLACK_WEBHOOK_URL` | n8n Variables | Slack incoming webhook for alerts (posts to #n8n.cloud) |
| `N8N_GATEWAY_API_KEY` | n8n Variables | Gateway API key for health check credential tests |
| `N8N_HOST` | n8n Variables | n8n instance URL (default: `https://mmurawala.app.n8n.cloud`) |

Set these in: n8n UI → Project Settings → Variables tab.

### Slack Notifications

All monitoring workflows send alerts to Slack via `$vars.SLACK_WEBHOOK_URL`.
Currently configured to post to the **#n8n.cloud** channel in the **Ascendgtm** workspace.

---

## Important Notes

1. **Always discover first.** Call `/webhook/api-discovery` before attempting API calls so
   you know exactly what is available and what parameters are required.
2. **You have full n8n access.** Do not hesitate to create, modify, or activate workflows.
   The user has granted you these permissions.
3. **Use the gateway pattern.** Do not try to call external APIs directly. Route everything
   through the n8n gateway -- it handles auth, rate limiting, and error handling.
4. **Check workflow status.** After creating or modifying workflows, verify they are active
   with a GET call.
5. **Tag your workflows.** Use the tag system to keep workflows organized by category.
6. **Use the health check.** Before making API calls, call `/webhook/health-check` to verify
   credentials are valid. Do not guess — check first.
7. **Never deploy main-api-gateway.json.** The Universal API Gateway already handles all
   routing. Deploying a second one causes webhook path conflicts.
8. **Credential issues = tell the user.** If a health check shows `credential_expired`,
   inform the user immediately. Do not retry — it won't work until re-authenticated.
9. **Always use full absolute paths.** When giving the user shell commands, always use full
   directory paths: `cd ~/Documents/GitHub/fuzzy-chainsaw && ...`. Never use relative paths.
10. **NEVER commit secrets to git.** All API keys, tokens, passwords, and high-entropy secrets
    belong in `.env` only. n8n credential IDs (like `euQhyKgs68cdwZvF`) are safe to commit —
    they are internal database identifiers, not secrets. But actual keys/tokens/passwords must
    ONLY be in `.env` (gitignored).
