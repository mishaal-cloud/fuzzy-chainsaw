#!/usr/bin/env bash
# ============================================
# export-workflows.sh — Export all workflows from n8n Cloud
#
# Pulls every workflow from your n8n instance and saves
# them as JSON files organized by tag.
#
# Cloud-first: only requires curl + jq
#
# Usage: ./n8n/export-workflows.sh [--audit-only]
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
WORKFLOWS_DIR="$SCRIPT_DIR/workflows"
ENV_FILE="$ROOT_DIR/.env"

AUDIT_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --audit-only) AUDIT_ONLY=true ;;
    --help|-h)
      echo "Usage: $0 [--audit-only]"
      echo "  --audit-only    Print audit report without saving files"
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

echo ""
echo "n8n Instance Audit — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Instance: $N8N_INSTANCE_URL"
echo ""

# ═══════════════════════════════════════════════
#  Workflows
# ═══════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════════"
echo "  Workflows"
echo "═══════════════════════════════════════════════════════════════"
echo ""

workflows=$(api_get "/workflows?limit=250") || {
  echo "[ERROR] Failed to fetch workflows"
  exit 1
}

wf_count=$(echo "$workflows" | jq '.data | length')
echo "[INFO] Found $wf_count workflow(s)"
echo ""

printf "  %-45s %-18s %-8s %s\n" "NAME" "ID" "ACTIVE" "TAGS"
printf "  %-45s %-18s %-8s %s\n" "---------------------------------------------" "------------------" "--------" "----"

echo "$workflows" | jq -r '.data[] | [.name, .id, (if .active then "YES" else "NO" end), ([.tags[]?.name] | join(", "))] | @tsv' | \
while IFS=$'\t' read -r name id active tags; do
  printf "  %-45s %-18s %-8s %s\n" "$name" "$id" "$active" "$tags"
done

# ═══════════════════════════════════════════════
#  Variables
# ═══════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Variables"
echo "═══════════════════════════════════════════════════════════════"
echo ""

variables=$(api_get "/variables?limit=250") || {
  echo "[ERROR] Failed to fetch variables"
  variables='{"data":[]}'
}

var_count=$(echo "$variables" | jq '.data | length')
echo "[INFO] Found $var_count variable(s)"
echo ""

printf "  %-35s %-8s %s\n" "KEY" "ID" "VALUE (first 40 chars)"
printf "  %-35s %-8s %s\n" "-----------------------------------" "--------" "----------------------------------------"

echo "$variables" | jq -r '.data[] | [.key, (.id | tostring), (.value[:40])] | @tsv' | \
while IFS=$'\t' read -r key id value; do
  printf "  %-35s %-8s %s\n" "$key" "$id" "$value"
done

# ═══════════════════════════════════════════════
#  Tags
# ═══════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Tags"
echo "═══════════════════════════════════════════════════════════════"
echo ""

tags=$(api_get "/tags?limit=250") || {
  echo "[ERROR] Failed to fetch tags"
  tags='{"data":[]}'
}

tag_count=$(echo "$tags" | jq '.data | length')
echo "[INFO] Found $tag_count tag(s)"
echo ""

echo "$tags" | jq -r '.data[] | "  \(.name) (ID: \(.id))"'

# ═══════════════════════════════════════════════
#  Credentials (metadata only — values are masked by n8n)
# ═══════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Credentials (metadata only)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

credentials=$(api_get "/credentials?limit=250") || {
  echo "[ERROR] Failed to fetch credentials"
  credentials='{"data":[]}'
}

cred_count=$(echo "$credentials" | jq '.data | length')
echo "[INFO] Found $cred_count credential(s)"
echo ""

printf "  %-40s %-18s %s\n" "NAME" "ID" "TYPE"
printf "  %-40s %-18s %s\n" "----------------------------------------" "------------------" "----"

echo "$credentials" | jq -r '.data[] | [.name, .id, .type] | @tsv' | \
while IFS=$'\t' read -r name id type; do
  printf "  %-40s %-18s %s\n" "$name" "$id" "$type"
done

# ═══════════════════════════════════════════════
#  Export workflows to files
# ═══════════════════════════════════════════════
if $AUDIT_ONLY; then
  echo ""
  echo "[INFO] Audit complete (--audit-only mode, no files saved)"
  exit 0
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Exporting Workflow Files"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Tag-to-directory mapping
declare -A TAG_DIR_MAP=(
  ["Infrastructure"]="infrastructure"
  ["Gateway"]="gateways"
  ["Monitoring"]="monitoring"
  ["Testing"]="testing"
  ["SEO-Pipeline"]="seo-pipeline"
)

exported=0

echo "$workflows" | jq -c '.data[]' | while read -r wf; do
  local_id=$(echo "$wf" | jq -r '.id')
  local_name=$(echo "$wf" | jq -r '.name')

  # Get full workflow with nodes
  full_wf=$(api_get "/workflows/$local_id") || {
    echo "[WARN] Failed to fetch full workflow: $local_name"
    continue
  }

  # Determine directory from first tag
  first_tag=$(echo "$wf" | jq -r '(.tags // [])[0].name // empty')
  dir_name="${TAG_DIR_MAP[$first_tag]:-uncategorized}"

  # Create safe filename from workflow name
  safe_name=$(echo "$local_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')

  # Ensure directory exists
  mkdir -p "$WORKFLOWS_DIR/$dir_name"

  # Save workflow (remove volatile fields)
  echo "$full_wf" | jq 'del(.id, .createdAt, .updatedAt, .versionId)' > "$WORKFLOWS_DIR/$dir_name/$safe_name.json"
  echo "[OK] Exported: $dir_name/$safe_name.json"
  ((exported++)) || true
done

echo ""
echo "[INFO] Exported $exported workflow(s) to $WORKFLOWS_DIR/"
echo "[INFO] Run 'git status' to see new files."
