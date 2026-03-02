# Adding a New API — Step by Step

## Prerequisites
- API credentials (key, OAuth2, etc.)
- API documentation for endpoints you want to expose
- Access to n8n instance

## Steps

### 1. Update API Registry
Edit `n8n/config/api-registry.json`:
```json
{
  "categories": {
    "your_category": {
      "new_api": {
        "name": "New API Display Name",
        "base_url": "https://api.newservice.com/v1",
        "auth_type": "oauth2",
        "credential_key": "PROD_NEW_API_OAUTH2",
        "rate_limits": { "requests_per_minute": 60, "daily_quota": 10000 },
        "actions": ["list", "create", "update", "delete"]
      }
    }
  }
}
```

### 2. Add to Domain Gateway
Edit the appropriate gateway workflow (e.g., `crm-gateway.json`):

In the "Build API Request" Code node, add the new API config:
```javascript
const apiConfigs = {
  // ... existing APIs ...
  new_api: {
    base_url: 'https://api.newservice.com/v1',
    endpoints: {
      list: { method: 'GET', path: '/resources', query: { limit: params.limit || 50 } },
      create: { method: 'POST', path: '/resources', body: params },
      update: { method: 'PUT', path: `/resources/${params.id}`, body: params },
      delete: { method: 'DELETE', path: `/resources/${params.id}` }
    }
  }
};
```

### 3. Update Main Gateway Router
In `main-api-gateway.json`, add the API to the routing table in the "Route Request" Code node:
```javascript
const routingTable = {
  // ... existing APIs ...
  new_api: 'your_category'
};
```

### 4. Update API Discovery Catalog
In `api-discovery.json`, add the API to the catalog in the "Build API Catalog" Code node under the appropriate category.

### 5. Add Credentials to n8n
1. Go to n8n Credentials UI
2. Create new credential with naming convention: `PROD_NEW_API_OAUTH2`
3. Update `config/credential-inventory.json`

### 6. Update Rate Limits
Edit `n8n/config/rate-limits.json`:
```json
{
  "apis": {
    "new_api": { "requests_per_minute": 60, "daily_quota": 10000 }
  }
}
```

### 7. Add Test Cases
In `test-runner.json`, add test cases for the new API in the "Define Test Cases" Code node.

### 8. Deploy and Test
```bash
# Redeploy updated workflows
./n8n/deploy-to-n8n.sh https://mmurawala.app.n8n.cloud YOUR_API_KEY

# Run tests
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests
```

### 9. Update Documentation
- Update `docs/api-reference.md` with the new API's actions and parameters
- Update CLAUDE.md if needed
