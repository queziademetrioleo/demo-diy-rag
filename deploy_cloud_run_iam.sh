#!/bin/bash
# Deploy FAQ Chatbot API to Cloud Run with IAM authentication (recommended for certification)

set -e

# ============================
# REQUIRED ENVIRONMENT CHECK
# ============================
if [[ -z "${PROJECT_ID}" ]]; then
  echo "❌ ERROR: PROJECT_ID environment variable is not set."
  echo ""
  echo "Set it before running the script:"
  echo "  export PROJECT_ID=my-gcp-project-id"
  echo ""
  exit 1
fi

# ============================
# CONFIGURATION
# ============================
REGION="us-central1"
SERVICE_NAME="faq-chatbot-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
BUCKET_NAME="${PROJECT_ID}-data"

echo "======================================================================"
echo "DEPLOYING FAQ CHATBOT API TO CLOUD RUN (IAM AUTHENTICATED)"
echo "======================================================================"
echo ""
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "Authentication: IAM (Service Account required)"
echo ""

# ============================
# AUTH CHECK
# ============================
echo "1️⃣  Checking authentication..."
gcloud auth list

# ============================
# SET PROJECT (FROM ENV)
# ============================
echo -e "\n2️⃣  Setting project from environment..."
gcloud config set project "${PROJECT_ID}"

# ============================
# ENABLE APIS
# ============================
echo -e "\n3️⃣  Enabling required APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  aiplatform.googleapis.com \
  containerregistry.googleapis.com

# ============================
# BUILD IMAGE
# ============================
echo -e "\n4️⃣  Building container image..."
gcloud builds submit --tag "${IMAGE_NAME}"

# ============================
# DEPLOY CLOUD RUN (IAM)
# ============================
echo -e "\n5️⃣  Deploying to Cloud Run (IAM authenticated)..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID="${PROJECT_ID}" \
  --set-env-vars BUCKET_NAME="${BUCKET_NAME}" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# ============================
# GET SERVICE URL
# ============================
echo -e "\n6️⃣  Getting service URL..."
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --format 'value(status.url)')

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT SUCCESSFUL (IAM AUTHENTICATED)"
echo "======================================================================"
echo ""
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "⚠️  This service requires authentication"
echo ""
echo "Test example:"
echo ""
echo "TOKEN=\$(gcloud auth print-identity-token)"
echo ""
echo "curl ${SERVICE_URL}/health \\"
echo "  -H \"Authorization: Bearer \$TOKEN\""
echo ""
echo "curl -X POST ${SERVICE_URL}/ask \\"
echo "  -H \"Authorization: Bearer \$TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"question\": \"How do I reset my password?\"}'"
echo ""
echo "======================================================================"
echo "📋 Google Cloud Gen AI Certification Checklist"
echo "======================================================================"
echo "✔ Cloud Run service deployed"
echo "✔ IAM authentication enforced"
echo "✔ Vertex AI compatible"
echo "✔ Network-accessible endpoint"
echo ""
echo "Submit this URL: ${SERVICE_URL}"
echo "======================================================================"
