# Credential Rotation Procedures

## Rotation Schedule

| Auth Type | Rotation Period | Auto-Refresh |
|-----------|----------------|--------------|
| OAuth2 | 90 days | Yes (token refresh) |
| API Key | 90 days | No (manual) |
| App Token | 90 days | No (manual) |
| Webhook URL | 365 days | No (manual) |

## Automated Alerts

The Credential Rotator workflow runs daily at 8 AM and alerts via Slack when:
- A credential expires in 7 days or less (`EXPIRING_SOON`)
- A credential has already expired (`EXPIRED`)

## Rotation Steps

### OAuth2 Credentials (Google Ads, Salesforce, GA4, etc.)

1. Go to n8n → Credentials
2. Find the credential (named `PROD_{SERVICE}_OAUTH2`)
3. Click "Re-authenticate" — this triggers the OAuth2 flow
4. Complete the consent screen in the browser
5. n8n automatically stores the new tokens
6. Test: run smoke tests or a manual API call
7. Update `last_rotated` in `config/credential-inventory.json`

### API Key Credentials (HubSpot, Pipedrive, TikTok)

1. Go to the API provider's dashboard
2. Generate a new API key
3. Go to n8n → Credentials
4. Update the credential with the new key
5. **Do NOT delete the old key yet** — wait 24 hours to confirm
6. Test: `POST /webhook/run-tests`
7. After 24 hours with no errors, revoke the old key
8. Update `last_rotated` in `config/credential-inventory.json`

### Slack Webhook URLs

1. Go to Slack → Apps → Incoming Webhooks
2. Create a new webhook URL
3. Update the webhook URL in these workflows:
   - `error-handler.json` — Send Slack Alert node
   - `credential-rotator.json` — Send Slack Alert node
   - `metrics-collector.json` — Alert Threshold Exceeded node
   - `alert-manager.json` — Send to Slack node
   - `daily-summary.json` — Send to Slack node
   - `smoke-tests.json` — Alert on Failure node
4. Redeploy affected workflows
5. Deactivate the old webhook in Slack

## Emergency Rotation

If a credential is compromised:

1. **Immediately** revoke the compromised credential at the provider
2. Generate new credentials
3. Update in n8n Credentials UI
4. Redeploy affected workflows
5. Run full test suite: `POST /webhook/run-tests`
6. Check execution logs for any unauthorized usage
7. Document the incident
