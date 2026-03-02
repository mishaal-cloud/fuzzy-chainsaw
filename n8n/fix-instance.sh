#!/usr/bin/env bash
# ============================================
# fix-instance.sh — Clean up and production-harden the n8n instance
#
# 1. Deduplicate variables (keep newest, delete old copies)
# 2. Tag all workflows by name pattern
# 3. Activate workflows that should be active
# 4. Deactivate workflows that should be inactive
# 5. Report final instance state
#
# Cloud-first: only requires curl + jq
# Usage: ./n8n/fix-instance.sh [--dry-run]
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$ROOT_DIR/.env"

DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --help|-h)
      echo "Usage: $0 [--dry-run]"
      exit 0
      ;;
  esac
done

# --- Load .env ---
if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] .env file not found at $ENV_FILE"
  exit 1
fi
set -a
source "$ENV_FILE"
set +a

if [[ -z "${N8N_API_KEY:-}" || -z "${N8N_INSTANCE_URL:-}" ]]; then
  echo "[ERROR] N8N_API_KEY and N8N_INSTANCE_URL must be set in .env"
  exit 1
fi

for cmd in curl jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "[ERROR] Required command '$cmd' not found."
    exit 1
  fi
done

API_URL="${N8N_INSTANCE_URL}/api/v1"
AUTH_HEADER="X-N8N-API-KEY: ${N8N_API_KEY}"

api_get() {
  curl -sf -H "$AUTH_HEADER" "$API_URL$1" 2>/dev/null
}

api_post() {
  curl -sf -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$2" "$API_URL$1" 2>/dev/null
}

api_put() {
  curl -s -w "\n%{http_code}" -X PUT -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$2" "$API_URL$1" 2>/dev/null
}

api_delete() {
  curl -sf -X DELETE -H "$AUTH_HEADER" "$API_URL$1" 2>/dev/null
}

echo ""
echo "n8n Instance Fix — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Instance: $N8N_INSTANCE_URL"
if $DRY_RUN; then echo "[DRY-RUN MODE — no changes will be made]"; fi
echo ""

# ═══════════════════════════════════════════════
#  Step 1: Deduplicate Variables
# ═══════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 1: Deduplicate Variables"
echo "═══════════════════════════════════════════════════════════════"
echo ""

all_vars=$(api_get "/variables?limit=250" | jq -c '.data // []') || {
  echo "[ERROR] Failed to fetch variables"
  exit 1
}

var_count=$(echo "$all_vars" | jq 'length')
echo "[INFO] Found $var_count variable(s)"

# Find duplicate keys
dup_keys=$(echo "$all_vars" | jq -r '[group_by(.key)[] | select(length > 1) | .[0].key] | .[]')
dupes_deleted=0

if [[ -z "$dup_keys" ]]; then
  echo "[OK]   No duplicate variables found."
else
  echo "[WARN] Duplicate variable keys found:"
  for dup_key in $dup_keys; do
    # Get all entries for this key, sorted by ID (newest last — n8n IDs are lexicographic)
    entries=$(echo "$all_vars" | jq -c --arg k "$dup_key" '[.[] | select(.key == $k)] | sort_by(.id)')
    entry_count=$(echo "$entries" | jq 'length')
    keep_id=$(echo "$entries" | jq -r '.[-1].id')
    echo "  $dup_key: $entry_count copies (keeping ID: $keep_id)"

    # Delete all but the newest
    echo "$entries" | jq -r ".[:-1][].id" | while read -r old_id; do
      if $DRY_RUN; then
        echo "  [DRY-RUN] Would delete variable $dup_key (ID: $old_id)"
      else
        api_delete "/variables/$old_id" && {
          echo "  [OK] Deleted duplicate $dup_key (ID: $old_id)"
          ((dupes_deleted++)) || true
        } || {
          echo "  [WARN] Failed to delete $dup_key (ID: $old_id)"
        }
      fi
    done
  done
  echo "[INFO] Deleted $dupes_deleted duplicate variable(s)"
fi

# ═══════════════════════════════════════════════
#  Step 2: Tag All Workflows
# ═══════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 2: Tag All Workflows"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Fetch tags
all_tags=$(api_get "/tags?limit=250" | jq -c '.data // []') || {
  echo "[ERROR] Failed to fetch tags"
  exit 1
}

# Build tag ID lookup
get_tag_id() {
  echo "$all_tags" | jq -r --arg t "$1" '.[] | select(.name == $t) | .id'
}

TAG_INFRA=$(get_tag_id "Infrastructure")
TAG_GATEWAY=$(get_tag_id "Gateway")
TAG_MONITORING=$(get_tag_id "Monitoring")
TAG_TESTING=$(get_tag_id "Testing")
TAG_SEO=$(get_tag_id "SEO-Pipeline")

echo "[INFO] Tag IDs:"
echo "  Infrastructure: $TAG_INFRA"
echo "  Gateway:        $TAG_GATEWAY"
echo "  Monitoring:     $TAG_MONITORING"
echo "  Testing:        $TAG_TESTING"
echo "  SEO-Pipeline:   $TAG_SEO"
echo ""

# Map workflow names to tags and active status
# Format: "workflow name|tag_id|tag_name|should_be_active"
name_to_tag() {
  local name="$1"
  case "$name" in
    "Gateway: Marketing Ads")                   echo "$TAG_GATEWAY|Gateway|true" ;;
    "Gateway: Analytics")                       echo "$TAG_GATEWAY|Gateway|true" ;;
    "Gateway: Google Suite")                    echo "$TAG_GATEWAY|Gateway|true" ;;
    "Gateway: CRM")                             echo "$TAG_GATEWAY|Gateway|true" ;;
    "API Discovery Gateway")                    echo "$TAG_GATEWAY|Gateway|true" ;;
    "Main API Gateway")                         echo "$TAG_GATEWAY|Gateway|true" ;;
    *"Universal API Gateway"*)                  echo "$TAG_GATEWAY|Gateway|true" ;;
    "Infrastructure: Rate Limiter")             echo "$TAG_INFRA|Infrastructure|true" ;;
    "Infrastructure: Request Logger")           echo "$TAG_INFRA|Infrastructure|true" ;;
    "Infrastructure: Health Check (Scheduled)") echo "$TAG_INFRA|Infrastructure|true" ;;
    "Infrastructure: Health Check (Webhook)")   echo "$TAG_INFRA|Infrastructure|true" ;;
    "Infrastructure: Error Handler")            echo "$TAG_INFRA|Infrastructure|true" ;;
    "Infrastructure: Credential Rotator")       echo "$TAG_INFRA|Infrastructure|false" ;;
    "Error Handler")                            echo "$TAG_INFRA|Infrastructure|false" ;;
    "Health Check")                             echo "$TAG_INFRA|Infrastructure|false" ;;
    "Monitor: Alert Manager")                   echo "$TAG_MONITORING|Monitoring|true" ;;
    "Monitor: Metrics Collector")               echo "$TAG_MONITORING|Monitoring|true" ;;
    "Monitor: Daily Summary")                   echo "$TAG_MONITORING|Monitoring|true" ;;
    "Testing: Smoke Tests")                     echo "$TAG_TESTING|Testing|true" ;;
    "Testing: Test Runner")                     echo "$TAG_TESTING|Testing|false" ;;
    "SEO Pipeline: Content Optimizer")          echo "$TAG_SEO|SEO-Pipeline|true" ;;
    "SEO Pipeline: Data Collection")            echo "$TAG_SEO|SEO-Pipeline|true" ;;
    "SEO Pipeline: Monitoring & Reporting")     echo "$TAG_SEO|SEO-Pipeline|true" ;;
    "SEO Pipeline: Master Orchestrator")        echo "$TAG_SEO|SEO-Pipeline|true" ;;
    *"Credential Blitz"*)                       echo "$TAG_TESTING|Testing|false" ;;
    "SEMrush API Key Test")                     echo "$TAG_TESTING|Testing|false" ;;
    "My workflow")                              echo "||false" ;;
    *)                                          echo "||" ;;
  esac
}

# Fetch all workflows
all_workflows=$(api_get "/workflows?limit=250" | jq -c '.data // []') || {
  echo "[ERROR] Failed to fetch workflows"
  exit 1
}

wf_count=$(echo "$all_workflows" | jq 'length')
echo "[INFO] Processing $wf_count workflow(s)..."
echo ""

tagged=0
activated=0
deactivated=0
skipped=0

while read -r wf; do
  wf_id=$(echo "$wf" | jq -r '.id')
  wf_name=$(echo "$wf" | jq -r '.name')
  wf_active=$(echo "$wf" | jq -r '.active')
  current_tags=$(echo "$wf" | jq -r '[.tags[]?.name] | join(", ")')

  mapping=$(name_to_tag "$wf_name")
  target_tag_id=$(echo "$mapping" | cut -d'|' -f1)
  target_tag_name=$(echo "$mapping" | cut -d'|' -f2)
  should_be_active=$(echo "$mapping" | cut -d'|' -f3)

  needs_tag=false
  needs_activate=false
  needs_deactivate=false

  # Check if tag needs to be applied
  if [[ -n "$target_tag_id" && "$current_tags" != *"$target_tag_name"* ]]; then
    needs_tag=true
  fi

  # Check if activation state needs to change
  if [[ "$should_be_active" == "true" && "$wf_active" == "false" ]]; then
    needs_activate=true
  elif [[ "$should_be_active" == "false" && "$wf_active" == "true" ]]; then
    needs_deactivate=true
  fi

  if ! $needs_tag && ! $needs_activate && ! $needs_deactivate; then
    ((skipped++)) || true
    continue
  fi

  echo "  $wf_name (ID: $wf_id)"

  if $DRY_RUN; then
    $needs_tag && echo "    [DRY-RUN] Would tag with '$target_tag_name'"
    $needs_activate && echo "    [DRY-RUN] Would activate"
    $needs_deactivate && echo "    [DRY-RUN] Would deactivate"
    continue
  fi

  # Tag via dedicated PUT /workflows/{id}/tags endpoint
  # (tags is read-only on PUT /workflows/{id} — per OpenAPI spec)
  if $needs_tag; then
    tag_body=$(jq -n --arg tid "$target_tag_id" '[{"id": $tid}]')

    response=$(api_put "/workflows/$wf_id/tags" "$tag_body")
    http_status=$(echo "$response" | tail -1)
    response_body=$(echo "$response" | sed '$d')

    if [[ "$http_status" -ge 200 && "$http_status" -lt 300 ]]; then
      echo "    [OK] Tagged: $target_tag_name"
      ((tagged++)) || true
    else
      echo "    [ERROR] Tag failed: HTTP $http_status — $response_body"
    fi
  fi

  # Activate/deactivate via dedicated endpoints
  if $needs_activate; then
    if api_post "/workflows/$wf_id/activate" '{}' >/dev/null 2>&1; then
      echo "    [OK] Activated"
      ((activated++)) || true
    else
      echo "    [WARN] Failed to activate (may only have manual triggers)"
    fi
  elif $needs_deactivate; then
    if api_post "/workflows/$wf_id/deactivate" '{}' >/dev/null 2>&1; then
      echo "    [OK] Deactivated"
      ((deactivated++)) || true
    else
      echo "    [WARN] Failed to deactivate"
    fi
  fi

done < <(echo "$all_workflows" | jq -c '.[]')

echo ""
echo "[INFO] Tagged: $tagged, Activated: $activated, Deactivated: $deactivated, Already OK: $skipped"

# ═══════════════════════════════════════════════
#  Step 3: Final State Report
# ═══════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 3: Final Instance State"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Re-fetch to show final state
final_wfs=$(api_get "/workflows?limit=250" | jq -c '.data // []') || final_wfs="$all_workflows"
final_vars=$(api_get "/variables?limit=250" | jq -c '.data // []') || final_vars="$all_vars"

echo "Workflows:"
printf "  %-45s %-8s %s\n" "NAME" "ACTIVE" "TAGS"
printf "  %-45s %-8s %s\n" "---------------------------------------------" "--------" "----"
echo "$final_wfs" | jq -r '.[] | [.name, (if .active then "YES" else "NO" end), ([.tags[]?.name] | join(", "))] | @tsv' | \
  sort | while IFS=$'\t' read -r name active tags; do
    printf "  %-45s %-8s %s\n" "$name" "$active" "$tags"
  done

echo ""
echo "Variables: $(echo "$final_vars" | jq 'length') total"

# Check for remaining duplicates
remaining_dupes=$(echo "$final_vars" | jq '[group_by(.key)[] | select(length > 1) | .[0].key] | length')
if [[ "$remaining_dupes" -gt 0 ]]; then
  echo "[WARN] $remaining_dupes duplicate variable key(s) remain"
else
  echo "[OK]   No duplicate variables"
fi

echo ""
echo "Credentials: $(api_get "/credentials?limit=250" | jq '.data | length') total"
echo "Tags: $(echo "$all_tags" | jq 'length') total"

# Health summary
active_count=$(echo "$final_wfs" | jq '[.[] | select(.active == true)] | length')
inactive_count=$(echo "$final_wfs" | jq '[.[] | select(.active == false)] | length')
tagged_count=$(echo "$final_wfs" | jq '[.[] | select((.tags // []) | length > 0)] | length')
untagged_count=$(echo "$final_wfs" | jq '[.[] | select((.tags // []) | length == 0)] | length')

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Health Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Workflows:  $active_count active / $inactive_count inactive"
echo "  Tagged:     $tagged_count / $(echo "$final_wfs" | jq 'length')"
if [[ "$untagged_count" -gt 0 ]]; then
  echo "  Untagged workflows:"
  echo "$final_wfs" | jq -r '.[] | select((.tags // []) | length == 0) | "    - \(.name) (\(.id))"'
fi
echo ""
echo "[OK] Instance fix complete!"
