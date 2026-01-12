#!/bin/bash
# Deploy FAQ Chatbot API to Cloud Run

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-teste-de-big-query-472216}"
REGION="us-central1"
SERVICE_NAME="faq-chatbot-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "======================================================================"
echo "DEPLOYING FAQ CHATBOT API TO CLOUD RUN"
echo "======================================================================"
echo ""
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
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

# Deploy to Cloud Run
echo -e "\n5️⃣  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
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
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "======================================================================"
echo ""
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test endpoints:"
echo "  Health check:"
echo "    curl ${SERVICE_URL}/health"
echo ""
echo "  Ask question:"
echo "    curl -X POST ${SERVICE_URL}/ask \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"question\": \"How do I reset my password?\"}'"
echo ""
echo "======================================================================"
