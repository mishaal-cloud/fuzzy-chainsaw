# Runbook: Adding a New API to the Gateway

**Version:** 2.0.0
**Last Updated:** 2026-03-02
**Instance:** https://mmurawala.app.n8n.cloud

---

## Overview

This runbook provides step-by-step instructions for adding a new API to the n8n Enterprise API Gateway. Follow all steps in order and verify at each stage before proceeding.

**Estimated time:** 30-60 minutes depending on API complexity.

---

## Prerequisites

Before starting, ensure you have:

- [ ] Access to the n8n instance: https://mmurawala.app.n8n.cloud
- [ ] API credentials for the new service (API key, OAuth2 client ID/secret, etc.)
- [ ] API documentation for the new service (endpoints, auth, rate limits)
- [ ] Understanding of the API's rate limits and quotas
- [ ] Access to this repository to update configuration files

---

## Step 1: Update API Registry

Edit `n8n/config/api-registry.json` and add the new API under the appropriate category.

### 1.1 Choose the Category

| Category | When to Use | Examples |
|----------|------------|---------|
| `marketing_ads` | Advertising platforms | Google Ads, Meta Ads, LinkedIn Ads |
| `crm` | Customer relationship management | HubSpot, Salesforce, Pipedrive |
| `analytics` | Analytics and tracking | GA4, Mixpanel, Hotjar |
| `google_suite` | Google Workspace tools | Gmail, Drive, Sheets |
| `communication` | Messaging and email | Slack, SendGrid, Twilio |
| `project_management` | Task and project tools | Jira, Notion, Trello |
| `ecommerce` | Commerce platforms | Shopify, Stripe |
| `ai_ml` | AI and ML services | OpenAI, Anthropic |
| `data_storage` | Databases and storage | Airtable, Supabase |

If no category fits, create a new one. Keep category names lowercase with underscores.

### 1.2 Add the API Entry

Add a new entry to the appropriate category in `api-registry.json`:

```json
{
  "new_api_name": {
    "name": "Human-Readable API Name",
    "base_url": "https://api.example.com/v1",
    "auth_type": "oauth2",
    "credential_key": "PROD_NEWAPI_OAUTH2",
    "rate_limits": {
      "requests_per_minute": 60,
      "daily_quota": 50000
    },
    "required_params": ["account_id"],
    "actions": ["list", "create", "update", "delete"],
    "documentation": "https://docs.example.com/api",
    "health_check_endpoint": "/me",
    "timeout_ms": 30000
  }
}
```

**Field Reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Human-readable display name |
| `base_url` | Yes | API base URL (include version number) |
| `auth_type` | Yes | One of: `oauth2`, `api_key`, `app_token`, `webhook` |
| `credential_key` | Yes | Credential name following `{ENV}_{SERVICE}_{TYPE}` convention |
| `rate_limits` | Yes | Rate limits from the API's documentation |
| `required_params` | Yes | Parameters required for all actions (can be empty array `[]`) |
| `actions` | Yes | List of supported action identifiers |
| `documentation` | Recommended | Link to the API's official documentation |
| `health_check_endpoint` | Recommended | Lightweight endpoint for health checks (e.g., `/me`, `/status`) |
| `timeout_ms` | Recommended | Default timeout for this API (default: 30000) |

### 1.3 Update Metadata

Update the `metadata.total_apis` count at the bottom of `api-registry.json` to reflect the new total.

---

## Step 2: Add Rate Limit Configuration

Edit `n8n/config/rate-limits.json` and add a new entry under the `apis` section:

```json
{
  "new_api_name": {
    "requests_per_minute": 60,
    "daily_quota": 50000,
    "burst_allowance": 5,
    "retry_after_seconds": 60,
    "throttle_strategy": "sliding_window"
  }
}
```

### Choosing a Throttle Strategy

| Strategy | Best For | Description |
|----------|---------|-------------|
| `sliding_window` | APIs with per-minute limits | Rolling window for smooth rate limiting |
| `token_bucket` | APIs with per-second limits that allow bursts | Allows bursts up to bucket capacity |
| `fixed_window` | APIs with daily limits only | Resets at fixed intervals |
| `leaky_bucket` | APIs that need very steady request rates | Processes at fixed rate, queues excess |

### Setting Burst Allowance

Set `burst_allowance` to approximately 10% of the per-minute or per-second limit. This allows short bursts without triggering throttling.

---

## Step 3: Add Credentials

### 3.1 Create Credential in n8n

1. Go to https://mmurawala.app.n8n.cloud > **Credentials**
2. Click **Add Credential**
3. Select the credential type:
   - For well-known services: select the built-in credential type (e.g., "HubSpot API")
   - For generic APIs: use "Header Auth", "HTTP Request", or "OAuth2 API"
4. Name it following the convention: `PROD_{SERVICE}_{TYPE}`
   - Examples: `PROD_NEWAPI_OAUTH2`, `PROD_NEWAPI_KEY`
5. Enter the credentials:
   - For OAuth2: Client ID, Client Secret, Authorization URL, Token URL, Scopes
   - For API Key: The API key value
   - For App Token: The token value
6. **Save** and **Test** the credential

### 3.2 Update Credential Inventory

Edit `n8n/config/credential-inventory.json` and add a new entry to the `credentials` array:

```json
{
  "name": "PROD_NEWAPI_OAUTH2",
  "service": "New API Name",
  "type": "oauth2",
  "environment": "production",
  "category": "category_name",
  "owner": "team_name",
  "rotation_days": 90,
  "last_rotated": null,
  "scopes": ["read", "write"],
  "notes": "Specific setup notes for this credential."
}
```

**Owner assignments by category:**

| Category | Default Owner |
|----------|--------------|
| `marketing_ads` | `marketing_team` |
| `crm` | `sales_team` |
| `analytics` | `analytics_team` |
| `google_suite` | `platform_team` |
| `communication` | `platform_team` |
| `project_management` | `engineering_team` |
| `ecommerce` | `ecommerce_team` |
| `ai_ml` | `platform_team` |
| `data_storage` | `engineering_team` |

---

## Step 4: Add to Domain Gateway Workflow

### 4.1 Open the Domain Gateway in n8n

Open the appropriate domain gateway workflow in the n8n editor at https://mmurawala.app.n8n.cloud:

| Category | Workflow Name |
|----------|--------------|
| `marketing_ads` | `marketing-ads-gateway` |
| `crm` | `crm-gateway` |
| `analytics` | `analytics-gateway` |
| `google_suite` | `google-suite-gateway` |
| `communication` | `communication-gateway` |
| `project_management` | `project-mgmt-gateway` |
| `ecommerce` | `ecommerce-gateway` |
| `ai_ml` | `ai-ml-gateway` |
| `data_storage` | `data-storage-gateway` |

### 4.2 Add to the Routing Switch Node

In the "Build API Request" Code node, add the new API configuration:

```javascript
const apiConfigs = {
  // ... existing APIs ...
  new_api_name: {
    base_url: 'https://api.example.com/v1',
    endpoints: {
      list: { method: 'GET', path: '/resources', query: { limit: params.limit || 50 } },
      create: { method: 'POST', path: '/resources', body: params },
      update: { method: 'PUT', path: `/resources/${params.id}`, body: params },
      delete: { method: 'DELETE', path: `/resources/${params.id}` }
    }
  }
};
```

### 4.3 Update Main Gateway Router

In the `main-api-gateway` workflow, add the API to the routing table in the "Route Request" Code node:

```javascript
const routingTable = {
  // ... existing APIs ...
  new_api_name: 'category_name'
};
```

### 4.4 Build the API Call Logic

For each action, ensure the nodes:

1. **Extract parameters** from `$json.params`
2. **Build the HTTP request** using the API's base URL and action-specific endpoint
3. **Add authentication** using the credential created in Step 3
4. **Handle the response** and normalize it into the standard envelope

### 4.5 Normalize the Response

Ensure the response matches the standard gateway envelope:

```json
{
  "success": true,
  "data": { },
  "metadata": {
    "request_id": "{{ $json.request_id }}",
    "api": "new_api_name",
    "action": "{{ $json.action }}",
    "duration_ms": "{{ Date.now() - $json.start_time }}",
    "cached": false
  }
}
```

---

## Step 5: Update API Discovery Catalog

The API Discovery workflow reads from `api-registry.json`, so updating the registry (Step 1) should automatically make the new API appear in discovery results.

If the discovery workflow uses a hardcoded catalog in a Code node, update the catalog there as well.

Verify by calling the discovery endpoint:

```bash
curl -s "https://mmurawala.app.n8n.cloud/webhook/api-discovery?api=new_api_name" \
  -H "X-API-KEY: your-key" | jq .
```

---

## Step 6: Update Validation Schema

Edit `n8n/schemas/request-validation.json`:

1. Add the new API name to the `api` enum:
   ```json
   "api": {
     "type": "string",
     "enum": [
       "google_ads",
       "meta_ads",
       "...",
       "new_api_name"
     ]
   }
   ```

2. If the API has required params with specific formats, add them to `params.properties`:
   ```json
   "params": {
     "properties": {
       "account_id": {
         "type": "string",
         "description": "New API account ID (required for new_api_name API)."
       }
     }
   }
   ```

---

## Step 7: Update OpenAPI Specification

Edit `n8n/schemas/openapi-spec.yaml`:

1. Add the new API to the `GatewayRequest.properties.api.enum` list
2. Add an example request in the `/api-gateway` path `examples` section:
   ```yaml
   new_api_example:
     summary: List resources from New API
     value:
       client: claude-desktop
       api: new_api_name
       action: list
       params:
         account_id: "12345"
         limit: 10
   ```
3. Add the new API to the description list of supported APIs in the `/api-gateway` path

---

## Step 8: Add Test Cases

### 8.1 Add to Test Runner Workflow

Open the `test-runner` workflow in n8n and add test cases for the new API in the "Define Test Cases" Code node:

```javascript
// Add these test cases to the test array
{
  test_name: "new_api_name - Authentication",
  request: {
    client: "test-runner",
    api: "new_api_name",
    action: "list",
    params: { limit: 1 }
  },
  expected: { success: true }
},
{
  test_name: "new_api_name - Invalid Action",
  request: {
    client: "test-runner",
    api: "new_api_name",
    action: "nonexistent_action",
    params: {}
  },
  expected: { success: false, error_code: "INVALID_ACTION" }
}
```

### 8.2 Run the Tests

```bash
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{ "apis": ["new_api_name"], "test_level": "basic" }'
```

Verify all tests pass before proceeding.

---

## Step 9: Deploy and Verify

### 9.1 Deploy Updated Workflows

```bash
# Redeploy all workflows
./n8n/deploy-to-n8n.sh https://mmurawala.app.n8n.cloud YOUR_API_KEY
```

Or manually activate the updated workflows in the n8n editor.

### 9.2 Run Full Verification

```bash
# 1. Check discovery
curl -s "https://mmurawala.app.n8n.cloud/webhook/api-discovery?api=new_api_name" \
  -H "X-API-KEY: your-key" | jq '.data'

# 2. Check health
curl -s "https://mmurawala.app.n8n.cloud/webhook/health-check?api=new_api_name" \
  -H "X-API-KEY: your-key" | jq '.status'

# 3. Test a basic action
curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{
    "client": "manual-test",
    "api": "new_api_name",
    "action": "list",
    "params": { "limit": 1 }
  }' | jq '.success'

# 4. Run full test suite
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{ "apis": ["new_api_name"], "test_level": "basic" }' | jq '.summary'
```

---

## Step 10: Update Documentation

### 10.1 API Reference

Edit `n8n/docs/api-reference.md`:

1. Add the new API to the appropriate category table in the "Available APIs" section
2. Add a curl example if the API has unique parameters or actions

### 10.2 Architecture Docs

Edit `n8n/docs/architecture.md`:

1. Update the External API Layer in the architecture diagram
2. Update the domain gateway table if changing gateway assignments
3. Update API counts if mentioned

### 10.3 Update CLAUDE.md

If a `CLAUDE.md` file exists at the project root, update it with any relevant information about the new API.

---

## Verification Checklist

Run through this checklist before considering the integration complete:

- [ ] **API Registry**: New API appears in `config/api-registry.json` with all fields
- [ ] **Rate Limits**: Rate limits configured in `config/rate-limits.json`
- [ ] **Credentials**: Credential created in n8n and documented in `config/credential-inventory.json`
- [ ] **Discovery**: `GET /api-discovery?api=new_api_name` returns the new API
- [ ] **Gateway routing**: Request routes to the correct domain gateway
- [ ] **Actions work**: Each action returns the expected response
- [ ] **Error handling**: Invalid actions return `INVALID_ACTION` error code
- [ ] **Required params**: Missing required params return `MISSING_PARAMS` error code
- [ ] **Rate limiting**: Rate limits are enforced correctly
- [ ] **Health check**: `GET /health-check?api=new_api_name` returns healthy
- [ ] **Tests pass**: `POST /run-tests` with the new API passes all tests
- [ ] **Schema updated**: `schemas/request-validation.json` includes the new API in enum
- [ ] **OpenAPI updated**: `schemas/openapi-spec.yaml` includes the new API
- [ ] **Docs updated**: `docs/api-reference.md` and `docs/architecture.md` updated

---

## Rollback Procedure

If the new API causes issues after deployment:

1. **Disable the branch** in the domain gateway Switch node (do not delete it)
2. **Remove from discovery** by commenting out the entry in the discovery workflow
3. **Notify affected teams** in Slack `#incidents` channel
4. **Investigate and fix** before re-enabling
5. The gateway will return `UNKNOWN_API` for requests to the disabled API, which is a clean failure mode for AI agents

---

## Files Modified Summary

| File | Change |
|------|--------|
| `n8n/config/api-registry.json` | Add new API entry, update total count |
| `n8n/config/rate-limits.json` | Add rate limit configuration |
| `n8n/config/credential-inventory.json` | Add credential documentation |
| `n8n/schemas/request-validation.json` | Add to API enum |
| `n8n/schemas/openapi-spec.yaml` | Add to enum, description, and examples |
| `n8n/docs/api-reference.md` | Add to Available APIs table |
| `n8n/docs/architecture.md` | Update API count and diagrams if needed |
| Domain gateway workflow (in n8n UI) | Add Switch branch and action handlers |
| Main gateway workflow (in n8n UI) | Add to routing table |
| Test runner workflow (in n8n UI) | Add test cases |
| API discovery workflow (in n8n UI) | Verify auto-discovery or update catalog |
