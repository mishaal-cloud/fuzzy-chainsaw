#!/usr/bin/env bash
set -euo pipefail

# ── AI Due Diligence — Google Cloud Run Deployment ──────────────────
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. A GCP project with billing enabled
#   3. Your Anthropic API key
#
# Usage:
#   ./deploy.sh                    # Deploy with defaults
#   ./deploy.sh --project my-proj  # Specify GCP project
# ────────────────────────────────────────────────────────────────────

# Configuration (override with env vars or flags)
PROJECT_ID="${GCP_PROJECT:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-ai-due-diligence}"
IMAGE_NAME="${IMAGE_NAME:-ai-due-diligence}"

# Parse flags
while [[ $# -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift 2 ;;
        --region)  REGION="$2"; shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

# Validate
if [[ -z "$PROJECT_ID" ]]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
    if [[ -z "$PROJECT_ID" ]]; then
        echo "Error: No GCP project set. Use --project <id> or 'gcloud config set project <id>'"
        exit 1
    fi
fi

echo "═══════════════════════════════════════════════════════"
echo "  AI Due Diligence — Cloud Run Deployment"
echo "═══════════════════════════════════════════════════════"
echo "  Project:  $PROJECT_ID"
echo "  Region:   $REGION"
echo "  Service:  $SERVICE_NAME"
echo "═══════════════════════════════════════════════════════"
echo

# Step 1: Enable required APIs
echo "[1/5] Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project="$PROJECT_ID" \
    --quiet

# Step 2: Create Artifact Registry repo (if not exists)
echo "[2/5] Setting up Artifact Registry..."
gcloud artifacts repositories describe docker-repo \
    --location="$REGION" \
    --project="$PROJECT_ID" 2>/dev/null || \
gcloud artifacts repositories create docker-repo \
    --repository-format=docker \
    --location="$REGION" \
    --project="$PROJECT_ID" \
    --quiet

# Step 3: Build and push container image
FULL_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/docker-repo/${IMAGE_NAME}:latest"
echo "[3/5] Building and pushing container image..."
echo "  Image: $FULL_IMAGE"
gcloud builds submit \
    --tag="$FULL_IMAGE" \
    --project="$PROJECT_ID" \
    --quiet

# Step 4: Create secret for Anthropic API key (if not exists)
echo "[4/5] Setting up secrets..."
if ! gcloud secrets describe anthropic-api-key --project="$PROJECT_ID" 2>/dev/null; then
    echo "  Creating secret 'anthropic-api-key'..."
    echo "  Enter your Anthropic API key (sk-ant-xxxxx):"
    read -rs ANTHROPIC_KEY
    echo -n "$ANTHROPIC_KEY" | gcloud secrets create anthropic-api-key \
        --data-file=- \
        --project="$PROJECT_ID"
    echo "  Secret created."
else
    echo "  Secret 'anthropic-api-key' already exists."
fi

if ! gcloud secrets describe admin-secret --project="$PROJECT_ID" 2>/dev/null; then
    ADMIN_SEC=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo -n "$ADMIN_SEC" | gcloud secrets create admin-secret \
        --data-file=- \
        --project="$PROJECT_ID"
    echo "  Admin secret created: $ADMIN_SEC"
    echo "  (Save this — you'll need it to create API keys via the /admin/create-key endpoint)"
else
    echo "  Secret 'admin-secret' already exists."
fi

# Get the service account for Cloud Run
SA_EMAIL="${PROJECT_ID}@appspot.gserviceaccount.com"
COMPUTE_SA="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')-compute@developer.gserviceaccount.com"

# Grant secret access
for SECRET_NAME in anthropic-api-key admin-secret; do
    gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" \
        --quiet 2>/dev/null || true
done

# Step 5: Deploy to Cloud Run
echo "[5/5] Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image="$FULL_IMAGE" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --platform=managed \
    --allow-unauthenticated \
    --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=600 \
    --concurrency=10 \
    --min-instances=1 \
    --max-instances=5 \
    --no-cpu-throttling \
    --execution-environment=gen2 \
    --quiet

# Get the URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(status.url)")

echo
echo "═══════════════════════════════════════════════════════"
echo "  Deployment complete!"
echo "═══════════════════════════════════════════════════════"
echo
echo "  Web App:  $SERVICE_URL"
echo
echo "  Open the URL above in your browser and enter a company URL to analyze."
echo
