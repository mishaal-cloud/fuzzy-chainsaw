# API Gateway Reference

## Base URL
```
https://mmurawala.app.n8n.cloud/webhook
```

## Authentication
Include your API key in the `X-API-KEY` header for gateway endpoints.

---

## Endpoints

### GET /api-discovery
Returns the complete API catalog with all available APIs, actions, and parameters.

**Request:**
```bash
curl https://mmurawala.app.n8n.cloud/webhook/api-discovery
```

**Response:**
```json
{
  "name": "Universal API Gateway",
  "version": "2.0.0",
  "endpoints": { ... },
  "apis": {
    "marketing_ads": { "google_ads": {...}, "meta_ads": {...} },
    "crm": { "hubspot": {...}, "salesforce": {...} },
    "analytics": { "ga4": {...}, "search_console": {...} },
    "google_suite": { "gmail": {...}, "calendar": {...} }
  },
  "usage_examples": [...]
}
```

---

### POST /api-gateway
Execute an API call through the gateway.

**Request:**
```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "X-API-KEY: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "client": "claude",
    "api": "hubspot",
    "action": "contacts",
    "params": { "query": "john@example.com", "limit": 10 }
  }'
```

**Body Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| client | string | Yes | Client identifier (claude, gemini, chatgpt, custom) |
| api | string | Yes | API name from the catalog |
| action | string | Yes | Action to perform |
| params | object | No | Action-specific parameters |

**Success Response (200):**
```json
{
  "success": true,
  "request_id": "exec-abc123",
  "timestamp": "2026-03-02T12:00:00Z",
  "api": "hubspot",
  "action": "contacts",
  "data": { ... }
}
```

**Validation Error (400):**
```json
{
  "error": true,
  "status_code": 400,
  "message": "Invalid request",
  "validation_errors": ["Missing required field: api"]
}
```

**Unknown API Error (404):**
```json
{
  "error": true,
  "status_code": 404,
  "message": "Unknown API: foo",
  "available_apis": ["google_ads", "meta_ads", "hubspot", ...],
  "suggestion": "Call GET /api-discovery for the full API catalog"
}
```

---

### GET /health-check
Check health status of all connected APIs.

**Request:**
```bash
curl https://mmurawala.app.n8n.cloud/webhook/health-check
```

**Response:**
```json
{
  "overall_status": "healthy",
  "total_apis": 4,
  "healthy_count": 4,
  "unhealthy_count": 0,
  "health_report": [
    { "api": "google_ads", "status": "healthy", "response_time_ms": 120 },
    { "api": "hubspot", "status": "healthy", "response_time_ms": 85 }
  ],
  "checked_at": "2026-03-02T12:00:00Z"
}
```

---

### POST /run-tests
Execute automated tests against the gateway.

**Request:**
```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests
```

**Response:**
```json
{
  "total": 5,
  "passed": 5,
  "failed": 0,
  "success_rate": "100%",
  "status": "ALL TESTS PASSED",
  "results": [
    { "test_name": "API Discovery - Returns Catalog", "passed": true },
    { "test_name": "Gateway - Valid Request Structure", "passed": true }
  ]
}
```

---

## Available APIs

### Marketing Ads
| API | Key | Actions |
|-----|-----|---------|
| Google Ads | `google_ads` | campaigns, ad_groups, ads, keywords, metrics, create_campaign |
| Meta Ads | `meta_ads` | campaigns, ad_sets, ads, insights, create_campaign |
| LinkedIn Ads | `linkedin_ads` | campaigns, analytics, create_campaign |
| TikTok Ads | `tiktok_ads` | campaigns, ad_groups, reports |

### CRM
| API | Key | Actions |
|-----|-----|---------|
| HubSpot | `hubspot` | contacts, companies, deals, create_contact, create_deal, pipelines |
| Salesforce | `salesforce` | accounts, contacts, opportunities, leads, create_lead, soql |
| Pipedrive | `pipedrive` | deals, persons, organizations, activities |

### Analytics
| API | Key | Actions |
|-----|-----|---------|
| Google Analytics 4 | `ga4` | report, realtime, audiences |
| Search Console | `search_console` | performance, sitemaps, inspect_url |

### Google Suite
| API | Key | Actions |
|-----|-----|---------|
| Gmail | `gmail` | list, read, send, search |
| Google Calendar | `calendar` | events, create_event, update_event |
| Google Drive | `drive` | list, download, upload, search |
| Google Sheets | `sheets` | read, write, append |

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid request (missing required fields) |
| 401 | Authentication failed (invalid API key) |
| 404 | Unknown API or action |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | Upstream API error |
| 504 | Upstream API timeout |
