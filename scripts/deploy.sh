#!/usr/bin/env bash
# Deploy Rakshak to Cloud Run. Prereqs: gcloud auth login; a project with billing; the Gemini key in Secret Manager.
#   PROJECT=my-proj REGION=asia-southeast1 ./scripts/deploy.sh
set -euo pipefail
PROJECT="${PROJECT:-$(gcloud config get-value project)}"
REGION="${REGION:-asia-southeast1}"
SERVICE="${SERVICE:-rakshak}"
SECRET="${SECRET:-gemini-api-key}"

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com \
  firestore.googleapis.com pubsub.googleapis.com bigquery.googleapis.com aiplatform.googleapis.com --project "$PROJECT"

if ! gcloud secrets describe "$SECRET" --project "$PROJECT" >/dev/null 2>&1; then
  echo "Creating secret $SECRET from \$GEMINI_API_KEY"; : "${GEMINI_API_KEY:?set GEMINI_API_KEY}"
  printf '%s' "$GEMINI_API_KEY" | gcloud secrets create "$SECRET" --data-file=- --project "$PROJECT"
fi
gcloud pubsub topics create rakshak-alerts --project "$PROJECT" 2>/dev/null || true

ENV_VARS="GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=$REGION,PUBSUB_ALERT_TOPIC=rakshak-alerts,USE_FIRESTORE=${USE_FIRESTORE:-false}"
[ -n "${BIGQUERY_PAYEE_TABLE:-}" ] && ENV_VARS="$ENV_VARS,BIGQUERY_PAYEE_TABLE=$BIGQUERY_PAYEE_TABLE"
[ -n "${TWILIO_DIAL_NUMBER:-}" ] && ENV_VARS="$ENV_VARS,TWILIO_DIAL_NUMBER=$TWILIO_DIAL_NUMBER"

gcloud run deploy "$SERVICE" --source . --project "$PROJECT" --region "$REGION" \
  --allow-unauthenticated --port 8080 --cpu 1 --memory 1Gi --concurrency 40 \
  --min-instances "${MIN_INSTANCES:-1}" --max-instances "${MAX_INSTANCES:-10}" --timeout 3600 \
  --session-affinity --set-env-vars "$ENV_VARS" --set-secrets "GEMINI_API_KEY=$SECRET:latest"

URL=$(gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format 'value(status.url)')
gcloud run services update "$SERVICE" --project "$PROJECT" --region "$REGION" --update-env-vars "PUBLIC_BASE_URL=$URL" >/dev/null
echo "Deployed: $URL   (victim app: $URL/  scammer console: $URL/scammer  fraud desk: $URL/desk)"
