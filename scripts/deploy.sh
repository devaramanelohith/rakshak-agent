#!/usr/bin/env bash
# Deploy Rakshak to Cloud Run. Call sessions live in memory, so the demo runs ONE instance (max-instances 1);
# cases/profiles/alerts are already durable in Firestore; for horizontal scale move live sessions to Memorystore first (docs/ARCHITECTURE.md). Prereqs: gcloud auth login; a project with billing; the Gemini key in Secret Manager.
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
# Firestore (native mode, database "(default)") holds cases, profiles and alerts; create it once if missing.
if [ "${USE_FIRESTORE:-true}" = "true" ] && ! gcloud firestore databases describe --database="(default)" --project "$PROJECT" >/dev/null 2>&1; then
  gcloud firestore databases create --location="$REGION" --type=firestore-native --project "$PROJECT"
fi

# The Cloud Run runtime service account must be able to read the secret and call Vertex AI.
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format 'value(projectNumber)')
RUNTIME_SA="${RUNTIME_SA:-$PROJECT_NUMBER-compute@developer.gserviceaccount.com}"
gcloud secrets add-iam-policy-binding "$SECRET" --project "$PROJECT" --member "serviceAccount:$RUNTIME_SA" --role roles/secretmanager.secretAccessor >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$RUNTIME_SA" --role roles/aiplatform.user >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$RUNTIME_SA" --role roles/datastore.user --condition=None >/dev/null

# Text/agents/TTS go through Vertex (no daily free-tier cap); the Live API uses the AI Studio key from the secret.
ENV_VARS="GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION:-global},GOOGLE_GENAI_USE_VERTEXAI=true,PUBSUB_ALERT_TOPIC=rakshak-alerts,USE_FIRESTORE=${USE_FIRESTORE:-true}"
[ -n "${BIGQUERY_PAYEE_TABLE:-}" ] && ENV_VARS="$ENV_VARS,BIGQUERY_PAYEE_TABLE=$BIGQUERY_PAYEE_TABLE"
[ -n "${TWILIO_DIAL_NUMBER:-}" ] && ENV_VARS="$ENV_VARS,TWILIO_DIAL_NUMBER=$TWILIO_DIAL_NUMBER"

gcloud run deploy "$SERVICE" --source . --quiet --project "$PROJECT" --region "$REGION" \
  --allow-unauthenticated --port 8080 --cpu 1 --memory 1Gi --concurrency 40 \
  --min-instances "${MIN_INSTANCES:-1}" --max-instances "${MAX_INSTANCES:-1}" --timeout 3600 \
  --session-affinity --set-env-vars "$ENV_VARS" --set-secrets "GEMINI_API_KEY=$SECRET:latest"

URL=$(gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format 'value(status.url)')
gcloud run services update "$SERVICE" --project "$PROJECT" --region "$REGION" --update-env-vars "PUBLIC_BASE_URL=$URL" >/dev/null
echo "Deployed: $URL   (victim app: $URL/  scammer console: $URL/scammer  fraud desk: $URL/desk)"
