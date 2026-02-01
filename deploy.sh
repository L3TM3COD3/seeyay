#!/bin/bash
# Manual deployment script for СИЯЙ AI to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-europe-west4}"
BOT_SERVICE="seeyay-bot"
API_SERVICE="seeyay-api"
MINIAPP_SERVICE="seeyay-mini-app"

echo "🚀 Deploying СИЯЙ AI to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com

# Create secrets if they don't exist
echo "🔐 Setting up secrets..."
if ! gcloud secrets describe bot-token --project=$PROJECT_ID &>/dev/null; then
    echo "Creating bot-token secret..."
    echo -n "Enter your Telegram Bot Token: "
    read -s BOT_TOKEN
    echo ""
    echo -n "$BOT_TOKEN" | gcloud secrets create bot-token --data-file=- --project=$PROJECT_ID
fi

# Build and deploy using Cloud Build
echo "🔨 Starting Cloud Build..."
gcloud builds submit . --config=cloudbuild.yaml --project=$PROJECT_ID

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Service URLs:"
gcloud run services describe $BOT_SERVICE --region=$REGION --format='value(status.url)' --project=$PROJECT_ID
gcloud run services describe $API_SERVICE --region=$REGION --format='value(status.url)' --project=$PROJECT_ID
gcloud run services describe $MINIAPP_SERVICE --region=$REGION --format='value(status.url)' --project=$PROJECT_ID
echo ""
echo "Don't forget to:"
echo "1. Configure the Mini App URL in @BotFather"
echo "2. Update the API URL in the Mini App configuration"
