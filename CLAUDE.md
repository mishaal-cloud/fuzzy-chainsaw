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

## Available API Categories

### Marketing & Ads
| API | Key Name | Example Actions |
|-----|----------|----------------|
| Google Ads | `google_ads` | campaigns, ad_groups, keywords, metrics, budget |
| Meta/Facebook Ads | `meta_ads` | campaigns, adsets, ads, insights, audiences |
| LinkedIn Ads | `linkedin_ads` | campaigns, creatives, analytics, audiences |
| TikTok Ads | `tiktok_ads` | campaigns, ad_groups, ads, reports |

### CRM
| API | Key Name | Example Actions |
|-----|----------|----------------|
| HubSpot | `hubspot` | contacts, companies, deals, tickets, pipelines |
| Salesforce | `salesforce` | leads, opportunities, accounts, contacts, reports |
| Pipedrive | `pipedrive` | deals, persons, organizations, activities, pipelines |

### Analytics
| API | Key Name | Example Actions |
|-----|----------|----------------|
| Google Analytics 4 | `ga4` | report, realtime, audiences, conversions |
| Google Search Console | `search_console` | performance, sitemaps, url_inspection |

### Google Suite
| API | Key Name | Example Actions |
|-----|----------|----------------|
| Gmail | `gmail` | send, search, read, labels, drafts |
| Google Calendar | `google_calendar` | events, create_event, calendars, free_busy |
| Google Drive | `google_drive` | files, upload, download, share, search |
| Google Sheets | `google_sheets` | read, write, append, create, sheets |

### Additional APIs (20+)
- **Social Media:** Twitter/X, Instagram, YouTube
- **Project Management:** Jira, Asana, Monday.com, Notion
- **Communication:** Slack, Microsoft Teams, Discord
- **Email Marketing:** Mailchimp, SendGrid, Klaviyo
- **E-Commerce:** Shopify, Stripe, WooCommerce
- **Developer Tools:** GitHub, GitLab, Bitbucket
- **Cloud:** AWS, GCP, Azure (select services)

> **Tip:** Always call the `/webhook/api-discovery` endpoint for the authoritative, real-time
> list of available APIs and their exact parameter schemas.

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
│   │   ├── main-api-gateway.json
│   │   ├── marketing-ads-gateway.json
│   │   ├── crm-gateway.json
│   │   ├── analytics-gateway.json
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
│   └── testing/            # Quality assurance
│       ├── test-runner.json
│       └── smoke-tests.json
├── schemas/                # OpenAPI spec, validation schemas
├── config/                 # Rate limits, credential inventory, API registry
├── docs/                   # Architecture docs and runbooks
└── deploy-to-n8n.sh       # One-command deployment script
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

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `N8N_API_KEY` | n8n instance management API key (header: `X-N8N-API-KEY`) |
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

### Slack Notifications

All monitoring workflows send alerts to the Slack webhook URL configured in the
n8n environment variable `SLACK_WEBHOOK_URL`. If alerts are not being received,
the user needs to:
1. Create a Slack incoming webhook at https://api.slack.com/messaging/webhooks
2. Set the `SLACK_WEBHOOK_URL` environment variable in n8n settings

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
