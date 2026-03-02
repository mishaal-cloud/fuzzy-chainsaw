# Incident Response Runbook

## Alert Triage

When you receive an alert (Slack or PagerDuty):

### 1. Identify Severity
| Severity | Action | SLA |
|----------|--------|-----|
| Critical | Immediate response, all hands | 15 minutes |
| Warning | Investigate within business hours | 4 hours |
| Info | Review in daily summary | Next business day |

### 2. Common Failure Scenarios

#### API Authentication Failure
**Symptom:** `auth_error` classification, 401 responses
**Cause:** Expired OAuth2 token or rotated API key
**Fix:**
1. Check which API is failing in the alert details
2. Go to n8n Credentials UI
3. Re-authenticate the OAuth2 credential or update the API key
4. Test by running: `POST /webhook/run-tests`

#### Rate Limit Exceeded
**Symptom:** `rate_limit` classification, 429 responses
**Cause:** Too many API calls in time window
**Fix:**
1. Check rate limit config in `config/rate-limits.json`
2. Reduce request frequency from the calling AI
3. If persistent, increase quota with the API provider
4. Check for runaway workflows making excessive calls

#### API Timeout
**Symptom:** `timeout` classification, no response after 30s
**Cause:** Upstream API is slow or down
**Fix:**
1. Check API status page (e.g., status.hubspot.com)
2. Verify with health check: `GET /webhook/health-check`
3. If API is down, wait for recovery
4. If persistent, increase timeout in the domain gateway workflow

#### Gateway Workflow Down
**Symptom:** 502 or no response from webhook endpoints
**Cause:** n8n instance issue or workflow deactivated
**Fix:**
1. Check n8n instance status at https://mmurawala.app.n8n.cloud
2. Verify workflows are active: `GET /api/v1/workflows?active=true`
3. If deactivated, reactivate: `POST /api/v1/workflows/{id}/activate`
4. Check n8n execution logs for errors

### 3. Escalation

If you cannot resolve within the SLA:
1. Post in #incidents Slack channel with: severity, API affected, error message, steps tried
2. Tag the credential owner (see `config/credential-inventory.json`)
3. For n8n platform issues, contact n8n support

### 4. Post-Incident

After resolving:
1. Run smoke tests: the hourly smoke test will verify recovery
2. Run full test suite: `POST /webhook/run-tests`
3. Check daily summary next morning for any lingering issues
4. Update runbooks if a new failure pattern was discovered
