# n8n Enterprise API Gateway -- Architecture Overview

**Version:** 2.0.0
**Last Updated:** 2026-03-02
**Instance:** https://mmurawala.app.n8n.cloud

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [System Architecture](#system-architecture)
3. [Component Responsibilities](#component-responsibilities)
4. [Data Flow](#data-flow)
5. [Webhook URL Reference](#webhook-url-reference)
6. [API Discovery](#api-discovery)
7. [Connecting AI Agents](#connecting-ai-agents)
8. [Security Model](#security-model)
9. [Scalability and Resilience](#scalability-and-resilience)

---

## Design Philosophy

### AI-First Architecture

This gateway follows an **AI-First** design principle: any AI agent -- Claude, ChatGPT, Gemini, or custom agents -- can interact with 30+ business APIs through a single, standardized webhook interface.

**Core Principles:**

1. **Universal Access**: One endpoint, one request format, all APIs.
2. **Self-Describing**: AI agents discover available APIs and actions at runtime via the `/api-discovery` endpoint. This eliminates the "20-minute problem" -- any AI can instantly learn what is available.
3. **Zero AI Configuration**: No per-AI setup required. Any system that can make HTTP POST requests can use the gateway.
4. **Fail Safe**: Comprehensive error handling, rate limiting, and circuit breaking protect both the gateway and upstream APIs.
5. **Observable**: Every request is logged, traced, and measurable.

### Why n8n?

n8n provides visual workflow automation with native support for 400+ integrations, webhook triggers, credential management, error handling, and execution logging -- all without writing infrastructure code. The n8n Cloud instance at `https://mmurawala.app.n8n.cloud` handles hosting, scaling, and maintenance.

---

## System Architecture

```
+------------------------------------------------------------------+
|                        AI AGENT LAYER                             |
|                                                                   |
|  +----------+   +-----------+   +--------+   +----------------+  |
|  |  Claude   |   |  ChatGPT  |   | Gemini |   | Custom Agents  |  |
|  | Desktop/  |   |  Plugin/  |   | Agent/ |   | (Zapier, Make, |  |
|  |  API      |   |  Actions  |   |  API   |   |  Scripts, etc) |  |
|  +-----+----+   +-----+-----+   +---+----+   +-------+--------+  |
|        |               |             |                |           |
+--------|---------------|-------------|----------------|----------+
         |               |             |                |
         v               v             v                v
+------------------------------------------------------------------+
|                    WEBHOOK INGRESS LAYER                          |
|                                                                   |
|  https://mmurawala.app.n8n.cloud/webhook/                        |
|                                                                   |
|  +----------------+  +---------------+  +---------------------+  |
|  | /api-discovery  |  | /api-gateway  |  | /health-check       |  |
|  | GET             |  | POST          |  | GET                 |  |
|  +----------------+  +---------------+  +---------------------+  |
|                                                                   |
|  +---------------------+                                         |
|  | /run-tests           |                                        |
|  | POST                 |                                        |
|  +---------------------+                                         |
+------------------------------------------------------------------+
         |
         v
+------------------------------------------------------------------+
|                    GATEWAY CORE (n8n Workflows)                   |
|                                                                   |
|  +-------------------+    +-------------------+                  |
|  | Authentication     |    | Request           |                  |
|  | & Authorization    |--->| Validation        |                  |
|  | (X-API-KEY check)  |    | (Schema check)    |                  |
|  +-------------------+    +--------+----------+                  |
|                                     |                             |
|                                     v                             |
|  +-------------------+    +-------------------+                  |
|  | Rate Limiter       |    | Router /          |                  |
|  | (Per-API limits,   |<---| Dispatcher        |                  |
|  |  circuit breaker)  |    | (Category-based)  |                  |
|  +-------------------+    +--------+----------+                  |
|                                     |                             |
|                                     v                             |
|  +--------------------------------------------------------------+|
|  |              DOMAIN GATEWAY WORKFLOWS                         ||
|  |                                                               ||
|  | +------------+ +--------+ +-----------+ +---------+          ||
|  | | Marketing  | |  CRM   | | Analytics | | Google  |          ||
|  | | Ads GW     | |  GW    | |    GW     | | Suite   |          ||
|  | +------------+ +--------+ +-----------+ |  GW     |          ||
|  |                                          +---------+          ||
|  | +------------+ +--------+ +-----------+ +---------+          ||
|  | | Comms      | | Project| | Ecommerce | | AI/ML   |          ||
|  | | GW         | | Mgmt GW| |    GW     | |  GW     |          ||
|  | +------------+ +--------+ +-----------+ +---------+          ||
|  |                                                               ||
|  | +-----------+                                                 ||
|  | | Data      |                                                 ||
|  | | Storage GW|                                                 ||
|  | +-----------+                                                 ||
|  +--------------------------------------------------------------+|
|                                     |                             |
|                                     v                             |
|  +-------------------+    +-------------------+                  |
|  | Response           |    | Error Handler     |                  |
|  | Normalizer         |    | & Logger          |                  |
|  +-------------------+    +-------------------+                  |
+------------------------------------------------------------------+
         |
         v
+------------------------------------------------------------------+
|                    EXTERNAL API LAYER (30+ APIs)                   |
|                                                                   |
|  Marketing:    Google Ads | Meta Ads | LinkedIn Ads | TikTok Ads  |
|                Twitter/X Ads                                      |
|                                                                   |
|  CRM:          HubSpot | Salesforce | Pipedrive                   |
|                                                                   |
|  Analytics:    GA4 | Search Console | Mixpanel | Hotjar           |
|                                                                   |
|  Google Suite: Gmail | Calendar | Drive | Sheets                  |
|                                                                   |
|  Communication: Slack | MS Teams | SendGrid | Twilio              |
|                                                                   |
|  Project Mgmt: Asana | Jira | Notion | Trello                    |
|                                                                   |
|  Ecommerce:    Shopify | Stripe                                   |
|                                                                   |
|  AI/ML:        OpenAI | Anthropic                                 |
|                                                                   |
|  Data Storage: Airtable | Supabase                                |
+------------------------------------------------------------------+
```

---

## Component Responsibilities

### 1. Webhook Ingress Layer

The entry point for all requests. Each webhook path maps to a dedicated n8n workflow.

| Component | Responsibility |
|-----------|---------------|
| `/api-discovery` | Returns the catalog of available APIs, actions, and parameters |
| `/api-gateway` | Primary endpoint for executing API actions |
| `/health-check` | Reports system and API health status |
| `/run-tests` | Executes integration test suites |

### 2. Authentication and Authorization

- Validates the `X-API-KEY` header on every request
- Rejects unauthenticated requests with `401` status
- Supports per-client API key management
- Logs all authentication attempts

### 3. Request Validation

- Validates incoming JSON against `request-validation.json` schema
- Checks that the requested `api` exists in the registry (`api-registry.json`)
- Verifies the `action` is valid for the specified API
- Confirms all `required_params` are present
- Returns descriptive error messages with suggestions (e.g., "Call GET /api-discovery for available APIs")

### 4. Rate Limiter

- Enforces per-API rate limits defined in `rate-limits.json`
- Supports multiple throttle strategies: sliding window, token bucket, fixed window, leaky bucket
- Implements circuit breaker pattern (5 failures trigger open state, 60-second recovery)
- Returns `429 Too Many Requests` with `Retry-After` header when limits exceeded
- Alerts via Slack when usage exceeds 80% of limits

### 5. Router / Dispatcher

- Routes requests to the appropriate domain gateway workflow based on API category
- Passes validated and enriched request context
- Handles request queuing when load is high (max 1000 in queue, 30-second timeout)

### 6. Domain Gateway Workflows

Each category of APIs has a dedicated n8n sub-workflow:

| Domain Gateway | Workflow File | APIs Handled |
|---------------|--------------|-------------|
| Marketing Ads Gateway | `marketing-ads-gateway.json` | Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads, Twitter Ads |
| CRM Gateway | `crm-gateway.json` | HubSpot, Salesforce, Pipedrive |
| Analytics Gateway | `analytics-gateway.json` | GA4, Search Console, Mixpanel, Hotjar |
| Google Suite Gateway | `google-suite-gateway.json` | Gmail, Calendar, Drive, Sheets |
| Communication Gateway | `communication-gateway.json` | Slack, Microsoft Teams, SendGrid, Twilio |
| Project Management Gateway | `project-mgmt-gateway.json` | Asana, Jira, Notion, Trello |
| Ecommerce Gateway | `ecommerce-gateway.json` | Shopify, Stripe |
| AI/ML Gateway | `ai-ml-gateway.json` | OpenAI, Anthropic |
| Data Storage Gateway | `data-storage-gateway.json` | Airtable, Supabase |

### 7. Infrastructure Sub-workflows

| Component | Workflow File | Purpose |
|-----------|--------------|---------|
| Error Handler | `error-handler.json` | Classify errors, log, alert on critical |
| Request Logger | `request-logger.json` | Structured logging for all requests |
| Rate Limiter | `rate-limiter.json` | Prevent API quota exhaustion |
| Health Check | `health-check.json` | Scheduled API health monitoring (every 5 min) |
| Health Check Webhook | `health-check-webhook.json` | On-demand health check via `GET /health-check` |
| Credential Rotator | `credential-rotator.json` | Daily credential expiry alerting |

### 8. Monitoring Sub-workflows

| Component | Workflow File | Purpose |
|-----------|--------------|---------|
| Metrics Collector | `metrics-collector.json` | Aggregate execution metrics (every 5 min) |
| Alert Manager | `alert-manager.json` | Centralized alert routing (Slack/PagerDuty) |
| Daily Summary | `daily-summary.json` | Daily operations report at 8:00 AM |

### 9. Testing Sub-workflows

| Component | Workflow File | Purpose |
|-----------|--------------|---------|
| Test Runner | `test-runner.json` | `POST /run-tests` -- automated test execution |
| Smoke Tests | `smoke-tests.json` | Hourly lightweight health validation |

### 10. Response Normalizer

Transforms varied API response formats into a consistent envelope:

```json
{
  "success": true,
  "data": { "..." },
  "metadata": {
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "api": "google_ads",
    "action": "campaigns",
    "duration_ms": 245,
    "cached": false,
    "rate_limit_remaining": 55
  }
}
```

### 11. Error Handler and Logger

- Catches and normalizes errors from all layers
- Classifies errors: `auth_error`, `rate_limit`, `timeout`, `api_error`, `internal_error`
- Assigns severity: `info`, `warning`, `critical`
- Maps upstream API errors to standardized error codes
- Logs full request/response context for debugging
- Triggers alerts for critical failures via Slack and PagerDuty

---

## Data Flow

### Standard Request Flow

```
1. AI Agent sends POST to /api-gateway
       |
2. Authentication check (X-API-KEY header)
       |
       +-- FAIL --> 401 Unauthorized (AUTH_FAILED)
       |
3. Request validation (schema + registry check)
       |
       +-- FAIL --> 400 Bad Request
       |            (INVALID_REQUEST / UNKNOWN_API / INVALID_ACTION / MISSING_PARAMS)
       |
4. Rate limit check (per-API and global limits)
       |
       +-- FAIL --> 429 Too Many Requests (RATE_LIMITED)
       |
5. Route to domain gateway sub-workflow (based on API category)
       |
6. Domain gateway builds and executes API call with stored credentials
       |
       +-- TIMEOUT --> 504 Gateway Timeout (TIMEOUT)
       +-- API ERROR --> 502 Bad Gateway (API_ERROR)
       |
7. Response normalization (standardized envelope)
       |
8. Return 200 with success response
```

### Discovery Flow

```
1. AI Agent sends GET to /api-discovery
       |
2. Authentication check (X-API-KEY header)
       |
3. Load API registry (api-registry.json)
       |
4. Apply optional query filters (?category=crm or ?api=hubspot)
       |
5. Transform registry into discovery-friendly format
       |
6. Return catalog of APIs, actions, required parameters, and rate limits
```

### Health Check Flow

```
1. Client sends GET to /health-check
       |
2. Authentication check (X-API-KEY header)
       |
3. Check gateway status (workflow active, last execution success)
       |
4. If ?detailed=true: ping each API using health_check_endpoint
       |
5. Aggregate results (healthy / degraded / unhealthy)
       |
6. Return health status with per-API details
```

### Error Flow

```
1. API call fails (timeout, auth error, rate limit, server error)
       |
2. Error Handler sub-workflow triggered
       |
3. Classify error type: auth_error | rate_limit | timeout | api_error
       |
4. Assign severity: info | warning | critical
       |
5. Log structured error entry (timestamp, API, action, error details)
       |
6. If critical --> send alert to Slack #incidents + PagerDuty
       |
7. Return standardized error response to caller
```

---

## Webhook URL Reference

All webhooks are served from the n8n Cloud instance.

### Production Endpoints

| Endpoint | Method | URL | Purpose |
|----------|--------|-----|---------|
| API Discovery | GET | `https://mmurawala.app.n8n.cloud/webhook/api-discovery` | List available APIs and actions |
| API Gateway | POST | `https://mmurawala.app.n8n.cloud/webhook/api-gateway` | Execute API actions |
| Health Check | GET | `https://mmurawala.app.n8n.cloud/webhook/health-check` | System health status |
| Run Tests | POST | `https://mmurawala.app.n8n.cloud/webhook/run-tests` | Run integration tests |

### Test Endpoints (for development)

| Endpoint | Method | URL |
|----------|--------|-----|
| API Discovery (Test) | GET | `https://mmurawala.app.n8n.cloud/webhook-test/api-discovery` |
| API Gateway (Test) | POST | `https://mmurawala.app.n8n.cloud/webhook-test/api-gateway` |
| Health Check (Test) | GET | `https://mmurawala.app.n8n.cloud/webhook-test/health-check` |
| Run Tests (Test) | POST | `https://mmurawala.app.n8n.cloud/webhook-test/run-tests` |

---

## API Discovery

The API Discovery endpoint enables AI agents to dynamically learn what APIs and actions are available without hardcoded knowledge.

### How It Works

1. **AI agent calls** `GET /webhook/api-discovery` (optionally with `?category=crm` or `?api=hubspot`).
2. **Gateway loads** the API registry (`config/api-registry.json`).
3. **Gateway transforms** the registry into a discovery-friendly format.
4. **Response includes** for each API:
   - API name and identifier
   - Available actions (e.g., `campaigns`, `create_contact`)
   - Required parameters (e.g., `customer_id` for Google Ads)
   - Rate limit information
5. **AI agent uses** this information to construct valid `/api-gateway` requests.

### Example Discovery Response

```json
{
  "success": true,
  "data": {
    "total_apis": 30,
    "categories": {
      "crm": [
        {
          "name": "hubspot",
          "display_name": "HubSpot",
          "actions": [
            "contacts",
            "companies",
            "deals",
            "create_contact",
            "create_deal",
            "pipelines",
            "tickets",
            "engagements"
          ],
          "required_params": [],
          "rate_limits": {
            "requests_per_second": 10,
            "daily_quota": 500000
          }
        },
        {
          "name": "salesforce",
          "display_name": "Salesforce",
          "actions": [
            "accounts",
            "contacts",
            "opportunities",
            "leads",
            "create_lead",
            "soql",
            "create_account",
            "create_opportunity"
          ],
          "required_params": [],
          "rate_limits": {
            "requests_per_day": 15000
          }
        }
      ]
    }
  }
}
```

### Why Discovery Matters for AI Agents

- **No hardcoding**: Agents do not need pre-configured lists of APIs.
- **Always current**: If a new API is added to the registry, agents discover it automatically.
- **Self-service**: New AI tools can integrate without any gateway modifications.
- **Eliminates the "20-minute problem"**: An AI assistant can go from zero knowledge to full API access in a single HTTP call.

---

## Connecting AI Agents

### Claude (Anthropic)

#### Via Claude Desktop (MCP Tool)

Configure Claude Desktop to call the gateway webhook as a tool:

```json
{
  "tools": [
    {
      "name": "api_gateway",
      "description": "Execute actions on 30+ business APIs (CRM, ads, analytics, email, etc.) through the n8n gateway. Call api_discovery first to see available APIs.",
      "input_schema": {
        "type": "object",
        "required": ["api", "action"],
        "properties": {
          "api": { "type": "string", "description": "API identifier (e.g., hubspot, google_ads)" },
          "action": { "type": "string", "description": "Action to perform (e.g., contacts, campaigns)" },
          "params": { "type": "object", "description": "Action-specific parameters" }
        }
      }
    },
    {
      "name": "api_discovery",
      "description": "Discover all available APIs, their actions, and required parameters",
      "input_schema": {
        "type": "object",
        "properties": {
          "category": { "type": "string", "description": "Optional: filter by category (marketing_ads, crm, analytics, etc.)" }
        }
      }
    }
  ]
}
```

The tool implementation sends requests to:
```
POST https://mmurawala.app.n8n.cloud/webhook/api-gateway
X-API-KEY: <your-api-key>
Content-Type: application/json
```

#### Via Claude API (Tool Use)

Define the gateway as a tool in the Claude API messages request. Claude will call it when a user asks about business data (CRM contacts, ad campaigns, analytics, etc.).

### ChatGPT (OpenAI)

#### Via Custom GPT Actions

1. Go to **GPT Editor** > **Configure** > **Actions**.
2. Import the OpenAPI spec (`schemas/openapi-spec.yaml`).
3. Set authentication to **API Key** with header name `X-API-KEY`.
4. ChatGPT will automatically show available actions based on the spec.
5. Users can ask natural language questions and ChatGPT will call the gateway.

#### Via Function Calling (API)

Define the gateway endpoints as functions in the OpenAI chat completions API:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "call_api_gateway",
        "description": "Execute business API actions through the n8n gateway",
        "parameters": {
          "type": "object",
          "required": ["api", "action"],
          "properties": {
            "api": {
              "type": "string",
              "enum": [
                "google_ads", "meta_ads", "linkedin_ads", "tiktok_ads", "twitter_ads",
                "hubspot", "salesforce", "pipedrive",
                "ga4", "search_console", "mixpanel", "hotjar",
                "gmail", "calendar", "drive", "sheets",
                "slack", "microsoft_teams", "sendgrid", "twilio",
                "asana", "jira", "notion", "trello",
                "shopify", "stripe", "openai", "anthropic",
                "airtable", "supabase"
              ]
            },
            "action": { "type": "string" },
            "params": { "type": "object" }
          }
        }
      }
    }
  ]
}
```

### Gemini (Google)

#### Via Function Declarations

```python
import google.generativeai as genai

api_gateway_tool = genai.Tool(
    function_declarations=[
        genai.FunctionDeclaration(
            name="call_api_gateway",
            description="Execute business API actions through the n8n gateway",
            parameters={
                "type": "object",
                "required": ["api", "action"],
                "properties": {
                    "api": {
                        "type": "string",
                        "description": "Target API (e.g., hubspot, google_ads, slack)"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to perform (e.g., contacts, campaigns, send_message)"
                    },
                    "params": {
                        "type": "object",
                        "description": "Action-specific parameters"
                    }
                }
            }
        ),
        genai.FunctionDeclaration(
            name="discover_apis",
            description="Discover all available APIs and their capabilities",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category filter"
                    }
                }
            }
        )
    ]
)

model = genai.GenerativeModel(
    model_name="gemini-pro",
    tools=[api_gateway_tool]
)
```

### Any HTTP Client

Any system that can make HTTP requests can use the gateway:

```bash
# Discover available APIs
curl -s https://mmurawala.app.n8n.cloud/webhook/api-discovery \
  -H "X-API-KEY: your-api-key" | jq .

# Execute an API action
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-api-key" \
  -d '{
    "client": "curl-test",
    "api": "hubspot",
    "action": "contacts",
    "params": { "limit": 10 }
  }'

# Check system health
curl -s https://mmurawala.app.n8n.cloud/webhook/health-check \
  -H "X-API-KEY: your-api-key" | jq .
```

---

## Security Model

### Authentication

- All endpoints require a valid `X-API-KEY` header
- API keys are managed per-client and stored in n8n credentials
- Keys follow the naming convention `PROD_N8N_GATEWAY_API_KEY`
- Keys can be rotated without downtime (add new key, update clients, remove old key)

### Credential Isolation

- API credentials (OAuth tokens, API keys) are stored exclusively in the n8n credential store
- Credentials are never exposed in webhook responses or logs
- Each API credential follows least-privilege scoping
- See `config/credential-inventory.json` for the complete inventory

### Network Security

- All traffic uses HTTPS (TLS 1.2+)
- n8n Cloud provides DDoS protection and WAF
- Webhook endpoints are only accessible via HTTPS
- No sensitive data in URL query parameters

### Audit Trail

- Every request is logged with timestamp, client, API, action, and result
- n8n execution logs provide full request/response traces
- Failed authentication attempts are tracked and alertable
- Quarterly credential audits per `credential-inventory.json` policy

---

## Scalability and Resilience

### Rate Limiting

- Per-API rate limits prevent upstream API abuse (see `config/rate-limits.json`)
- Global concurrent request limit of 50 prevents gateway overload
- Request queue (max 1000, 30-second timeout) handles burst traffic
- Multiple throttle strategies per API: sliding window, token bucket, fixed window, leaky bucket

### Circuit Breaker

- 5 consecutive failures to an API trigger the circuit breaker (open state)
- Open state rejects requests immediately for 60 seconds (fail-fast)
- Half-open state allows 3 test requests before fully reopening
- Prevents cascading failures from a single unhealthy API

### Retry Strategy

- Exponential backoff: 1s, 2s, 4s (configurable per API)
- Maximum 3 retries by default (client-configurable up to 5 via `options.max_retries`)
- Only retries on transient errors (5xx status codes, timeouts, network errors)
- Does not retry on client errors (4xx) to prevent infinite loops

### Monitoring and Alerting

- Health check endpoint (`GET /health-check`) for external monitoring tools (Datadog, Pingdom, etc.)
- Scheduled health checks every 5 minutes via `health-check.json` workflow
- Hourly smoke tests via `smoke-tests.json` workflow
- Slack alerts when API usage exceeds 80% of limits
- PagerDuty integration for critical failures
- Daily operations summary report at 8:00 AM via `daily-summary.json` workflow

### Deployment

All workflows are deployed via the deployment script:

```bash
./n8n/deploy-to-n8n.sh https://mmurawala.app.n8n.cloud YOUR_API_KEY
```

The script:
1. Creates tags (Infrastructure, Gateway, Monitoring, Testing)
2. Deploys all workflow JSON files via n8n REST API
3. Activates workflows that need to be always-on
4. Assigns tags for organization
5. Prints deployment summary with webhook URLs
