# n8n Enterprise Improvements - Implementation Plan

## Context
Based on high-caliber feedback from the n8n AI Bot and enterprise audit, we need to
transform the Universal API Gateway from a monolithic 1000+ line single workflow into
a modular, observable, resilient enterprise architecture.

## What We're Building

### Directory Structure
```
n8n/
├── workflows/
│   ├── gateways/
│   │   ├── main-api-gateway.json          # Slim router (replaces 1000+ line monolith)
│   │   ├── marketing-ads-gateway.json     # Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads
│   │   ├── crm-gateway.json              # HubSpot, Salesforce, Pipedrive
│   │   ├── analytics-gateway.json        # GA4, Search Console, Data Studio
│   │   └── google-suite-gateway.json     # Gmail, Calendar, Drive, Sheets
│   ├── infrastructure/
│   │   ├── error-handler.json            # Centralized error processing sub-workflow
│   │   ├── rate-limiter.json             # Rate limiting with counters
│   │   ├── request-logger.json           # Structured request/response logging
│   │   ├── health-check.json             # Periodic API health monitoring
│   │   └── credential-rotator.json       # Credential rotation alerts
│   ├── monitoring/
│   │   ├── metrics-collector.json        # Aggregate execution metrics
│   │   ├── alert-manager.json            # PagerDuty/Slack escalation
│   │   └── daily-summary.json            # Daily ops summary report
│   └── testing/
│       ├── test-runner.json              # Automated test execution
│       └── smoke-tests.json              # Quick health validation
├── schemas/
│   ├── openapi-spec.yaml                 # OpenAPI spec for the API Gateway
│   └── request-validation.json           # JSON Schema for input validation
├── config/
│   ├── rate-limits.json                  # Rate limit definitions per API
│   ├── credential-inventory.json         # Credential registry & rotation schedule
│   └── api-registry.json                 # API configuration registry (extracted from code node)
├── docs/
│   ├── architecture.md                   # Architecture overview & diagrams
│   ├── runbooks/
│   │   ├── incident-response.md          # When things break
│   │   ├── adding-new-api.md             # How to add a new API
│   │   └── credential-rotation.md        # How to rotate credentials
│   └── api-reference.md                  # Endpoint documentation
├── infrastructure/
│   ├── docker-compose.monitoring.yml     # ELK/Grafana/Prometheus stack
│   └── backup-restore.sh                # Workflow backup/restore script
└── IMPLEMENTATION_PLAN.md               # This file
```

---

## Phase 1: Foundation Infrastructure (Critical)

### 1.1 API Registry Extraction
**What:** Extract the 1000+ line code node into a clean JSON registry
**Why:** Single source of truth for all API configs, decoupled from routing logic
**File:** `config/api-registry.json`
- All 30+ API configurations with endpoints, auth types, required params
- Organized by category (marketing, CRM, analytics, google-suite)
- Each entry: name, base_url, auth_type, credential_key, rate_limits, required_params

### 1.2 Request Validation Schema
**What:** JSON Schema for validating incoming gateway requests
**Why:** Malformed requests currently cause cryptic errors
**File:** `schemas/request-validation.json`
- Required fields: client, api, action
- Per-API parameter validation
- Clear error messages for invalid requests

### 1.3 Error Handler Sub-Workflow
**What:** Centralized error processing workflow
**Why:** Only routing errors trigger Slack alerts; API failures are silent
**File:** `workflows/infrastructure/error-handler.json`
- Receives: error details, workflow context, request info
- Actions: Log to data table, send Slack alert, escalate to PagerDuty for critical
- Retry guidance: exponential backoff config per error type
- Dead letter queue: store failed requests for retry

### 1.4 Request Logger Sub-Workflow
**What:** Structured logging for every request/response
**Why:** Zero observability currently
**File:** `workflows/infrastructure/request-logger.json`
- Log entry: request_id, timestamp, client, api, action, status, duration, error
- Stores to n8n internal data table
- Webhook endpoint for external log aggregation (ELK/Datadog)

---

## Phase 2: Gateway Refactoring (High Priority)

### 2.1 Main API Gateway (Slim Router)
**What:** Replace monolithic gateway with thin routing layer
**Why:** 1000+ line code node is unmaintainable
**File:** `workflows/gateways/main-api-gateway.json`
- Webhook entry point with API key auth
- Input validation (calls validation schema)
- Request logging (calls logger sub-workflow)
- Route to category-specific sub-workflow via Execute Workflow
- Properly configured Switch node with explicit rules for all 32 APIs
- Error handling wrapper

### 2.2 Marketing Ads Gateway
**File:** `workflows/gateways/marketing-ads-gateway.json`
- Handles: Google Ads, Meta/Facebook Ads, LinkedIn Ads, TikTok Ads
- Per-API error handling with retry logic
- Rate limiting integration
- Response normalization

### 2.3 CRM Gateway
**File:** `workflows/gateways/crm-gateway.json`
- Handles: HubSpot, Salesforce, Pipedrive
- OAuth2 token refresh handling
- Pagination support
- Response normalization

### 2.4 Analytics Gateway
**File:** `workflows/gateways/analytics-gateway.json`
- Handles: GA4, Google Search Console, Data Studio
- Date range normalization
- Metric/dimension validation
- Response normalization

### 2.5 Google Suite Gateway
**File:** `workflows/gateways/google-suite-gateway.json`
- Handles: Gmail, Calendar, Drive, Sheets
- OAuth2 scoping
- Response normalization

---

## Phase 3: Resilience & Rate Limiting

### 3.1 Rate Limiter Sub-Workflow
**What:** Prevent API quota exhaustion
**File:** `workflows/infrastructure/rate-limiter.json`
- Check current usage against limits from `config/rate-limits.json`
- Counter storage in n8n data tables
- Return: allowed/denied + retry_after time
- Auto-reset counters based on window (per-minute, per-day)

### 3.2 Rate Limits Configuration
**File:** `config/rate-limits.json`
- Per-API rate limits: requests_per_minute, requests_per_hour, daily_quota
- Burst allowance settings
- Queue priority levels

### 3.3 Health Check Workflow
**What:** Proactive API health monitoring
**File:** `workflows/infrastructure/health-check.json`
- Scheduled every 5 minutes
- Lightweight ping to each API endpoint
- Credential validity check
- Store health status in data table
- Alert on consecutive failures

---

## Phase 4: Monitoring & Alerting

### 4.1 Metrics Collector
**File:** `workflows/monitoring/metrics-collector.json`
- Aggregates execution data from n8n internal API
- Calculates: request volume, error rates, p50/p95/p99 latency
- Stores time-series data for dashboards
- Scheduled every 5 minutes

### 4.2 Alert Manager
**File:** `workflows/monitoring/alert-manager.json`
- Escalation tiers: Info → Warning → Critical
- Channels: Slack (info/warning), PagerDuty (critical)
- Alert conditions: error rate > 5%, latency p95 > 10s, API down
- Alert deduplication and cooldown

### 4.3 Daily Summary Report
**File:** `workflows/monitoring/daily-summary.json`
- Scheduled at 8 AM daily
- Summary: total requests, errors, top APIs, slowest APIs
- Credential expiration warnings
- Sends to Slack and email

### 4.4 Monitoring Stack (Docker Compose)
**File:** `infrastructure/docker-compose.monitoring.yml`
- Prometheus for metrics collection
- Grafana with pre-configured dashboards
- Optional ELK stack for log aggregation

---

## Phase 5: Security & Credentials

### 5.1 Credential Inventory
**File:** `config/credential-inventory.json`
- Registry of all credentials: service, type, owner, last_rotated, rotation_policy
- Environment tagging (dev/staging/prod)
- Naming convention enforcement

### 5.2 Credential Rotator
**File:** `workflows/infrastructure/credential-rotator.json`
- Scheduled daily check
- Alerts 7 days before credential expiration
- Validates credentials are still functional
- Logs rotation history

---

## Phase 6: Testing & Quality

### 6.1 Test Runner Workflow
**File:** `workflows/testing/test-runner.json`
- Executes test cases from test definitions
- Tests: valid requests, invalid requests, auth failures, rate limits
- Stores test results in data table
- Blocks deployment if tests fail

### 6.2 Smoke Tests
**File:** `workflows/testing/smoke-tests.json`
- Lightweight validation (runs every hour)
- Ping each API category gateway
- Verify auth is working
- Response time < 5s threshold

---

## Phase 7: Documentation & Operations

### 7.1 Architecture Documentation
**File:** `docs/architecture.md`
- System architecture diagram
- Data flow diagrams
- Component responsibilities
- Decision records

### 7.2 OpenAPI Specification
**File:** `schemas/openapi-spec.yaml`
- Full API documentation for the gateway
- Request/response schemas
- Authentication documentation
- Example requests

### 7.3 Runbooks
**Files:** `docs/runbooks/*.md`
- Incident response playbook
- Adding a new API guide
- Credential rotation procedures

### 7.4 Backup/Restore Script
**File:** `infrastructure/backup-restore.sh`
- Export all workflows via n8n CLI/API
- Encrypted credential backup
- Git-based version control
- Restore procedure

---

## Implementation Order & Parallelization

```
Parallel Track A (Infrastructure):     Parallel Track B (Gateways):
├── 1.1 API Registry                   ├── 2.1 Main Gateway (after 1.1)
├── 1.2 Request Validation             ├── 2.2 Marketing Ads Gateway
├── 1.3 Error Handler                  ├── 2.3 CRM Gateway
├── 1.4 Request Logger                 ├── 2.4 Analytics Gateway
├── 3.1 Rate Limiter                   └── 2.5 Google Suite Gateway
├── 3.2 Rate Limits Config
└── 3.3 Health Check

Parallel Track C (Monitoring):         Parallel Track D (Docs & Testing):
├── 4.1 Metrics Collector              ├── 6.1 Test Runner
├── 4.2 Alert Manager                  ├── 6.2 Smoke Tests
├── 4.3 Daily Summary                  ├── 7.1 Architecture Docs
├── 4.4 Monitoring Stack               ├── 7.2 OpenAPI Spec
├── 5.1 Credential Inventory           ├── 7.3 Runbooks
└── 5.2 Credential Rotator             └── 7.4 Backup Script
```

**Key dependency:** Main Gateway (2.1) depends on API Registry (1.1) being complete.
Everything else can be parallelized across tracks.

---

## Deliverables Summary

| Category | Files | Priority |
|----------|-------|----------|
| Gateway Workflows | 5 JSON files | Critical |
| Infrastructure Workflows | 5 JSON files | Critical |
| Monitoring Workflows | 3 JSON files | High |
| Testing Workflows | 2 JSON files | High |
| Config Files | 3 JSON files | Critical |
| Schema Files | 2 files (YAML + JSON) | High |
| Documentation | 5 files (MD + YAML) | Medium |
| Infrastructure | 2 files (Docker + Shell) | Medium |
| **Total** | **27 files** | |

All workflow JSON files will be importable directly into n8n.
