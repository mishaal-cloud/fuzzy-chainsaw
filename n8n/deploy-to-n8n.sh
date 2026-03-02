#!/usr/bin/env bash
# n8n Enterprise Deployment Script
# Deploys all workflow JSON files to your n8n instance via the REST API
#
# Usage:
#   ./deploy-to-n8n.sh <N8N_URL> <N8N_API_KEY>
#   or set N8N_URL and N8N_API_KEY environment variables
#
# Requirements: curl, bash, jq (optional, for prettier output)
#
# What this script does:
#   1. Validates connectivity to the n8n instance
#   2. Creates organizational tags (Infrastructure, Gateway, Monitoring, Testing)
#   3. Discovers all workflow JSON files in n8n/workflows/**/*.json
#   4. For each workflow: checks if it already exists (by name), creates or skips
#   5. Activates workflows that should be always-on (health checks, monitors, gateways)
#   6. Assigns appropriate tags to each workflow based on its directory
#   7. Prints a deployment summary with IDs and webhook URLs
#
# Idempotency: Safe to run multiple times. Existing workflows (matched by name) are skipped.

set -euo pipefail

# ==============================================================================
# Configuration
# ==============================================================================

# Color codes for output (disabled if not a terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
fi

# Tags to create for organizing workflows
TAGS=("Infrastructure" "Gateway" "Monitoring" "Testing")

# Workflows that should be activated after deployment
# Patterns matched against workflow file paths
ACTIVATE_PATTERNS=(
    "gateways/main-api-gateway"
    "gateways/marketing-ads-gateway"
    "gateways/crm-gateway"
    "gateways/analytics-gateway"
    "gateways/google-suite-gateway"
    "infrastructure/health-check"
    "infrastructure/request-logger"
    "infrastructure/error-handler"
    "infrastructure/rate-limiter"
    "monitoring/metrics-collector"
    "monitoring/alert-manager"
    "monitoring/daily-summary"
    "testing/smoke-tests"
)

# Map directory names to tag names (bash 3.2 compatible — no associative arrays)
dir_to_tag() {
    case "$1" in
        gateways)       echo "Gateway" ;;
        infrastructure) echo "Infrastructure" ;;
        monitoring)     echo "Monitoring" ;;
        testing)        echo "Testing" ;;
        *)              echo "" ;;
    esac
}

# Tag ID storage (bash 3.2 compatible — parallel arrays instead of assoc array)
TAG_NAMES_LIST=()
TAG_IDS_LIST=()

set_tag_id() {
    TAG_NAMES_LIST+=("$1")
    TAG_IDS_LIST+=("$2")
}

get_tag_id() {
    local i=0
    for name in "${TAG_NAMES_LIST[@]}"; do
        if [ "$name" = "$1" ]; then
            echo "${TAG_IDS_LIST[$i]}"
            return 0
        fi
        i=$((i + 1))
    done
    echo ""
}

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_header() {
    echo ""
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Check if a command exists
require_cmd() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found. Please install it."
        exit 1
    fi
}

# Check if jq is available (optional, for prettier output)
HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

# Pretty-print JSON if jq is available, otherwise raw output
pretty_json() {
    if $HAS_JQ; then
        echo "$1" | jq '.' 2>/dev/null || echo "$1"
    else
        echo "$1"
    fi
}

# Extract a JSON field value without jq (fallback)
# Usage: json_extract '{"id": 123}' 'id'
json_extract() {
    local json="$1"
    local field="$2"
    if $HAS_JQ; then
        echo "$json" | jq -r ".$field" 2>/dev/null
    else
        # Basic regex extraction -- works for simple flat JSON values
        echo "$json" | sed -n "s/.*\"$field\"[[:space:]]*:[[:space:]]*\"\{0,1\}\([^,\"}\]*\)\"\{0,1\}.*/\1/p" | head -1
    fi
}

# Extract JSON array of workflow names (for idempotency check)
json_extract_names() {
    local json="$1"
    if $HAS_JQ; then
        echo "$json" | jq -r '.data[].name // empty' 2>/dev/null
    else
        echo "$json" | sed 's/},{/}\n{/g' | sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
    fi
}

# Extract workflow name from a JSON file
extract_workflow_name() {
    local file="$1"
    if $HAS_JQ; then
        jq -r '.name // empty' "$file" 2>/dev/null
    else
        sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$file" | head -1
    fi
}

# Make an API call to n8n and return the response
# Usage: n8n_api GET /workflows
#        n8n_api POST /workflows --data '{"name":"test"}'
n8n_api() {
    local method="$1"
    local endpoint="$2"
    shift 2

    local url="${N8N_URL}/api/v1${endpoint}"
    local http_code
    local response
    local tmpfile

    tmpfile=$(mktemp)

    # Make the request, capture HTTP status code separately
    http_code=$(curl -s -o "$tmpfile" -w "%{http_code}" \
        -X "$method" \
        -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        "$@" \
        "$url" 2>/dev/null) || {
        rm -f "$tmpfile"
        log_error "curl failed for $method $endpoint"
        return 1
    }

    response=$(cat "$tmpfile")
    rm -f "$tmpfile"

    # Check for HTTP errors
    if [[ "$http_code" -ge 400 ]]; then
        log_error "HTTP $http_code from $method $endpoint"
        log_error "Response: $(echo "$response" | head -c 500)"
        return 1
    fi

    echo "$response"
}

# ==============================================================================
# Parse Arguments
# ==============================================================================

parse_args() {
    # Accept positional args or environment variables
    if [ $# -ge 2 ]; then
        N8N_URL="${1%/}"  # Remove trailing slash if present
        N8N_API_KEY="$2"
    elif [ $# -eq 1 ]; then
        N8N_URL="${1%/}"
        N8N_API_KEY="${N8N_API_KEY:-}"
    else
        N8N_URL="${N8N_URL:-}"
        N8N_API_KEY="${N8N_API_KEY:-}"
    fi

    # Validate required values
    if [ -z "$N8N_URL" ]; then
        log_error "N8N_URL is required. Pass as first argument or set as environment variable."
        echo ""
        echo "Usage: $0 <N8N_URL> <N8N_API_KEY>"
        echo "   or: N8N_URL=https://your-instance.app.n8n.cloud N8N_API_KEY=xxx $0"
        exit 1
    fi

    if [ -z "$N8N_API_KEY" ]; then
        log_error "N8N_API_KEY is required. Pass as second argument or set as environment variable."
        echo ""
        echo "Usage: $0 <N8N_URL> <N8N_API_KEY>"
        echo "   or: N8N_URL=https://your-instance.app.n8n.cloud N8N_API_KEY=xxx $0"
        exit 1
    fi
}

# ==============================================================================
# Core Deployment Functions
# ==============================================================================

# Step 0: Validate connectivity to n8n
validate_connection() {
    log_header "Validating n8n Connection"
    log_info "Connecting to ${N8N_URL} ..."

    local response
    if response=$(n8n_api GET /workflows "?limit=1"); then
        log_success "Connected to n8n instance at ${N8N_URL}"
        return 0
    else
        log_error "Failed to connect to n8n at ${N8N_URL}"
        log_error "Please check your N8N_URL and N8N_API_KEY."
        exit 1
    fi
}

# Step 1: Create organizational tags
create_tags() {
    log_header "Creating Tags"

    # Get existing tags
    local existing_tags_response
    existing_tags_response=$(n8n_api GET /tags) || {
        log_warn "Could not fetch existing tags. Will attempt to create all."
        existing_tags_response='{"data":[]}'
    }

    local existing_tag_names
    if $HAS_JQ; then
        existing_tag_names=$(echo "$existing_tags_response" | jq -r '.data[]?.name // empty' 2>/dev/null || echo "")
    else
        existing_tag_names=$(echo "$existing_tags_response" | sed 's/},{/}\n{/g' | sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    fi

    for tag in "${TAGS[@]}"; do
        if echo "$existing_tag_names" | grep -qx "$tag" 2>/dev/null; then
            log_info "Tag '${tag}' already exists, skipping."
        else
            local tag_response
            if tag_response=$(n8n_api POST /tags -d "{\"name\": \"${tag}\"}"); then
                local tag_id
                tag_id=$(json_extract "$tag_response" "id")
                log_success "Created tag '${tag}' (ID: ${tag_id})"
            else
                log_warn "Failed to create tag '${tag}' (may already exist)."
            fi
        fi
    done
}

# Build a lookup map of tag name -> tag ID
build_tag_map() {
    local tags_response
    tags_response=$(n8n_api GET /tags) || {
        log_warn "Could not fetch tags for mapping."
        return 1
    }

    # Reset tag ID storage
    TAG_NAMES_LIST=()
    TAG_IDS_LIST=()

    if $HAS_JQ; then
        while IFS='|' read -r name id; do
            if [ -n "$name" ] && [ -n "$id" ]; then
                set_tag_id "$name" "$id"
            fi
        done < <(echo "$tags_response" | jq -r '.data[]? | "\(.name)|\(.id)"' 2>/dev/null)
    else
        # Fallback: parse manually (best effort)
        local entries
        entries=$(echo "$tags_response" | sed 's/},{/}\n{/g')
        while IFS= read -r entry; do
            local name id
            name=$(echo "$entry" | sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
            id=$(echo "$entry" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\{0,1\}\([^,"}\]*\)\"\{0,1\}.*/\1/p')
            if [ -n "$name" ] && [ -n "$id" ]; then
                set_tag_id "$name" "$id"
            fi
        done <<< "$entries"
    fi
}

# Get existing workflow names for idempotency
get_existing_workflows() {
    log_info "Fetching existing workflows for idempotency check..."

    local response
    response=$(n8n_api GET "/workflows?limit=250") || {
        log_warn "Could not fetch existing workflows. Will attempt to create all."
        EXISTING_WORKFLOWS=""
        return
    }

    EXISTING_WORKFLOWS=$(json_extract_names "$response")
    local count
    count=$(echo "$EXISTING_WORKFLOWS" | grep -c . 2>/dev/null || echo "0")
    log_info "Found ${count} existing workflow(s) on the instance."
}

# Check if a workflow name already exists
workflow_exists() {
    local name="$1"
    if [ -z "$EXISTING_WORKFLOWS" ]; then
        return 1
    fi
    echo "$EXISTING_WORKFLOWS" | grep -qFx "$name" 2>/dev/null
}

# Determine if a workflow should be auto-activated based on its file path
should_activate() {
    local filepath="$1"
    for pattern in "${ACTIVATE_PATTERNS[@]}"; do
        if echo "$filepath" | grep -q "$pattern"; then
            return 0
        fi
    done
    return 1
}

# Get the tag name for a workflow based on its directory
get_tag_for_workflow() {
    local filepath="$1"
    local dir_name
    dir_name=$(basename "$(dirname "$filepath")")
    dir_to_tag "$dir_name"
}

# Step 2: Deploy all workflow JSON files
deploy_workflows() {
    log_header "Deploying Workflows"

    # Find the script's directory to locate workflow files
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local workflows_dir="${script_dir}/workflows"

    if [ ! -d "$workflows_dir" ]; then
        log_error "Workflows directory not found: ${workflows_dir}"
        log_error "Expected directory structure: n8n/workflows/{gateways,infrastructure,monitoring,testing}/*.json"
        exit 1
    fi

    # Collect all JSON workflow files
    local workflow_files=()
    while IFS= read -r -d '' file; do
        workflow_files+=("$file")
    done < <(find "$workflows_dir" -name "*.json" -type f -print0 2>/dev/null | sort -z)

    if [ ${#workflow_files[@]} -eq 0 ]; then
        log_warn "No workflow JSON files found in ${workflows_dir}/"
        log_info "Expected files like: workflows/gateways/main-api-gateway.json"
        log_info "Skipping workflow deployment."
        return
    fi

    log_info "Found ${#workflow_files[@]} workflow file(s) to deploy."
    echo ""

    # Get existing workflows for idempotency
    get_existing_workflows

    # Build tag ID lookup
    build_tag_map

    # Track deployment results for summary
    DEPLOYED_WORKFLOWS=()
    SKIPPED_WORKFLOWS=()
    FAILED_WORKFLOWS=()

    # Deploy each workflow
    for workflow_file in "${workflow_files[@]}"; do
        local relative_path="${workflow_file#$script_dir/}"
        local workflow_name
        workflow_name=$(extract_workflow_name "$workflow_file")

        if [ -z "$workflow_name" ]; then
            log_warn "Could not extract name from ${relative_path}, skipping."
            FAILED_WORKFLOWS+=("${relative_path}|No name found in JSON")
            continue
        fi

        echo -e "${BOLD}--- ${relative_path} ---${NC}"

        # Idempotency check: skip if workflow already exists
        if workflow_exists "$workflow_name"; then
            log_info "Workflow '${workflow_name}' already exists, skipping."
            SKIPPED_WORKFLOWS+=("${workflow_name}")
            echo ""
            continue
        fi

        # Read the workflow JSON
        local workflow_json
        workflow_json=$(cat "$workflow_file")

        # Deploy the workflow
        local create_response
        if create_response=$(n8n_api POST /workflows -d "$workflow_json"); then
            local workflow_id
            workflow_id=$(json_extract "$create_response" "id")
            log_success "Created workflow '${workflow_name}' (ID: ${workflow_id})"

            # Assign tag if applicable
            local tag_name
            tag_name=$(get_tag_for_workflow "$workflow_file")
            local tag_id_val
            tag_id_val=$(get_tag_id "$tag_name")
            if [ -n "$tag_name" ] && [ -n "$tag_id_val" ]; then
                local tag_id="$tag_id_val"
                # Update workflow with tag
                local tag_update
                if tag_update=$(n8n_api PUT "/workflows/${workflow_id}" \
                    -d "{\"name\": \"${workflow_name}\", \"tags\": [{\"id\": \"${tag_id}\", \"name\": \"${tag_name}\"}]}"); then
                    log_info "  Tagged with '${tag_name}'"
                else
                    log_warn "  Failed to tag with '${tag_name}'"
                fi
            fi

            # Activate if needed
            local is_active="false"
            if should_activate "$workflow_file"; then
                if n8n_api POST "/workflows/${workflow_id}/activate" > /dev/null 2>&1; then
                    log_success "  Activated workflow"
                    is_active="true"
                else
                    log_warn "  Failed to activate workflow"
                fi
            fi

            # Extract webhook URL if this is a webhook-triggered workflow
            local webhook_path=""
            if $HAS_JQ; then
                webhook_path=$(echo "$workflow_json" | jq -r '
                    .nodes[]? | select(.type == "n8n-nodes-base.webhook") |
                    .parameters.path // empty
                ' 2>/dev/null | head -1)
            fi

            local webhook_url=""
            if [ -n "$webhook_path" ]; then
                webhook_url="${N8N_URL}/webhook/${webhook_path}"
            fi

            DEPLOYED_WORKFLOWS+=("${workflow_name}|${workflow_id}|${is_active}|${webhook_url}|${tag_name}")
        else
            log_error "Failed to deploy '${workflow_name}'"
            FAILED_WORKFLOWS+=("${relative_path}|API error")
        fi

        echo ""
    done
}

# Step 3: Print deployment summary
print_summary() {
    log_header "Deployment Summary"

    echo -e "${BOLD}n8n Instance:${NC} ${N8N_URL}"
    echo ""

    # Deployed workflows
    if [ ${#DEPLOYED_WORKFLOWS[@]} -gt 0 ]; then
        echo -e "${GREEN}${BOLD}Deployed (${#DEPLOYED_WORKFLOWS[@]}):${NC}"
        echo ""
        printf "  ${BOLD}%-40s %-10s %-8s %-15s %s${NC}\n" "WORKFLOW" "ID" "ACTIVE" "TAG" "WEBHOOK URL"
        printf "  %-40s %-10s %-8s %-15s %s\n" "$(printf '%.0s-' {1..40})" "----------" "--------" "---------------" "---"
        for entry in "${DEPLOYED_WORKFLOWS[@]}"; do
            IFS='|' read -r name id active webhook_url tag <<< "$entry"
            local active_display
            if [ "$active" = "true" ]; then
                active_display="${GREEN}YES${NC}"
            else
                active_display="no"
            fi
            printf "  %-40s %-10s " "$name" "$id"
            echo -ne "$active_display"
            printf "     %-15s %s\n" "${tag:-—}" "${webhook_url:-—}"
        done
        echo ""
    fi

    # Skipped workflows
    if [ ${#SKIPPED_WORKFLOWS[@]} -gt 0 ]; then
        echo -e "${YELLOW}${BOLD}Skipped - Already Exist (${#SKIPPED_WORKFLOWS[@]}):${NC}"
        for name in "${SKIPPED_WORKFLOWS[@]}"; do
            echo "  - ${name}"
        done
        echo ""
    fi

    # Failed workflows
    if [ ${#FAILED_WORKFLOWS[@]} -gt 0 ]; then
        echo -e "${RED}${BOLD}Failed (${#FAILED_WORKFLOWS[@]}):${NC}"
        for entry in "${FAILED_WORKFLOWS[@]}"; do
            IFS='|' read -r file reason <<< "$entry"
            echo "  - ${file}: ${reason}"
        done
        echo ""
    fi

    # Final status
    local total=$(( ${#DEPLOYED_WORKFLOWS[@]} + ${#SKIPPED_WORKFLOWS[@]} + ${#FAILED_WORKFLOWS[@]} ))
    echo -e "${BOLD}Total: ${total} workflow(s) processed${NC}"
    echo -e "  ${GREEN}Deployed: ${#DEPLOYED_WORKFLOWS[@]}${NC}"
    echo -e "  ${YELLOW}Skipped:  ${#SKIPPED_WORKFLOWS[@]}${NC}"

    if [ ${#FAILED_WORKFLOWS[@]} -gt 0 ]; then
        echo -e "  ${RED}Failed:   ${#FAILED_WORKFLOWS[@]}${NC}"
        echo ""
        log_error "Some workflows failed to deploy. Check the errors above."
        return 1
    else
        echo -e "  ${RED}Failed:   0${NC}"
        echo ""
        log_success "Deployment complete!"
    fi
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    log_header "n8n Enterprise Deployment"
    echo -e "${BOLD}Starting deployment at $(date '+%Y-%m-%d %H:%M:%S')${NC}"

    # Pre-flight checks
    require_cmd curl
    require_cmd bash

    if ! $HAS_JQ; then
        log_warn "jq is not installed. Output will be less readable."
        log_warn "Install with: apt-get install jq  or  brew install jq"
        echo ""
    fi

    # Parse arguments and validate
    parse_args "$@"

    # Run deployment steps
    validate_connection
    create_tags
    deploy_workflows
    print_summary
}

# Run main with all script arguments
main "$@"
