# n8n Enterprise API Gateway -- Complete API Reference

**Version:** 2.0.0
**Base URL:** `https://mmurawala.app.n8n.cloud/webhook`
**Last Updated:** 2026-03-02

---

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
   - [GET /api-discovery](#get-api-discovery)
   - [POST /api-gateway](#post-api-gateway)
   - [GET /health-check](#get-health-check)
   - [POST /run-tests](#post-run-tests)
3. [Available APIs](#available-apis)
4. [Error Codes and Handling](#error-codes-and-handling)
5. [Rate Limits](#rate-limits)
6. [Response Envelope](#response-envelope)

---

## Authentication

All requests must include an API key in the `X-API-KEY` header.

```
X-API-KEY: your-api-key-here
```

Requests without a valid API key receive a `401 Unauthorized` response:

```json
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Invalid or missing API key. Include a valid key in the X-API-KEY header."
  }
}
```

API keys are managed by the platform team. Contact them to obtain or rotate keys.

---

## Endpoints

### GET /api-discovery

Returns the complete catalog of available APIs, their actions, required parameters, and rate limits.

**URL:** `https://mmurawala.app.n8n.cloud/webhook/api-discovery`

**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by API category. Values: `marketing_ads`, `crm`, `analytics`, `google_suite`, `communication`, `project_management`, `ecommerce`, `ai_ml`, `data_storage` |
| `api` | string | No | Get details for a specific API (e.g., `hubspot`, `google_ads`) |

**Example Requests:**

```bash
# Full catalog
curl -s https://mmurawala.app.n8n.cloud/webhook/api-discovery \
  -H "X-API-KEY: your-key" | jq .

# Filter by category
curl -s "https://mmurawala.app.n8n.cloud/webhook/api-discovery?category=crm" \
  -H "X-API-KEY: your-key" | jq .

# Specific API details
curl -s "https://mmurawala.app.n8n.cloud/webhook/api-discovery?api=hubspot" \
  -H "X-API-KEY: your-key" | jq .
```

**Success Response (200):**

```json
{
  "success": true,
  "data": {
    "name": "Universal API Gateway",
    "version": "2.0.0",
    "total_apis": 30,
    "categories": {
      "marketing_ads": [
        {
          "name": "google_ads",
          "display_name": "Google Ads",
          "actions": ["campaigns", "ad_groups", "ads", "keywords", "metrics", "create_campaign"],
          "required_params": ["customer_id"],
          "rate_limits": {
            "requests_per_minute": 60,
            "daily_quota": 15000
          }
        },
        {
          "name": "meta_ads",
          "display_name": "Meta/Facebook Ads",
          "actions": ["campaigns", "ad_sets", "ads", "insights", "create_campaign"],
          "required_params": ["ad_account_id"],
          "rate_limits": {
            "requests_per_minute": 200,
            "daily_quota": 50000
          }
        }
      ],
      "crm": [
        {
          "name": "hubspot",
          "display_name": "HubSpot",
          "actions": ["contacts", "companies", "deals", "create_contact", "create_deal", "pipelines", "tickets", "engagements"],
          "required_params": [],
          "rate_limits": {
            "requests_per_second": 10,
            "daily_quota": 500000
          }
        }
      ]
    },
    "usage_examples": [
      {
        "description": "Get HubSpot contacts",
        "request": {
          "client": "claude",
          "api": "hubspot",
          "action": "contacts",
          "params": { "limit": 10 }
        }
      }
    ]
  }
}
```

---

### POST /api-gateway

The primary endpoint for executing API actions. Accepts a standardized request, validates it, applies rate limiting, routes to the appropriate API, and returns a normalized response.

**URL:** `https://mmurawala.app.n8n.cloud/webhook/api-gateway`

**Method:** `POST`

**Headers:**

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | Must be `application/json` |
| `X-API-KEY` | Yes | Authentication key |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client` | string | Yes | Client identifier (e.g., `claude-desktop`, `chatgpt-plugin`, `gemini-agent`, `custom-script`) |
| `api` | string | Yes | Target API identifier (see [Available APIs](#available-apis)) |
| `action` | string | Yes | Action to perform (must be valid for the specified API) |
| `params` | object | No | Action-specific parameters |
| `options` | object | No | Request-level options (see below) |
| `metadata` | object | No | Tracking and correlation metadata (see below) |

**Options Object:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `timeout_ms` | integer | 30000 | Request timeout (1000-120000) |
| `retry` | boolean | true | Retry on transient failures |
| `max_retries` | integer | 3 | Maximum retry attempts (0-5) |
| `cache` | boolean | false | Use cached response if available |
| `cache_ttl_seconds` | integer | 300 | Cache TTL (30-3600) |
| `dry_run` | boolean | false | Validate without executing |

**Metadata Object:**

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string (UUID) | Unique request ID for tracing |
| `correlation_id` | string | Link related requests across systems |
| `source` | string | Originating system or workflow |
| `priority` | string | `low`, `normal`, `high`, `critical` (default: `normal`) |

#### Example: Get Google Ads Campaigns

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "claude-desktop",
    "api": "google_ads",
    "action": "campaigns",
    "params": {
      "customer_id": "123-456-7890",
      "date_range": {
        "start_date": "2026-02-01",
        "end_date": "2026-02-28"
      },
      "limit": 50
    }
  }'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "campaigns": [
      {
        "id": "123456",
        "name": "Brand Awareness Q1",
        "status": "ENABLED",
        "budget": 5000,
        "impressions": 150000,
        "clicks": 4500,
        "cost": 3200.50
      },
      {
        "id": "789012",
        "name": "Product Launch March",
        "status": "ENABLED",
        "budget": 10000,
        "impressions": 85000,
        "clicks": 2100,
        "cost": 4150.00
      }
    ]
  },
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

#### Example: Create a HubSpot Contact

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "chatgpt-plugin",
    "api": "hubspot",
    "action": "create_contact",
    "params": {
      "email": "jane.doe@example.com",
      "firstname": "Jane",
      "lastname": "Doe",
      "company": "Acme Inc",
      "phone": "+1-555-0123"
    }
  }'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "501",
    "properties": {
      "email": "jane.doe@example.com",
      "firstname": "Jane",
      "lastname": "Doe",
      "company": "Acme Inc",
      "phone": "+1-555-0123",
      "createdate": "2026-03-02T12:00:00.000Z"
    }
  },
  "metadata": {
    "request_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "api": "hubspot",
    "action": "create_contact",
    "duration_ms": 180,
    "cached": false,
    "rate_limit_remaining": 499985
  }
}
```

#### Example: Run a GA4 Report

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "gemini-agent",
    "api": "ga4",
    "action": "report",
    "params": {
      "property_id": "properties/123456789",
      "date_range": {
        "start_date": "2026-01-01",
        "end_date": "2026-02-28"
      },
      "fields": ["sessions", "pageviews", "bounceRate"]
    },
    "options": {
      "cache": true,
      "cache_ttl_seconds": 600
    }
  }'
```

#### Example: Send a Slack Message

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "internal-automation",
    "api": "slack",
    "action": "send_message",
    "params": {
      "channel": "#alerts",
      "text": "Daily report generated successfully."
    }
  }'
```

#### Example: Query Salesforce with SOQL

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "claude-desktop",
    "api": "salesforce",
    "action": "soql",
    "params": {
      "query": "SELECT Id, Name, Amount FROM Opportunity WHERE StageName = '\''Closed Won'\'' AND CloseDate = THIS_QUARTER",
      "limit": 100
    }
  }'
```

#### Example: Send Email via SendGrid

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "internal-automation",
    "api": "sendgrid",
    "action": "send_email",
    "params": {
      "to": "recipient@example.com",
      "from": "noreply@example.com",
      "subject": "Monthly Report - March 2026",
      "html_content": "<h1>Monthly Report</h1><p>Please find attached...</p>"
    }
  }'
```

#### Example: Create a Jira Issue

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "claude-desktop",
    "api": "jira",
    "action": "create_issue",
    "params": {
      "project_key": "ENG",
      "summary": "Fix login timeout issue",
      "description": "Users are experiencing timeouts on the login page.",
      "issue_type": "Bug",
      "priority": "High"
    }
  }'
```

#### Example: Dry Run (Validate Without Executing)

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "test-client",
    "api": "hubspot",
    "action": "contacts",
    "params": { "limit": 5 },
    "options": { "dry_run": true }
  }'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "dry_run": true,
    "validation": "passed",
    "would_execute": {
      "api": "hubspot",
      "action": "contacts",
      "params": { "limit": 5 }
    }
  }
}
```

---

### GET /health-check

Check the health status of the gateway and connected APIs.

**URL:** `https://mmurawala.app.n8n.cloud/webhook/health-check`

**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `detailed` | boolean | No | Include per-API health status (default: `false`) |
| `api` | string | No | Check health for a specific API only |

**Example Requests:**

```bash
# Basic health check
curl -s https://mmurawala.app.n8n.cloud/webhook/health-check \
  -H "X-API-KEY: your-key" | jq .

# Detailed health check
curl -s "https://mmurawala.app.n8n.cloud/webhook/health-check?detailed=true" \
  -H "X-API-KEY: your-key" | jq .

# Check specific API
curl -s "https://mmurawala.app.n8n.cloud/webhook/health-check?api=hubspot" \
  -H "X-API-KEY: your-key" | jq .
```

**Basic Response (200):**

```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2026-03-02T12:00:00Z",
  "version": "2.0.0",
  "uptime_seconds": 86400,
  "checks": {
    "gateway": "healthy",
    "total_apis": 30,
    "healthy_apis": 30,
    "degraded_apis": 0,
    "unhealthy_apis": 0
  }
}
```

**Detailed Response (200):**

```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2026-03-02T12:00:00Z",
  "version": "2.0.0",
  "uptime_seconds": 86400,
  "checks": {
    "gateway": "healthy",
    "total_apis": 30,
    "healthy_apis": 29,
    "degraded_apis": 1,
    "unhealthy_apis": 0
  },
  "apis": {
    "google_ads": { "status": "healthy", "latency_ms": 120, "last_checked": "2026-03-02T11:59:00Z" },
    "meta_ads": { "status": "degraded", "latency_ms": 2500, "last_checked": "2026-03-02T11:59:00Z", "message": "High latency detected" },
    "hubspot": { "status": "healthy", "latency_ms": 85, "last_checked": "2026-03-02T11:59:00Z" },
    "salesforce": { "status": "healthy", "latency_ms": 200, "last_checked": "2026-03-02T11:59:00Z" },
    "ga4": { "status": "healthy", "latency_ms": 150, "last_checked": "2026-03-02T11:59:00Z" },
    "gmail": { "status": "healthy", "latency_ms": 90, "last_checked": "2026-03-02T11:59:00Z" },
    "slack": { "status": "healthy", "latency_ms": 65, "last_checked": "2026-03-02T11:59:00Z" },
    "stripe": { "status": "healthy", "latency_ms": 110, "last_checked": "2026-03-02T11:59:00Z" }
  }
}
```

**Unhealthy Response (503):**

```json
{
  "success": false,
  "status": "unhealthy",
  "timestamp": "2026-03-02T12:00:00Z",
  "version": "2.0.0",
  "checks": {
    "gateway": "unhealthy",
    "message": "Critical services unavailable"
  }
}
```

---

### POST /run-tests

Execute integration tests against connected APIs. Returns detailed pass/fail results.

**URL:** `https://mmurawala.app.n8n.cloud/webhook/run-tests`

**Method:** `POST`

**Request Body (all fields optional):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `apis` | array of strings | `[]` (all) | Specific APIs to test. Empty array tests all. |
| `test_level` | string | `basic` | Test depth: `connectivity`, `basic`, `full` |
| `dry_run` | boolean | `false` | Validate test configuration without executing |

**Test Levels:**

| Level | Description | Risk |
|-------|-------------|------|
| `connectivity` | Test authentication and reachability only | None |
| `basic` | Test basic read operations | Low |
| `full` | Test read and write operations | Medium -- use with caution in production |

**Example Requests:**

```bash
# Test all APIs (connectivity only)
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{ "test_level": "connectivity" }'

# Test specific APIs
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "apis": ["google_ads", "hubspot", "slack"],
    "test_level": "basic"
  }'
```

**Success Response (200):**

```json
{
  "success": true,
  "summary": {
    "total": 3,
    "passed": 2,
    "failed": 1,
    "skipped": 0,
    "duration_ms": 5430,
    "success_rate": "66.7%",
    "status": "PARTIAL PASS"
  },
  "results": [
    {
      "api": "google_ads",
      "status": "passed",
      "tests": [
        { "name": "authentication", "status": "passed", "duration_ms": 320 },
        { "name": "list_campaigns", "status": "passed", "duration_ms": 450 }
      ]
    },
    {
      "api": "hubspot",
      "status": "passed",
      "tests": [
        { "name": "authentication", "status": "passed", "duration_ms": 180 },
        { "name": "list_contacts", "status": "passed", "duration_ms": 210 }
      ]
    },
    {
      "api": "slack",
      "status": "failed",
      "tests": [
        { "name": "authentication", "status": "failed", "duration_ms": 150, "error": "invalid_auth: Invalid auth token" }
      ]
    }
  ],
  "tested_at": "2026-03-02T12:00:00Z"
}
```

---

## Available APIs

### Marketing Ads

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| Google Ads | `google_ads` | `campaigns`, `ad_groups`, `ads`, `keywords`, `metrics`, `create_campaign` | `customer_id` |
| Meta/Facebook Ads | `meta_ads` | `campaigns`, `ad_sets`, `ads`, `insights`, `create_campaign` | `ad_account_id` |
| LinkedIn Ads | `linkedin_ads` | `campaigns`, `analytics`, `create_campaign` | -- |
| TikTok Ads | `tiktok_ads` | `campaigns`, `ad_groups`, `reports` | `advertiser_id` |
| Twitter/X Ads | `twitter_ads` | `campaigns`, `line_items`, `analytics` | `account_id` |

### CRM

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| HubSpot | `hubspot` | `contacts`, `companies`, `deals`, `create_contact`, `create_deal`, `pipelines`, `tickets`, `engagements` | -- |
| Salesforce | `salesforce` | `accounts`, `contacts`, `opportunities`, `leads`, `create_lead`, `soql`, `create_account`, `create_opportunity` | -- |
| Pipedrive | `pipedrive` | `deals`, `persons`, `organizations`, `activities`, `create_deal`, `create_person` | -- |

### Analytics

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| Google Analytics 4 | `ga4` | `report`, `realtime`, `audiences`, `dimensions`, `metrics` | `property_id` |
| Google Search Console | `search_console` | `performance`, `sitemaps`, `inspect_url` | `site_url` |
| Mixpanel | `mixpanel` | `events`, `funnels`, `retention`, `export` | `project_id` |
| Hotjar | `hotjar` | `heatmaps`, `recordings`, `surveys` | `site_id` |

### Google Suite

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| Gmail | `gmail` | `list`, `read`, `send`, `search`, `draft`, `labels` | -- |
| Google Calendar | `calendar` | `events`, `create_event`, `update_event`, `delete_event`, `calendars` | -- |
| Google Drive | `drive` | `list`, `download`, `upload`, `search`, `share`, `create_folder` | -- |
| Google Sheets | `sheets` | `read`, `write`, `append`, `create`, `batch_update` | -- |

### Communication

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| Slack | `slack` | `send_message`, `channels`, `users`, `files`, `reactions` | -- |
| Microsoft Teams | `microsoft_teams` | `send_message`, `channels`, `teams`, `chats` | -- |
| SendGrid | `sendgrid` | `send_email`, `templates`, `contacts`, `lists`, `stats` | -- |
| Twilio | `twilio` | `send_sms`, `make_call`, `messages`, `calls` | `account_sid` |

### Project Management

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| Asana | `asana` | `tasks`, `projects`, `workspaces`, `create_task`, `update_task` | -- |
| Jira | `jira` | `issues`, `create_issue`, `update_issue`, `search`, `transitions` | `project_key` |
| Notion | `notion` | `pages`, `databases`, `blocks`, `create_page`, `query_database` | -- |
| Trello | `trello` | `boards`, `lists`, `cards`, `create_card`, `move_card` | -- |

### E-commerce

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| Shopify | `shopify` | `products`, `orders`, `customers`, `inventory`, `create_product` | `shop` |
| Stripe | `stripe` | `charges`, `customers`, `subscriptions`, `invoices`, `payments`, `refunds` | -- |

### AI/ML

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| OpenAI | `openai` | `chat_completion`, `embeddings`, `images`, `audio` | -- |
| Anthropic Claude | `anthropic` | `messages`, `completions` | -- |

### Data Storage

| API | Identifier | Actions | Required Params |
|-----|-----------|---------|----------------|
| Airtable | `airtable` | `list_records`, `create_record`, `update_record`, `delete_record` | `base_id` |
| Supabase | `supabase` | `select`, `insert`, `update`, `delete`, `rpc` | `project_ref` |

---

## Error Codes and Handling

### HTTP Status Codes

| Status | Meaning | Error Code |
|--------|---------|------------|
| 200 | Success | -- |
| 400 | Invalid request | `INVALID_REQUEST`, `UNKNOWN_API`, `INVALID_ACTION`, `MISSING_PARAMS` |
| 401 | Authentication failed | `AUTH_FAILED` |
| 429 | Rate limit exceeded | `RATE_LIMITED` |
| 500 | Internal server error | `INTERNAL_ERROR` |
| 502 | Upstream API error | `API_ERROR` |
| 504 | Gateway timeout | `TIMEOUT` |

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": { }
  }
}
```

### Error Code Details

#### INVALID_REQUEST (400)

Returned when the request body is malformed or missing required fields.

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required field: 'api'",
    "details": {
      "missing_fields": ["api"]
    }
  }
}
```

#### UNKNOWN_API (400)

Returned when the specified API does not exist in the registry.

```json
{
  "success": false,
  "error": {
    "code": "UNKNOWN_API",
    "message": "Unknown API: 'invalid_api'. Use GET /api-discovery to see available APIs.",
    "details": {
      "requested_api": "invalid_api",
      "available_apis": ["google_ads", "meta_ads", "hubspot", "..."],
      "suggestion": "Call GET /api-discovery for the full API catalog"
    }
  }
}
```

#### INVALID_ACTION (400)

Returned when the action is not supported for the specified API.

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ACTION",
    "message": "Action 'invalid_action' is not supported for API 'google_ads'.",
    "details": {
      "requested_action": "invalid_action",
      "available_actions": ["campaigns", "ad_groups", "ads", "keywords", "metrics", "create_campaign"]
    }
  }
}
```

#### MISSING_PARAMS (400)

Returned when required parameters for the API are missing.

```json
{
  "success": false,
  "error": {
    "code": "MISSING_PARAMS",
    "message": "Missing required parameter 'customer_id' for API 'google_ads'.",
    "details": {
      "required_params": ["customer_id"],
      "provided_params": {}
    }
  }
}
```

#### AUTH_FAILED (401)

Returned when the API key is invalid or missing.

```json
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Invalid or missing API key. Include a valid key in the X-API-KEY header."
  }
}
```

#### RATE_LIMITED (429)

Returned when the API's rate limit has been exceeded. Check the `Retry-After` header.

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded for API 'google_ads'. Retry after 45 seconds.",
    "details": {
      "api": "google_ads",
      "limit": 60,
      "window": "per_minute",
      "retry_after_seconds": 45
    }
  }
}
```

**Response Headers:**

| Header | Value |
|--------|-------|
| `Retry-After` | Seconds to wait before retrying |
| `X-RateLimit-Remaining` | `0` |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

#### API_ERROR (502)

Returned when the upstream API returns an error.

```json
{
  "success": false,
  "error": {
    "code": "API_ERROR",
    "message": "Upstream API 'google_ads' returned an error.",
    "details": {
      "upstream_status": 503,
      "upstream_message": "Service temporarily unavailable",
      "api": "google_ads"
    }
  }
}
```

#### TIMEOUT (504)

Returned when the upstream API does not respond within the timeout period.

```json
{
  "success": false,
  "error": {
    "code": "TIMEOUT",
    "message": "Request to 'google_ads' timed out after 30000ms.",
    "details": {
      "api": "google_ads",
      "timeout_ms": 30000
    }
  }
}
```

#### INTERNAL_ERROR (500)

Returned when an unexpected error occurs in the gateway.

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred. Please try again or contact support.",
    "details": {
      "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  }
}
```

### Recommended Error Handling

AI agents and clients should implement the following error handling:

1. **400 errors**: Fix the request. Check API discovery for valid APIs and actions.
2. **401 errors**: Verify the API key is correct and included in the `X-API-KEY` header.
3. **429 errors**: Wait for `Retry-After` seconds, then retry. Reduce request frequency.
4. **502 errors**: The upstream API is having issues. Wait and retry, or check the API's status page.
5. **504 errors**: Increase `options.timeout_ms` or retry later. The upstream API may be slow.
6. **500 errors**: Retry once. If persistent, contact the platform team with the `request_id`.

---

## Rate Limits

Each API has specific rate limits. The gateway enforces these to prevent upstream quota exhaustion.

### Per-API Limits

| API | Limit | Daily Quota |
|-----|-------|-------------|
| Google Ads | 60/min | 15,000 |
| Meta Ads | 200/min | 50,000 |
| LinkedIn Ads | 80/min | 100,000 |
| TikTok Ads | 60/min | 10,000 |
| Twitter Ads | 60/min | 10,000 |
| HubSpot | 10/sec | 500,000 |
| Salesforce | 15,000/day | 15,000 |
| Pipedrive | 10/sec | 100,000 |
| GA4 | 60/min | 50,000 |
| Search Console | 60/min | -- |
| Mixpanel | 60/min | 50,000 |
| Hotjar | 30/min | 10,000 |
| Gmail | 250/min | 1,000,000 |
| Calendar | 100/min | -- |
| Drive | 100/min | -- |
| Sheets | 60/min | -- |
| Slack | 60/min | 100,000 |
| MS Teams | 120/min | 100,000 |
| SendGrid | 10/sec | 100,000 |
| Twilio | 100/sec | 500,000 |
| Asana | 150/min | 100,000 |
| Jira | 60/min | 50,000 |
| Notion | 3/sec | 50,000 |
| Trello | 10/sec | 100,000 |
| Shopify | 2/sec | 50,000 |
| Stripe | 100/sec | 500,000 |
| OpenAI | 60/min | 10,000 |
| Anthropic | 60/min | 10,000 |
| Airtable | 5/sec | 100,000 |
| Supabase | 100/sec | 500,000 |

### Global Limits

| Setting | Value |
|---------|-------|
| Max concurrent requests | 50 |
| Queue max size | 1,000 |
| Queue timeout | 30 seconds |

### Rate Limit Response Headers

Successful responses include rate limit headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

---

## Response Envelope

All responses follow a consistent envelope format.

### Success Envelope

```json
{
  "success": true,
  "data": { },
  "metadata": {
    "request_id": "uuid",
    "api": "string",
    "action": "string",
    "duration_ms": 0,
    "cached": false,
    "rate_limit_remaining": 0
  }
}
```

### Error Envelope

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { }
  }
}
```

### Pagination

For list endpoints that support pagination, use the `params.limit` and `params.offset` fields:

```json
{
  "client": "claude-desktop",
  "api": "hubspot",
  "action": "contacts",
  "params": {
    "limit": 50,
    "offset": 100
  }
}
```

The response may include pagination metadata when applicable:

```json
{
  "success": true,
  "data": {
    "results": [ ],
    "pagination": {
      "total": 500,
      "limit": 50,
      "offset": 100,
      "has_more": true
    }
  }
}
```
