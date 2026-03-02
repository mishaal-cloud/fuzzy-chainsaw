#!/usr/bin/env bash
# ============================================
# deploy-to-n8n.sh — Deploy workflows & variables to n8n Cloud
#
# Cloud-first: only requires curl + jq (no local deps)
# Fixes:
#   - Variable sync: uses PATCH with variable ID for existing vars
#   - Workflow tagging: GETs full workflow before PUT to include nodes
#
# Usage: ./n8n/deploy-to-n8n.sh [--dry-run] [--skip-variables] [--skip-tags] [--skip-workflows]
# ============================================
set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
WORKFLOWS_DIR="$SCRIPT_DIR/workflows"
ENV_FILE="$ROOT_DIR/.env"

# --- Parse flags ---
DRY_RUN=false
SKIP_VARS=false
SKIP_TAGS=false
SKIP_WORKFLOWS=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --skip-variables) SKIP_VARS=true ;;
    --skip-tags) SKIP_TAGS=true ;;
    --skip-workflows) SKIP_WORKFLOWS=true ;;
    --help|-h)
      echo "Usage: $0 [--dry-run] [--skip-variables] [--skip-tags] [--skip-workflows]"
      exit 0
      ;;
  esac
done

# --- Load .env ---
if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] .env file not found at $ENV_FILE"
  echo "        Copy .env.example to .env and fill in your values."
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# --- Validate required vars ---
if [[ -z "${N8N_API_KEY:-}" ]]; then
  echo "[ERROR] N8N_API_KEY is not set in .env"
  exit 1
fi
if [[ -z "${N8N_INSTANCE_URL:-}" ]]; then
  echo "[ERROR] N8N_INSTANCE_URL is not set in .env"
  exit 1
fi

# --- Check dependencies ---
for cmd in curl jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "[ERROR] Required command '$cmd' not found. Install it first."
    exit 1
  fi
done

API_URL="${N8N_INSTANCE_URL}/api/v1"
AUTH_HEADER="X-N8N-API-KEY: ${N8N_API_KEY}"

# --- Counters ---
VARS_SYNCED=0
VARS_FAILED=0
TAGS_CREATED=0
TAGS_SKIPPED=0
WF_DEPLOYED=0
WF_SKIPPED=0
WF_FAILED=0

# --- Helpers ---
api_get() {
  curl -sf -H "$AUTH_HEADER" "$API_URL$1" 2>/dev/null
}

api_post() {
  curl -sf -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$2" "$API_URL$1" 2>/dev/null
}

api_patch() {
  curl -sf -X PATCH -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$2" "$API_URL$1" 2>/dev/null
}

api_put() {
  curl -sf -X PUT -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$2" "$API_URL$1" 2>/dev/null
}

api_post_verbose() {
  local status body
  body=$(curl -s -w "\n%{http_code}" -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$2" "$API_URL$1" 2>/dev/null)
  status=$(echo "$body" | tail -1)
  body=$(echo "$body" | sed '$d')
  echo "$status|$body"
}

api_put_verbose() {
  local status body
  body=$(curl -s -w "\n%{http_code}" -X PUT -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$2" "$API_URL$1" 2>/dev/null)
  status=$(echo "$body" | tail -1)
  body=$(echo "$body" | sed '$d')
  echo "$status|$body"
}

# ═══════════════════════════════════════════════
#  Sync Variables
# ═══════════════════════════════════════════════
sync_variables() {
  echo ""
  echo "Syncing n8n Project Variables"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  # Variables to sync from .env -> n8n project variables
  local -a VAR_KEYS=(
    SEMRUSH_API_KEY
    GA4_PROPERTY_ID
    GSC_SITE_URL
    GOOGLE_ADS_CUSTOMER_ID
    GOOGLE_ADS_LOGIN_CUSTOMER_ID
    GOOGLE_ADS_DEVELOPER_TOKEN
    ALERT_EMAIL
    APOLLO_API_KEY
    FRED_API_KEY
    CENSUS_API_KEY
    FMP_API_KEY
    NEWSAPI_AI_KEY
    GONG_ACCESS_KEY
    GONG_BASE_URL
    CLARITY_API_TOKEN
    HUBSPOT_ACCESS_TOKEN
  )

  echo "[INFO] Found ${#VAR_KEYS[@]} variable(s) to sync."

  # Fetch existing variables (with pagination)
  local existing_vars
  existing_vars=$(api_get "/variables?limit=250" | jq -c '.data // []') || {
    echo "[ERROR] Failed to fetch existing variables from n8n"
    return 1
  }

  for key in "${VAR_KEYS[@]}"; do
    local value="${!key:-}"
    if [[ -z "$value" ]]; then
      echo "[SKIP] $key — not set in .env"
      continue
    fi

    if $DRY_RUN; then
      echo "[DRY-RUN] Would sync: $key"
      continue
    fi

    # Check if variable already exists
    local existing_id
    existing_id=$(echo "$existing_vars" | jq -r --arg k "$key" '.[] | select(.key == $k) | .id')

    if [[ -n "$existing_id" ]]; then
      # FIX: Use PATCH with the variable ID to update existing variables
      local patch_result
      patch_result=$(api_patch "/variables/$existing_id" "$(jq -n --arg v "$value" '{value: $v}')" 2>&1) && {
        echo "[OK]   Updated: $key"
        ((VARS_SYNCED++))
      } || {
        # Some n8n versions use DELETE + POST instead of PATCH
        # Try delete and recreate
        curl -sf -X DELETE -H "$AUTH_HEADER" "$API_URL/variables/$existing_id" &>/dev/null
        local recreate_result
        recreate_result=$(api_post "/variables" "$(jq -n --arg k "$key" --arg v "$value" '{key: $k, value: $v}')" 2>&1) && {
          echo "[OK]   Recreated: $key"
          ((VARS_SYNCED++))
        } || {
          echo "[WARN]   Failed to update: $key"
          ((VARS_FAILED++))
        }
      }
    else
      # Create new variable
      local create_result
      create_result=$(api_post "/variables" "$(jq -n --arg k "$key" --arg v "$value" '{key: $k, value: $v}')" 2>&1) && {
        echo "[OK]   Created: $key"
        ((VARS_SYNCED++))
      } || {
        echo "[WARN]   Failed to create: $key"
        ((VARS_FAILED++))
      }
    fi
  done

  echo "[INFO] Variables synced: $VARS_SYNCED, failed: $VARS_FAILED"
}

# ═══════════════════════════════════════════════
#  Create Tags
# ═══════════════════════════════════════════════
create_tags() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  Creating Tags"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  local -a TAGS=(Infrastructure Gateway Monitoring Testing SEO-Pipeline)

  # Fetch existing tags
  local existing_tags
  existing_tags=$(api_get "/tags?limit=250" | jq -c '.data // []') || {
    echo "[ERROR] Failed to fetch existing tags"
    return 1
  }

  for tag in "${TAGS[@]}"; do
    local exists
    exists=$(echo "$existing_tags" | jq -r --arg t "$tag" '[.[] | select(.name == $t)] | length')

    if [[ "$exists" -gt 0 ]]; then
      echo "[INFO] Tag '$tag' already exists, skipping."
      ((TAGS_SKIPPED++))
      continue
    fi

    if $DRY_RUN; then
      echo "[DRY-RUN] Would create tag: $tag"
      continue
    fi

    local result
    result=$(api_post "/tags" "$(jq -n --arg n "$tag" '{name: $n}')")
    if [[ $? -eq 0 ]]; then
      local tag_id
      tag_id=$(echo "$result" | jq -r '.id')
      echo "[OK] Created tag '$tag' (ID: $tag_id)"
      ((TAGS_CREATED++))
    else
      echo "[WARN] Failed to create tag '$tag'"
    fi
  done
}

# ═══════════════════════════════════════════════
#  Deploy Workflows
# ═══════════════════════════════════════════════
deploy_workflows() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  Deploying Workflows"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  if [[ ! -d "$WORKFLOWS_DIR" ]]; then
    echo "[WARN] No workflows directory found at $WORKFLOWS_DIR"
    return 0
  fi

  # Find all workflow JSON files
  local -a wf_files=()
  while IFS= read -r -d '' f; do
    wf_files+=("$f")
  done < <(find "$WORKFLOWS_DIR" -name '*.json' -print0 | sort -z)

  echo "[INFO] Found ${#wf_files[@]} workflow file(s) to deploy."
  echo ""

  if [[ ${#wf_files[@]} -eq 0 ]]; then
    echo "[INFO] No workflow files found. Use export-workflows.sh to pull from n8n first."
    return 0
  fi

  # Fetch existing workflows for idempotency check
  echo "[INFO] Fetching existing workflows for idempotency check..."
  local existing_workflows
  existing_workflows=$(api_get "/workflows?limit=250" | jq -c '.data // []') || {
    echo "[ERROR] Failed to fetch existing workflows"
    return 1
  }
  local existing_count
  existing_count=$(echo "$existing_workflows" | jq 'length')
  echo "[INFO] Found $existing_count existing workflow(s) on the instance."

  # Fetch all tags for tag mapping
  local all_tags
  all_tags=$(api_get "/tags?limit=250" | jq -c '.data // []') || all_tags="[]"

  # Deploy each workflow
  for wf_file in "${wf_files[@]}"; do
    local rel_path="${wf_file#$WORKFLOWS_DIR/}"
    echo "--- $rel_path ---"

    # Extract workflow name from JSON
    local wf_name
    wf_name=$(jq -r '.name // empty' "$wf_file")
    if [[ -z "$wf_name" ]]; then
      echo "[WARN] No 'name' field in $rel_path, skipping."
      ((WF_FAILED++))
      continue
    fi

    # Determine tag from directory
    local wf_dir
    wf_dir=$(dirname "$rel_path")
    local tag_name=""
    case "$wf_dir" in
      gateways)       tag_name="Gateway" ;;
      infrastructure) tag_name="Infrastructure" ;;
      monitoring)     tag_name="Monitoring" ;;
      testing)        tag_name="Testing" ;;
      seo-pipeline)   tag_name="SEO-Pipeline" ;;
    esac

    # Check if workflow already exists (by name)
    local existing_id
    existing_id=$(echo "$existing_workflows" | jq -r --arg n "$wf_name" '.[] | select(.name == $n) | .id' | head -1)

    if [[ -n "$existing_id" ]]; then
      echo "[INFO] Workflow '$wf_name' already exists, skipping."
      ((WF_SKIPPED++))
      continue
    fi

    if $DRY_RUN; then
      echo "[DRY-RUN] Would deploy: $wf_name"
      continue
    fi

    # Create the workflow
    local create_response
    create_response=$(api_post_verbose "/workflows" "$(cat "$wf_file")")
    local http_status="${create_response%%|*}"
    local response_body="${create_response#*|}"

    if [[ "$http_status" -ge 200 && "$http_status" -lt 300 ]]; then
      local new_id
      new_id=$(echo "$response_body" | jq -r '.id')
      echo "[OK] Created workflow '$wf_name' (ID: $new_id)"

      # FIX: Tag the workflow by GETting full workflow first, then PUTting with tags
      if [[ -n "$tag_name" ]]; then
        local tag_id
        tag_id=$(echo "$all_tags" | jq -r --arg t "$tag_name" '.[] | select(.name == $t) | .id')

        if [[ -n "$tag_id" ]]; then
          # GET the full workflow (includes nodes, connections, etc.)
          local full_workflow
          full_workflow=$(api_get "/workflows/$new_id")

          if [[ -n "$full_workflow" ]]; then
            # Merge tags into the full workflow body
            local updated_body
            updated_body=$(echo "$full_workflow" | jq --arg tid "$tag_id" --arg tname "$tag_name" \
              '.tags = [{"id": $tid, "name": $tname}]')

            local tag_response
            tag_response=$(api_put_verbose "/workflows/$new_id" "$updated_body")
            local tag_status="${tag_response%%|*}"

            if [[ "$tag_status" -ge 200 && "$tag_status" -lt 300 ]]; then
              echo "[OK]   Tagged with '$tag_name'"
            else
              local tag_error="${tag_response#*|}"
              echo "[WARN]   Failed to tag with '$tag_name'"
              echo "[ERROR] HTTP $tag_status from PUT /workflows/$new_id"
              echo "[ERROR] Response: $tag_error"
            fi
          fi
        fi
      fi

      # Activate the workflow
      local activate_body
      activate_body=$(api_get "/workflows/$new_id" | jq '.active = true')
      local activate_response
      activate_response=$(api_put_verbose "/workflows/$new_id" "$activate_body")
      local act_status="${activate_response%%|*}"

      if [[ "$act_status" -ge 200 && "$act_status" -lt 300 ]]; then
        echo "[OK]   Activated workflow"
      else
        echo "[WARN]   Failed to activate workflow"
      fi

      ((WF_DEPLOYED++))
    else
      echo "[ERROR] Failed to create workflow '$wf_name'"
      echo "[ERROR] HTTP $http_status: $response_body"
      ((WF_FAILED++))
    fi
    echo ""
  done
}

# ═══════════════════════════════════════════════
#  Print Summary
# ═══════════════════════════════════════════════
print_summary() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  Deployment Summary"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  echo "n8n Instance: $N8N_INSTANCE_URL"
  echo ""
  echo "Variables: synced=$VARS_SYNCED, failed=$VARS_FAILED"
  echo "Tags:      created=$TAGS_CREATED, skipped=$TAGS_SKIPPED"
  echo "Workflows: deployed=$WF_DEPLOYED, skipped=$WF_SKIPPED, failed=$WF_FAILED"
  echo ""

  if [[ $VARS_FAILED -gt 0 || $WF_FAILED -gt 0 ]]; then
    echo "[WARN] Some operations failed. Review the output above."
  else
    echo "[OK] Deployment complete!"
  fi
}

# ═══════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════
echo ""
echo "n8n Deployment — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Instance: $N8N_INSTANCE_URL"
if $DRY_RUN; then echo "[DRY-RUN MODE]"; fi
echo ""

$SKIP_VARS      || sync_variables
$SKIP_TAGS      || create_tags
$SKIP_WORKFLOWS || deploy_workflows
print_summary
