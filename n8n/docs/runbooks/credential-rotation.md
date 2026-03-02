# Runbook: Credential Rotation Procedures

**Version:** 2.0.0
**Last Updated:** 2026-03-02
**Instance:** https://mmurawala.app.n8n.cloud

---

## Table of Contents

1. [Rotation Schedule](#rotation-schedule)
2. [Automated Alerts](#automated-alerts)
3. [Rotation Procedures by Auth Type](#rotation-procedures-by-auth-type)
4. [Emergency Credential Rotation](#emergency-credential-rotation)
5. [Post-Rotation Verification](#post-rotation-verification)
6. [Quarterly Audit Process](#quarterly-audit-process)
7. [Credential Naming Convention](#credential-naming-convention)
8. [Provider-Specific Notes](#provider-specific-notes)

---

## Rotation Schedule

All credentials follow a mandatory rotation schedule to maintain security.

| Auth Type | Rotation Period | Auto-Refresh | Alert Threshold |
|-----------|----------------|--------------|-----------------|
| OAuth2 | 90 days | Yes (token refresh) | 14 days before expiry |
| API Key | 90 days | No (manual) | 14 days before expiry |
| App Token | 90 days | No (manual) | 14 days before expiry |
| Webhook URL | 365 days | No (manual) | 30 days before expiry |
| Gateway API Key | 180 days | No (manual) | 14 days before expiry |

### Understanding OAuth2 Auto-Refresh

OAuth2 credentials have two components:
- **Access token**: Short-lived (usually 1 hour). Automatically refreshed by n8n using the refresh token.
- **Refresh token**: Long-lived (varies by provider). Must be manually rotated every 90 days by re-authenticating.

Even though access tokens auto-refresh, the underlying refresh token can expire or be revoked. The 90-day rotation ensures the refresh token stays valid.

---

## Automated Alerts

The **Credential Rotator** workflow runs daily at 8:00 AM UTC and checks all credentials against the rotation schedule in `config/credential-inventory.json`.

### Alert Levels

| Alert | Condition | Action Required |
|-------|-----------|----------------|
| `EXPIRING_SOON` | Credential expires within 14 days (or 30 days for webhooks) | Plan rotation |
| `EXPIRED` | Credential has passed its rotation date | Rotate immediately |
| `NEVER_ROTATED` | `last_rotated` is null | Rotate and set initial date |

### Alert Destination

Alerts are sent to:
- Slack channel: `#credential-alerts`
- Tagged: credential owner from `credential-inventory.json`

### Alert Format

```
:warning: CREDENTIAL ROTATION ALERT

Status: EXPIRING_SOON
Credential: PROD_GOOGLE_ADS_OAUTH2
Service: Google Ads
Owner: marketing_team
Last Rotated: 2025-12-05
Expires In: 7 days
Action: Re-authenticate in n8n Credentials UI

Runbook: docs/runbooks/credential-rotation.md
```

---

## Rotation Procedures by Auth Type

### OAuth2 Credentials

**Applies to:** Google Ads, Meta Ads, LinkedIn Ads, Twitter Ads, Salesforce, GA4, Search Console, Gmail, Calendar, Drive, Sheets, Slack, MS Teams, Asana

**Procedure:**

1. **Prepare**: Identify the credential to rotate
   ```
   Credential: PROD_{SERVICE}_OAUTH2
   Location: https://mmurawala.app.n8n.cloud > Credentials
   ```

2. **Re-authenticate**:
   - Navigate to https://mmurawala.app.n8n.cloud
   - Go to **Credentials** in the left sidebar
   - Find the credential by name (e.g., `PROD_GOOGLE_ADS_OAUTH2`)
   - Click on the credential to open it
   - Click **"Reconnect"** or **"Re-authenticate"**
   - Complete the OAuth2 authorization flow in the browser popup:
     - Sign in to the service (Google, Meta, LinkedIn, etc.)
     - Grant the requested permissions
     - Wait for the redirect back to n8n
   - n8n automatically stores the new access token and refresh token
   - Click **Save**

3. **Verify connectivity**:
   ```bash
   # Test the specific API
   curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your-key" \
     -d '{ "apis": ["<api_name>"], "test_level": "connectivity" }'
   ```

4. **Update inventory**:
   - Edit `config/credential-inventory.json`
   - Set `last_rotated` to today's date (YYYY-MM-DD format)
   - Commit the change

5. **Confirm**: Verify the next smoke test passes (runs hourly)

**Important notes for OAuth2:**
- Do NOT create a new credential -- always re-authenticate the existing one
- The credential name in n8n must stay the same so workflows continue to reference it
- If the OAuth app's scopes have changed, you may need to re-consent

---

### API Key Credentials

**Applies to:** TikTok Ads, Pipedrive, Mixpanel, Hotjar, SendGrid, Twilio, Jira, Notion, Trello, Shopify, Stripe, OpenAI, Anthropic, Airtable, Supabase

**Procedure:**

1. **Generate new key** at the provider's dashboard:

   | Provider | Where to Generate |
   |----------|------------------|
   | TikTok Ads | TikTok Business Center > Settings > API |
   | Pipedrive | Settings > Personal Preferences > API |
   | Mixpanel | Project Settings > Service Accounts |
   | Hotjar | Account Settings > API Key |
   | SendGrid | Settings > API Keys |
   | Twilio | Console > Account > API Keys |
   | Jira | Atlassian Account > Security > API Tokens |
   | Notion | My Integrations > Your Integration > Secrets |
   | Trello | Developer API Key page |
   | Shopify | Admin > Apps > Custom App > API Credentials |
   | Stripe | Dashboard > Developers > API Keys |
   | OpenAI | Platform > API Keys |
   | Anthropic | Console > API Keys |
   | Airtable | Developer Hub > Personal Access Tokens |
   | Supabase | Project Settings > API > Service Role Key |

2. **Update in n8n** (do NOT delete old key yet):
   - Navigate to https://mmurawala.app.n8n.cloud > Credentials
   - Find the credential (e.g., `PROD_SENDGRID_KEY`)
   - Update the API key value with the new key
   - Click **Save**

3. **Verify connectivity**:
   ```bash
   curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your-key" \
     -d '{ "apis": ["<api_name>"], "test_level": "basic" }'
   ```

4. **Wait 24 hours**: Keep the old key active for 24 hours as a safety net
   - Monitor for any errors related to the API in `#incidents` and execution logs

5. **Revoke old key**: After 24 hours with no errors:
   - Go back to the provider's dashboard
   - Delete/revoke the old API key
   - This ensures no other systems are still using the old key

6. **Update inventory**:
   - Edit `config/credential-inventory.json`
   - Set `last_rotated` to today's date
   - Commit the change

**Important notes for API keys:**
- Some providers (Stripe, OpenAI) let you create restricted keys -- always use minimum required permissions
- For Twilio, you need to update both Account SID and Auth Token
- For Jira, the "key" is actually email + API token used as basic auth

---

### App Token Credentials

**Applies to:** HubSpot

**Procedure:**

1. **Generate new token**:
   - Go to HubSpot Developer Portal > Your App > Auth
   - Generate a new private app access token
   - Copy the new token (it is only shown once)

2. **Update in n8n**:
   - Navigate to https://mmurawala.app.n8n.cloud > Credentials
   - Find `PROD_HUBSPOT_TOKEN`
   - Update the token value
   - Click **Save**

3. **Verify**:
   ```bash
   curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your-key" \
     -d '{ "apis": ["hubspot"], "test_level": "basic" }'
   ```

4. **Revoke old token**: In HubSpot, revoke the previous private app token

5. **Update inventory**: Set `last_rotated` in `config/credential-inventory.json`

---

### Webhook URL Credentials

**Applies to:** Slack incoming webhooks, internal webhook secrets

**Procedure:**

1. **Create new webhook** at the provider (e.g., Slack > Apps > Incoming Webhooks)

2. **Update all workflows** that reference the webhook URL. Check these workflows:
   - `error-handler` -- Send Slack Alert node
   - `credential-rotator` -- Send Slack Alert node
   - `metrics-collector` -- Alert Threshold Exceeded node
   - `alert-manager` -- Send to Slack node
   - `daily-summary` -- Send to Slack node
   - `smoke-tests` -- Alert on Failure node

3. **Test each workflow**: Trigger a test execution for each updated workflow

4. **Deactivate old webhook**: Remove the old webhook URL from the provider

5. **Update inventory**: Set `last_rotated` in `config/credential-inventory.json`

**Important**: Webhook URLs require coordinated updates across multiple workflows. Schedule this during a maintenance window to avoid missed alerts.

---

### Gateway API Key (Internal)

**Applies to:** `PROD_N8N_GATEWAY_API_KEY` -- the key clients use to authenticate with the gateway

**Procedure:**

1. **Generate a new key**: Create a new secure random key (minimum 32 characters)
   ```bash
   openssl rand -hex 32
   ```

2. **Support both keys temporarily**:
   - Update the gateway authentication workflow to accept both the old and new key
   - This prevents service disruption during the transition

3. **Notify all clients**: Send notification to all AI agent operators and API consumers
   - Provide the new key
   - Set a deadline for migration (e.g., 7 days)

4. **Monitor adoption**: Track which clients have migrated to the new key via execution logs

5. **Remove old key**: After all clients have migrated (or after the deadline):
   - Update the authentication workflow to only accept the new key
   - Revoke/remove the old key

6. **Update inventory**: Set `last_rotated` in `config/credential-inventory.json`

---

## Emergency Credential Rotation

Use this procedure if a credential is compromised (leaked, unauthorized access detected, etc.).

### Immediate Actions (within 15 minutes)

1. **Revoke the compromised credential immediately** at the provider's dashboard
   - This is the highest priority -- stop unauthorized access first
   - Expect service disruption for this API

2. **Assess the scope**:
   - What data could have been accessed?
   - How long was the credential exposed?
   - Were any unauthorized API calls made? (check provider's audit logs)

3. **Generate new credential** at the provider

4. **Update in n8n**:
   - Navigate to https://mmurawala.app.n8n.cloud > Credentials
   - Update the credential with the new value
   - Save immediately

5. **Verify recovery**:
   ```bash
   curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your-key" \
     -d '{ "apis": ["<affected_api>"], "test_level": "connectivity" }'
   ```

### Follow-up Actions (within 24 hours)

6. **Check execution logs**: Review n8n execution logs for any unauthorized API calls made through the gateway

7. **Check provider audit logs**: Review the API provider's audit/activity logs for suspicious activity

8. **Notify stakeholders**:
   - Post in `#incidents` Slack channel
   - Notify the credential owner
   - Notify security team if sensitive data may have been accessed

9. **Document the incident**: Create an incident report including:
   - Timeline of events
   - Scope of exposure
   - Actions taken
   - Preventive measures

10. **Review and harden**:
    - How was the credential exposed? Fix the root cause.
    - Consider reducing credential scopes to minimum required
    - Consider enabling additional security measures (IP allowlisting, etc.)
    - Update `config/credential-inventory.json` with the new rotation date

---

## Post-Rotation Verification

After any credential rotation, perform these verification steps:

### Automated Verification

```bash
# 1. Run connectivity test for the specific API
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{ "apis": ["<api_name>"], "test_level": "connectivity" }'

# 2. Run basic functionality test
curl -X POST https://mmurawala.app.n8n.cloud/webhook/run-tests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-key" \
  -d '{ "apis": ["<api_name>"], "test_level": "basic" }'

# 3. Check health status
curl -s "https://mmurawala.app.n8n.cloud/webhook/health-check?api=<api_name>" \
  -H "X-API-KEY: your-key" | jq .
```

### Manual Verification

1. Execute a real request through the gateway:
   ```bash
   curl -X POST https://mmurawala.app.n8n.cloud/webhook/api-gateway \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your-key" \
     -d '{
       "client": "rotation-test",
       "api": "<api_name>",
       "action": "<read_action>",
       "params": { "limit": 1 }
     }'
   ```

2. Check the n8n execution log for the request -- verify it completed successfully

3. Wait for the next hourly smoke test and confirm it passes

### Update Records

After successful verification:

1. Edit `config/credential-inventory.json`:
   ```json
   {
     "name": "PROD_{SERVICE}_{TYPE}",
     "last_rotated": "2026-03-02"
   }
   ```

2. Commit the change to the repository

---

## Quarterly Audit Process

Every quarter, conduct a full credential audit. The next audit is tracked in `config/credential-inventory.json` under `audit_requirements`.

### Audit Checklist

- [ ] **Verify all credentials are active**: Run `POST /run-tests` with `test_level: connectivity` for all APIs
- [ ] **Check rotation compliance**: Verify all `last_rotated` dates are within the rotation period
- [ ] **Identify unused credentials**: Review n8n execution logs for credentials with zero usage in the past 90 days
- [ ] **Decommission unused credentials**: Revoke and remove any credentials no longer in use
- [ ] **Review access scopes**: For each credential, verify scopes follow least-privilege principle
- [ ] **Confirm owner assignments**: Verify all credential owners in `credential-inventory.json` are current team members
- [ ] **Test failover**: For critical APIs, verify the error handling and alerting works correctly
- [ ] **Update documentation**: Ensure all credential documentation is current

### Audit Report Template

```
# Quarterly Credential Audit Report

Date: YYYY-MM-DD
Auditor: [Name]

## Summary
- Total credentials: [count]
- Compliant: [count]
- Non-compliant: [count]
- Decommissioned: [count]

## Non-Compliant Credentials
| Credential | Issue | Action Required | Owner |
|-----------|-------|-----------------|-------|
| PROD_XYZ_KEY | Overdue rotation (120 days) | Rotate immediately | team_name |

## Decommissioned Credentials
| Credential | Reason | Revoked Date |
|-----------|--------|--------------|

## Scope Review
| Credential | Current Scopes | Recommended Change |
|-----------|---------------|-------------------|

## Action Items
- [ ] [Action] - Owner: [Name] - Due: [Date]
```

### Audit Schedule

| Quarter | Audit Month | Deadline |
|---------|------------|----------|
| Q1 | March | March 31 |
| Q2 | June | June 30 |
| Q3 | September | September 30 |
| Q4 | December | December 31 |

---

## Credential Naming Convention

All credentials follow the pattern: `{ENV}_{SERVICE}_{TYPE}`

| Component | Values | Examples |
|-----------|--------|---------|
| `ENV` | `PROD`, `STAGING`, `DEV` | `PROD` |
| `SERVICE` | Service name in UPPER_SNAKE_CASE | `GOOGLE_ADS`, `HUBSPOT`, `SLACK` |
| `TYPE` | `OAUTH2`, `KEY`, `TOKEN`, `WEBHOOK` | `OAUTH2` |

**Examples:**
- `PROD_GOOGLE_ADS_OAUTH2`
- `PROD_HUBSPOT_TOKEN`
- `PROD_SENDGRID_KEY`
- `PROD_SLACK_OAUTH2`
- `PROD_N8N_GATEWAY_API_KEY`

---

## Provider-Specific Notes

### Google APIs (Ads, GA4, Search Console, Gmail, Calendar, Drive, Sheets)

- All Google APIs share the same OAuth2 app but may use different credentials in n8n
- Refresh tokens can expire if not used for 6 months
- If you see "Token has been expired or revoked", re-authenticate through n8n
- Google Cloud Console: https://console.cloud.google.com > APIs & Services > Credentials

### Meta/Facebook APIs

- Access tokens for Marketing API are short-lived (1-2 hours)
- System user tokens last longer but still need periodic re-authentication
- Check token status: https://developers.facebook.com/tools/debug/accesstoken/
- Business Manager: https://business.facebook.com/settings

### Salesforce

- Connected App OAuth2 tokens can be revoked by Salesforce admins
- After rotation, the `instance_url` may change -- verify it is stored correctly
- Setup: https://login.salesforce.com > Setup > App Manager

### Stripe

- Use restricted API keys with only necessary permissions
- Never use the publishable key for server-side operations
- Dashboard: https://dashboard.stripe.com/apikeys

### OpenAI / Anthropic

- Set spend limits in the provider dashboard to prevent cost overruns
- API keys do not expire automatically but should still be rotated
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

### Slack

- Bot tokens (`xoxb-`) do not expire but should be rotated periodically
- User tokens (`xoxp-`) may expire based on workspace settings
- App management: https://api.slack.com/apps

### HubSpot

- Private app tokens do not expire but can be revoked
- When creating a new private app, ensure all required scopes are selected
- Developer Portal: https://developers.hubspot.com
