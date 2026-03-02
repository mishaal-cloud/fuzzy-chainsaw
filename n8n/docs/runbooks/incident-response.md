# Incident Response Runbook

**Version:** 1.0.0
**Last Updated:** 2026-03-02
**Instance:** https://mmurawala.app.n8n.cloud

---

## Table of Contents

1. [Alert Triage](#alert-triage)
2. [Severity Classification](#severity-classification)
3. [Common Failure Scenarios](#common-failure-scenarios)
4. [Escalation Procedures](#escalation-procedures)
5. [Recovery Steps](#recovery-steps)
6. [Post-Incident Review](#post-incident-review)
7. [Contact Directory](#contact-directory)

---

## Alert Triage

When you receive an alert (via Slack `#incidents` channel or PagerDuty), follow this process:

### Step 1: Acknowledge the Alert

- Acknowledge the alert in PagerDuty or respond in the Slack thread within **5 minutes**
- Add a reaction (eyes emoji) to the Slack alert to signal you are investigating
- Post: "Investigating -- [your name]"

### Step 2: Identify the Source

Check the alert message for:
- **API affected**: Which API or gateway component is failing?
- **Error type**: Authentication, rate limit, timeout, or internal error?
- **Frequency**: One-off or recurring pattern?
- **Duration**: When did the issue start?

### Step 3: Classify Severity

Use the table below to determine severity and response requirements.

---

## Severity Classification

| Severity | Criteria | Response SLA | Who Responds |
|----------|----------|-------------|--------------|
| **P1 - Critical** | All gateway endpoints down, or multiple APIs failing simultaneously | 15 minutes | On-call engineer + platform team lead |
| **P2 - High** | Single domain gateway down (e.g., all CRM APIs failing) | 30 minutes | On-call engineer |
| **P3 - Medium** | Single API failing (e.g., HubSpot returning errors) | 4 hours | On-call engineer (business hours) |
| **P4 - Low** | Degraded performance, elevated latency, non-critical warnings | Next business day | Platform team |
| **P5 - Info** | Informational alerts, metric anomalies | Review in daily summary | Platform team |

### Severity Decision Tree

```
Is the entire gateway unreachable?
  YES --> P1 Critical
  NO  --> Are multiple APIs in different categories failing?
            YES --> P1 Critical
            NO  --> Is an entire domain gateway down (all CRM, all Ads)?
                      YES --> P2 High
                      NO  --> Is a single API failing?
                                YES --> P3 Medium
                                NO  --> Is performance degraded?
                                          YES --> P4 Low
                                          NO  --> P5 Info
```

---

## Common Failure Scenarios

### Scenario 1: API Authentication Failure

**Symptoms:**
- Error code: `AUTH_FAILED`
- HTTP status: 401 from upstream API
- Alert: "Authentication failure for [API_NAME]"

**Root Causes:**
- OAuth2 token expired and refresh failed
- API key rotated on provider side without updating n8n
- Permission scopes changed or revoked

**Resolution Steps:**

1. Identify the failing API from the alert details
2. Check the credential status:
   ```
   GET https://mmurawala.app.n8n.cloud/webhook/health-check?api=<api_name>
   ```
3. Go to n8n Credentials UI: `https://mmurawala.app.n8n.cloud` > Credentials
4. Find the credential (naming convention: `PROD_{SERVICE}_{TYPE}`)
5. For OAuth2 credentials:
   - Click "Reconnect" to re-authenticate
   - Complete the OAuth flow in the popup
   - Save the credential
6. For API key credentials:
   - Go to the provider's dashboard and generate a new key
   - Update the key in n8n Credentials UI
   - Save the credential
7. Verify connectivity:
   ```bash
   curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your-key" \
     -d '{ "apis": ["<api_name>"], "test_level": "connectivity" }'
   ```
8. Update `config/credential-inventory.json` with the rotation date

### Scenario 2: Rate Limit Exceeded

**Symptoms:**
- Error code: `RATE_LIMITED`
- HTTP status: 429
- Alert: "Rate limit exceeded for [API_NAME]"
- `Retry-After` header present in responses

**Root Causes:**
- Burst of requests from one or more AI agents
- Runaway workflow making excessive calls
- Rate limit configured too aggressively

**Resolution Steps:**

1. Identify which API and client are hitting limits:
   - Check n8n execution logs for the affected workflow
   - Look for patterns in request frequency
2. Check for runaway workflows:
   - Go to `https://mmurawala.app.n8n.cloud` > Executions
   - Filter by the domain gateway workflow
   - Look for unusual execution counts
   - Deactivate any runaway workflows immediately
3. If legitimate traffic:
   - Review `config/rate-limits.json` for the API
   - Consider increasing the limit if within provider's actual quota
   - Implement request batching for the calling client
4. If API provider is enforcing lower limits:
   - Contact the API provider to increase quota
   - Reduce the configured limit in `rate-limits.json` to match
5. Verify recovery:
   - Wait for the rate limit window to reset
   - Run a test request to confirm

### Scenario 3: API Timeout

**Symptoms:**
- Error code: `TIMEOUT`
- HTTP status: 504
- Alert: "Timeout waiting for [API_NAME]"
- Response time exceeds configured `timeout_ms`

**Root Causes:**
- Upstream API is slow or experiencing outage
- Network connectivity issues
- Request too complex (e.g., large data export)

**Resolution Steps:**

1. Check the upstream API status page:
   - Google: https://www.google.com/appsstatus
   - HubSpot: https://status.hubspot.com
   - Salesforce: https://status.salesforce.com
   - Slack: https://status.slack.com
   - Meta: https://metastatus.com
   - Stripe: https://status.stripe.com
2. Verify connectivity from the gateway:
   ```bash
   curl -s "https://mmurawala.app.n8n.cloud/webhook/health-check?api=<api_name>&detailed=true" \
     -H "X-API-KEY: your-key" | jq .
   ```
3. If the upstream API is down:
   - There is nothing to do but wait for recovery
   - Post status update in `#incidents` Slack channel
   - Set the API status to "known issue" in monitoring
4. If the API is up but slow:
   - Increase timeout in the domain gateway workflow (temporarily)
   - Check if the specific action requires more time (e.g., large reports)
   - Consider adding `options.timeout_ms` override in the request
5. If network issue:
   - Check n8n Cloud status: contact n8n support
   - Verify no proxy or firewall changes

### Scenario 4: Gateway Workflow Down

**Symptoms:**
- No response from webhook endpoints (connection refused or 502)
- Webhooks return generic n8n error page
- Health check endpoint not responding

**Root Causes:**
- n8n workflow deactivated (manually or due to error threshold)
- n8n Cloud instance experiencing issues
- Workflow corrupted or has configuration errors

**Resolution Steps:**

1. Check if the n8n instance is accessible:
   - Navigate to `https://mmurawala.app.n8n.cloud` in a browser
   - If inaccessible, this is an n8n Cloud infrastructure issue (escalate to P1)
2. Check workflow status via n8n API:
   ```bash
   curl -s https://mmurawala.app.n8n.cloud/api/v1/workflows \
     -H "X-N8N-API-KEY: your-n8n-api-key" | jq '.data[] | {id, name, active}'
   ```
3. Identify deactivated workflows and reactivate:
   ```bash
   curl -X POST https://mmurawala.app.n8n.cloud/api/v1/workflows/<workflow_id>/activate \
     -H "X-N8N-API-KEY: your-n8n-api-key"
   ```
4. Check recent execution errors:
   - Go to `https://mmurawala.app.n8n.cloud` > Executions
   - Filter for failed executions
   - Review error messages for root cause
5. If workflow is corrupted:
   - Re-deploy from the workflow JSON files:
     ```bash
     ./n8n/deploy-to-n8n.sh https://mmurawala.app.n8n.cloud YOUR_API_KEY
     ```
6. Verify recovery:
   ```bash
   curl -s https://mmurawala.app.n8n.cloud/webhook/health-check \
     -H "X-API-KEY: your-key" | jq .
   ```

### Scenario 5: Circuit Breaker Open

**Symptoms:**
- Requests to a specific API immediately rejected
- Error message indicates circuit breaker is open
- Rapid failures before the breaker opened

**Root Causes:**
- 5+ consecutive failures to the upstream API
- Upstream API experiencing sustained outage

**Resolution Steps:**

1. The circuit breaker opens after 5 consecutive failures
2. It stays open for 60 seconds (requests fail immediately during this period)
3. After 60 seconds, it enters half-open state (allows 3 test requests)
4. If test requests succeed, the circuit breaker closes (normal operation resumes)
5. If test requests fail, the circuit breaker re-opens for another 60 seconds
6. Check the upstream API status page to determine if the issue is external
7. Once the upstream API recovers, the circuit breaker will auto-recover

### Scenario 6: Request Queue Overflow

**Symptoms:**
- Requests rejected with queue full error
- High latency on all requests
- Alert: "Request queue capacity exceeded"

**Root Causes:**
- Sustained high traffic exceeding gateway capacity
- Slow upstream APIs causing queue backlog
- Burst of requests from multiple AI agents simultaneously

**Resolution Steps:**

1. Check current queue status in monitoring dashboard
2. Identify which APIs or clients are generating the most traffic
3. Temporary mitigation:
   - Reduce `global.queue_max_size` to reject overflow sooner
   - Reduce `global.queue_timeout_seconds` to free stuck requests
4. Long-term fixes:
   - Implement client-side throttling
   - Add caching for frequently requested data
   - Consider scaling the n8n instance

---

## Escalation Procedures

### When to Escalate

Escalate when:
- You cannot resolve within the SLA for the severity level
- The issue affects multiple teams or customers
- The root cause requires access you do not have
- The issue involves credential or security concerns

### Escalation Path

```
Level 1: On-call engineer
    |
    v (if unresolved within SLA, or needs higher access)
Level 2: Platform team lead
    |
    v (if infrastructure or n8n platform issue)
Level 3: n8n Cloud support + Engineering manager
    |
    v (if security incident)
Level 4: Security team + CTO
```

### Escalation Communication Template

Post this in `#incidents` Slack channel when escalating:

```
ESCALATION: [P1/P2/P3] - [Brief description]

Affected: [API name / Component]
Started: [Timestamp]
Duration: [How long so far]
Impact: [What is broken for users]
Investigated:
  - [Step 1 taken]
  - [Step 2 taken]
  - [What was found]
Blocked on: [Why you need to escalate]
Tagging: @[escalation target]
```

---

## Recovery Steps

### After Any Incident

1. **Verify the fix**: Run targeted tests
   ```bash
   curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your-key" \
     -d '{ "apis": ["<affected_api>"], "test_level": "basic" }'
   ```

2. **Monitor for recurrence**: Watch the `#incidents` channel and execution logs for 30 minutes after resolution

3. **Run full health check**:
   ```bash
   curl -s "https://mmurawala.app.n8n.cloud/webhook/health-check?detailed=true" \
     -H "X-API-KEY: your-key" | jq .
   ```

4. **Wait for smoke test**: The hourly smoke test workflow will run and confirm system stability

5. **Update status**: Post resolution in `#incidents` channel:
   ```
   RESOLVED: [Brief description]
   Root cause: [What happened]
   Fix: [What was done]
   Duration: [Total outage/degradation time]
   Follow-up: [Any remaining actions]
   ```

---

## Post-Incident Review

For P1 and P2 incidents, conduct a post-incident review within 48 hours.

### Review Template

```
# Post-Incident Review

Date: [Date]
Severity: [P1/P2]
Duration: [Start time - End time]

## Timeline
- [HH:MM] Alert triggered
- [HH:MM] Investigation started
- [HH:MM] Root cause identified
- [HH:MM] Fix applied
- [HH:MM] Recovery confirmed

## Root Cause
[Detailed description of what went wrong]

## Impact
- APIs affected: [list]
- Requests failed: [count]
- Duration of impact: [time]

## What Went Well
- [Positive aspects of the response]

## What Could Be Improved
- [Areas for improvement]

## Action Items
- [ ] [Action 1] - Owner: [Name] - Due: [Date]
- [ ] [Action 2] - Owner: [Name] - Due: [Date]
```

### Review Participants
- On-call engineer who handled the incident
- Platform team lead
- Credential owner (if credential-related)
- Any escalation contacts who were involved

---

## Contact Directory

| Role | Team | Slack Channel | Escalation |
|------|------|--------------|------------|
| On-call engineer | Platform | `#incidents` | First responder |
| Platform team lead | Platform | `#platform-team` | L2 escalation |
| Marketing credential owner | Marketing | `#marketing-ops` | Ad API issues |
| Sales credential owner | Sales | `#sales-ops` | CRM API issues |
| Analytics credential owner | Analytics | `#analytics-team` | Analytics API issues |
| Engineering credential owner | Engineering | `#engineering` | Project mgmt API issues |
| n8n Cloud support | External | support@n8n.io | Platform infrastructure |
| Security team | Security | `#security` | Security incidents |

### Useful Links

| Resource | URL |
|----------|-----|
| n8n Instance | https://mmurawala.app.n8n.cloud |
| n8n Executions | https://mmurawala.app.n8n.cloud/executions |
| n8n Credentials | https://mmurawala.app.n8n.cloud/credentials |
| Health Check | https://mmurawala.app.n8n.cloud/webhook/health-check |
| API Registry | `config/api-registry.json` |
| Rate Limits Config | `config/rate-limits.json` |
| Credential Inventory | `config/credential-inventory.json` |
