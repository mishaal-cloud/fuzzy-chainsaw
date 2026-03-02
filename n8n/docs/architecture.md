# n8n Enterprise Architecture

## AI-First Design Philosophy

This architecture is designed so that **any AI frontend** (Claude, Gemini, ChatGPT, or custom agents) can discover and use all connected APIs through a single n8n gateway — with zero local hardware dependencies.

```
┌─────────────────────────────────────────────────┐
│         AI Frontends (No Local Hardware)         │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │ Claude   │  │ Gemini  │  │ ChatGPT / Other │ │
│  └────┬─────┘  └────┬────┘  └───────┬─────────┘ │
└───────┼──────────────┼───────────────┼───────────┘
        │              │               │
        ▼              ▼               ▼
┌─────────────────────────────────────────────────┐
│  Step 1: GET /webhook/api-discovery              │
│  → Returns full API catalog (self-describing)    │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│  Step 2: POST /webhook/api-gateway               │
│  Body: { client, api, action, params }           │
│  → Routes to correct domain gateway              │
└──────────────────┬──────────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Marketing │ │   CRM    │ │Analytics │  ... more
│  Ads     │ │ Gateway  │ │ Gateway  │
│ Gateway  │ │          │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │             │             │
  ┌──┴──┐      ┌──┴──┐      ┌──┴──┐
  │Google│      │Hub- │      │ GA4 │
  │ Ads  │      │Spot │      │     │
  │Meta  │      │SF   │      │GSC  │
  │LI    │      │Pipe │      │     │
  │TikTok│      │drive│      │     │
  └──────┘      └─────┘      └─────┘
```

## Components

### 1. API Discovery (api-discovery.json)
- **Webhook:** `GET /api-discovery`
- **Purpose:** Self-describing endpoint that returns the full API catalog
- **Returns:** JSON with all available APIs, actions, parameters, and examples
- **Why:** Eliminates the "20-minute problem" — any AI can instantly learn what's available

### 2. Main API Gateway (main-api-gateway.json)
- **Webhook:** `POST /api-gateway`
- **Purpose:** Slim router that validates requests and routes to domain gateways
- **Flow:** Validate → Route → Execute Sub-workflow → Format Response
- **Switch:** Routes to 4 domain categories based on API name

### 3. Domain Gateways (sub-workflows)
| Gateway | File | APIs |
|---------|------|------|
| Marketing Ads | marketing-ads-gateway.json | Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads |
| CRM | crm-gateway.json | HubSpot, Salesforce, Pipedrive |
| Analytics | analytics-gateway.json | GA4, Search Console |
| Google Suite | google-suite-gateway.json | Gmail, Calendar, Drive, Sheets |

### 4. Infrastructure (sub-workflows)
| Component | File | Purpose |
|-----------|------|---------|
| Error Handler | error-handler.json | Classify errors, log, alert on critical |
| Request Logger | request-logger.json | Structured logging for all requests |
| Rate Limiter | rate-limiter.json | Prevent API quota exhaustion |
| Health Check | health-check.json | Scheduled API health monitoring (5 min) |
| Health Check Webhook | health-check-webhook.json | On-demand health check via GET /health-check |
| Credential Rotator | credential-rotator.json | Daily credential expiry alerting |

### 5. Monitoring
| Component | File | Purpose |
|-----------|------|---------|
| Metrics Collector | metrics-collector.json | Aggregate execution metrics (5 min) |
| Alert Manager | alert-manager.json | Centralized alert routing (Slack/PagerDuty) |
| Daily Summary | daily-summary.json | Daily ops report at 8 AM |

### 6. Testing
| Component | File | Purpose |
|-----------|------|---------|
| Test Runner | test-runner.json | POST /run-tests — automated test execution |
| Smoke Tests | smoke-tests.json | Hourly lightweight health validation |

## Data Flow

### Request Lifecycle
```
1. AI sends POST /api-gateway { client: "claude", api: "hubspot", action: "contacts" }
2. Webhook receives request
3. Validate Request: check required fields (client, api, action)
4. Route Request: lookup api → category (hubspot → crm)
5. Switch: route to CRM Gateway sub-workflow
6. CRM Gateway: build HTTP request for HubSpot API
7. Make API Call: execute HTTP request
8. Format Response: normalize into standard envelope
9. Return: { success: true, request_id: "...", data: {...} }
```

### Error Flow
```
1. API call fails (timeout, auth error, rate limit)
2. Error Handler sub-workflow triggered
3. Classify: auth_error | rate_limit | timeout | api_error
4. Severity: info | warning | critical
5. Log: store structured error entry
6. Alert: if critical → Slack + PagerDuty
7. Return: error classification to caller
```

## Deployment

All workflows are deployed via `deploy-to-n8n.sh`:
```bash
./n8n/deploy-to-n8n.sh https://mmurawala.app.n8n.cloud YOUR_API_KEY
```

The script:
1. Creates tags (Infrastructure, Gateway, Monitoring, Testing)
2. Deploys all workflow JSON files via n8n REST API
3. Activates workflows that need to be always-on
4. Assigns tags for organization
5. Prints deployment summary with webhook URLs

## Webhook URL Reference

| Endpoint | Method | URL |
|----------|--------|-----|
| API Discovery | GET | https://mmurawala.app.n8n.cloud/webhook/api-discovery |
| API Gateway | POST | https://mmurawala.app.n8n.cloud/webhook/api-gateway |
| Health Check | GET | https://mmurawala.app.n8n.cloud/webhook/health-check |
| Run Tests | POST | https://mmurawala.app.n8n.cloud/webhook/run-tests |
