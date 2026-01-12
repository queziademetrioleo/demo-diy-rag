#!/bin/bash
# Deploy FAQ Chatbot API to Cloud Run with IAM authentication (recommended for certification)

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-teste-de-big-query-472216}"
REGION="us-central1"
SERVICE_NAME="faq-chatbot-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "======================================================================"
echo "DEPLOYING FAQ CHATBOT API TO CLOUD RUN (IAM AUTHENTICATED)"
echo "======================================================================"
echo ""
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "Authentication: IAM (Service Account required)"
echo ""

# Check if gcloud is authenticated
echo "1️⃣  Checking authentication..."
gcloud auth list

# Set project
echo -e "\n2️⃣  Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "\n3️⃣  Enabling required APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  aiplatform.googleapis.com \
  containerregistry.googleapis.com

# Build container image
echo -e "\n4️⃣  Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run with IAM authentication
echo -e "\n5️⃣  Deploying to Cloud Run (IAM authenticated)..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=${PROJECT_ID} \
  --set-env-vars BUCKET_NAME=${PROJECT_ID}-data \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# Get service URL
echo -e "\n6️⃣  Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT SUCCESSFUL (IAM AUTHENTICATED)!"
echo "======================================================================"
echo ""
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "⚠️  This service requires authentication!"
echo ""
echo "To test, you need to:"
echo ""
echo "1. Get authentication token:"
echo "   TOKEN=\$(gcloud auth print-identity-token)"
echo ""
echo "2. Test with token:"
echo "   curl ${SERVICE_URL}/health \\"
echo "     -H \"Authorization: Bearer \$TOKEN\""
echo ""
echo "   curl -X POST ${SERVICE_URL}/ask \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"question\": \"How do I reset my password?\"}'"
echo ""
echo "3. Grant access to others (optional):"
echo "   gcloud run services add-iam-policy-binding ${SERVICE_NAME} \\"
echo "     --region=${REGION} \\"
echo "     --member='user:estagiaria@example.com' \\"
echo "     --role='roles/run.invoker'"
echo ""
echo "======================================================================"
echo ""
echo "📋 For Google Cloud Gen AI certification:"
echo "   - Service is deployed ✅"
echo "   - Uses Vertex AI (gemini-2.5-flash + text-embedding-004) ✅"
echo "   - Has network-accessible endpoint ✅"
echo "   - Protected by IAM authentication ✅"
echo ""
echo "Submit this URL for certification: ${SERVICE_URL}"
echo "======================================================================"
