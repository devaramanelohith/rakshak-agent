# Deploying Rakshak to Google Cloud

Copy-pasteable steps for a judge-visible deployment on Cloud Run, then the optional services. Commands assume a Unix shell with `gcloud`, `uv` and `jq` installed.

## 1. Prerequisites

* A Google Cloud project with billing enabled. The current working project id on this machine is `fde-cloud-run-lab-123456`, which is a lab project; a fresh project for the submission is recommended so quotas, IAM and costs are isolated.
* `gcloud` CLI authenticated (`gcloud auth login`), and `gcloud auth application-default login` if you will run `scripts/load_bigquery.py` locally.
* A Gemini API key from AI Studio (free tier is enough for the demo), or the Vertex AI alternative in step 3b.
* Python 3.12 and `uv` for local tests.

```bash
gcloud auth login
# optional: fresh project
gcloud projects create rakshak-cup-2026 --name="Rakshak"
gcloud billing projects link rakshak-cup-2026 --billing-account=XXXXXX-XXXXXX-XXXXXX
gcloud config set project rakshak-cup-2026

export PROJECT=$(gcloud config get-value project)
export REGION=asia-southeast1
export PN=$(gcloud projects describe "$PROJECT" --format 'value(projectNumber)')
export RUN_SA="${PN}-compute@developer.gserviceaccount.com"   # Cloud Run's default runtime service account
```

## 2. Enable the APIs

`scripts/deploy.sh` runs this line itself; run it now so the IAM steps below do not fail.

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com firestore.googleapis.com pubsub.googleapis.com bigquery.googleapis.com \
  aiplatform.googleapis.com --project "$PROJECT"
```

## 3a. Gemini API key in Secret Manager

```bash
export GEMINI_API_KEY=<paste the AI Studio key>
printf '%s' "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=- --project "$PROJECT"
# the deploy script mounts it as GEMINI_API_KEY=gemini-api-key:latest; the runtime SA must be able to read it
gcloud secrets add-iam-policy-binding gemini-api-key --project "$PROJECT" \
  --member="serviceAccount:${RUN_SA}" --role=roles/secretmanager.secretAccessor
# rotate later with:
# printf '%s' "$NEW_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
```

`deploy.sh` creates the secret for you from `$GEMINI_API_KEY` if it does not exist, but it does not grant the accessor role; do it once as above.

Quota note: a free AI Studio key has small daily request caps on the 3.x models (one rehearsal can exhaust `gemini-3.8-flash`; see section 6 of `docs/DEMO_STRATEGY.md`). Before recording or judging, either enable billing on the AI Studio project or move text, TTS and agent traffic to Vertex AI as in 3b.

## 3b. Alternative: Vertex AI / Agent Platform endpoints with the $300 trial

The $300 trial credit applies to Vertex AI usage, not to AI Studio keys. With `GOOGLE_GENAI_USE_VERTEXAI=true` the rubric, TTS, ADK agents, Search grounding and narrative use Vertex AI through the runtime service account (`config.llm_enabled()` is true without a key). The two Live API models (`gemini-3.5-transcribe-live` for transcription and `gemini-3.8-live` for the post-hold conversation) are published under those ids on the Gemini API, so `app/llm.py` `live_client()` keeps using the AI Studio key for them unless `RAKSHAK_LIVE_VIA_VERTEX=1` is set, which has not been exercised. Keep the secret mounted in this mode; `/api/health` reports `live: false` when neither is available and audio transcription is then disabled (the transcript-driven path still works).

```bash
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${RUN_SA}" --role=roles/aiplatform.user
PROJECT=$PROJECT REGION=$REGION ./scripts/deploy.sh      # deploys with the secret mounted, as in step 4
gcloud run services update rakshak --project "$PROJECT" --region "$REGION" \
  --update-env-vars "GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_LOCATION=global"
```

`GOOGLE_CLOUD_LOCATION` is the Vertex model location, separate from the Cloud Run region. `app/config.py` defaults it to `global`, but `deploy.sh` sets it to `$REGION`; override it to `global` (as above) unless you have confirmed every model id is served in `$REGION`. The model ids in `app/config.py` were verified against the Gemini API on 2026-10-10, not against Vertex AI; run `scripts/smoke_agent.py` locally with the same env to exercise the rubric, TTS and ADK paths through Vertex before relying on it. For a local run without Application Default Credentials, `RAKSHAK_ACCESS_TOKEN=$(gcloud auth print-access-token)` in `.env` makes `client()` use that short-lived token; never set it on Cloud Run.

## 4. Deploy with `scripts/deploy.sh`

```bash
cd rakshak-agent
uv run pytest                                            # 16 offline tests
PROJECT=$PROJECT REGION=$REGION GEMINI_API_KEY=$GEMINI_API_KEY ./scripts/deploy.sh
```

Environment variables the script reads:

| Variable | Default | Effect |
|---|---|---|
| `PROJECT` | `gcloud config get-value project` | Target project |
| `REGION` | `asia-southeast1` | Cloud Run region |
| `SERVICE` | `rakshak` | Service name |
| `SECRET` | `gemini-api-key` | Secret Manager secret holding the key |
| `GEMINI_API_KEY` | required only if the secret does not exist yet | Used to create the secret |
| `USE_FIRESTORE` | `false` | Passed to the service |
| `BIGQUERY_PAYEE_TABLE` | unset | Passed to the service when set |
| `TWILIO_DIAL_NUMBER` | unset | Passed to the service when set |
| `MIN_INSTANCES` / `MAX_INSTANCES` | `1` / `10` | Autoscaling bounds |

What it does: enables the APIs, creates the secret if missing, creates the `rakshak-alerts` topic (idempotent), runs `gcloud run deploy --source .` (Cloud Build builds the `Dockerfile`: `python:3.12-slim`, `uv sync --extra gcp`, `uvicorn --ws websockets`), sets `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` (to `$REGION`; only relevant when Vertex is selected, see 3b), `PUBSUB_ALERT_TOPIC`, `USE_FIRESTORE`, mounts the secret, then reads the service URL and writes it back as `PUBLIC_BASE_URL` (used by the Twilio TwiML to build the `wss://` stream URL). The last line prints the three URLs.

## 5. Verify

```bash
export URL=$(gcloud run services describe rakshak --project "$PROJECT" --region "$REGION" --format 'value(status.url)')
curl -s "$URL/api/health" | jq
# expect: {"ok":true,"llm":true,"live":true,"vertex":false,"project":null,"models":{"rubric":"gemini-3.5-flash","transcribe":"gemini-3.5-transcribe-live","tts":"gemini-3.8-flash-tts","live":"gemini-3.8-live","agent":"gemini-3.8-flash"},...}
gcloud run services logs read rakshak --project "$PROJECT" --region "$REGION" --limit 50 | grep -E "prewarmed|Using FirestoreStore|Firestore unavailable"
```

Then run the curl flow from the README ("Flow 3") against `$URL`, and open `$URL/`, `$URL/scammer`, `$URL/desk` in a browser. The pages need a secure context for the microphone; the `run.app` URL is HTTPS, so this works out of the box. If `llm` is `false`, the secret did not mount: check the IAM binding from step 3a and the revision's environment in the console. If `llm` is `true` but `live` is `false`, Vertex is selected without an AI Studio key, so audio transcription and the post-hold conversation are off (see 3b).

## 6. Firestore (native mode) for durable cases

```bash
gcloud firestore databases create --location="$REGION" --type=firestore-native --project "$PROJECT"
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${RUN_SA}" --role=roles/datastore.user
gcloud run services update rakshak --project "$PROJECT" --region "$REGION" --update-env-vars USE_FIRESTORE=true
# or redeploy: USE_FIRESTORE=true ./scripts/deploy.sh
```

The app uses the `(default)` database and the collections `rakshak_cases`, `rakshak_profiles`, `rakshak_alerts` (prefix from `FIRESTORE_PREFIX`). On startup it loads existing cases and profiles, then writes through on every change. The log line `Using FirestoreStore` confirms it; `Firestore unavailable (...)` means it fell back to the in-memory JSON store, usually an IAM or database-not-created problem.

## 7. BigQuery payee risk table

Load the 60 synthetic payees into BigQuery and point the service at the table. The lookup is one parameterised query per payment; on any error it falls back to the local JSON.

```bash
uv sync --extra gcp
gcloud auth application-default login
uv run python scripts/load_bigquery.py --project "$PROJECT" --dataset rakshak --table payee_risk --location "$REGION"
# prints: loaded 60 rows into <project>.rakshak.payee_risk  and  export BIGQUERY_PAYEE_TABLE=<project>.rakshak.payee_risk

gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${RUN_SA}" --role=roles/bigquery.jobUser
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${RUN_SA}" --role=roles/bigquery.dataViewer
gcloud run services update rakshak --project "$PROJECT" --region "$REGION" \
  --update-env-vars "BIGQUERY_PAYEE_TABLE=${PROJECT}.rakshak.payee_risk"
curl -s "$URL/api/payees/cbi.verification@rakshakdemo" | jq .source     # "bigquery"
```

Production feature engineering: `sql/payee_risk.sql` builds the same table from a transaction ledger (`payer_vpa, payee_vpa, amount_inr, ts, channel`) joined with a telecom FRI feed, 1930 complaint counts and KYC tiers; replace the `project.rakshak.*` table names and run it on a schedule.

BigQuery `AI.GENERATE` for fraud-desk records (`sql/narrative_ai_generate.sql`) is a documented path, not executed by the app. It needs a cases table and a BigQuery connection to Vertex AI:

```bash
bq mk --connection --location="$REGION" --project_id="$PROJECT" --connection_type=CLOUD_RESOURCE vertex_conn
CONN_SA=$(bq show --format=json --connection "$PROJECT.$REGION.vertex_conn" | jq -r .cloudResource.serviceAccountId)
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${CONN_SA}" --role=roles/aiplatform.user
# load cases (for example an export of data/runtime/cases.json or Firestore) into <project>.rakshak.cases, then run the SQL
```

## 8. Pub/Sub alerts and a sample subscriber

`deploy.sh` creates the topic and sets `PUBSUB_ALERT_TOPIC=rakshak-alerts`. Grant publish rights and add a subscription to see the alerts:

```bash
gcloud pubsub topics create rakshak-alerts --project "$PROJECT" 2>/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${RUN_SA}" --role=roles/pubsub.publisher
gcloud pubsub subscriptions create rakshak-alerts-desk --topic rakshak-alerts --project "$PROJECT"
# trigger a hold_and_alert (README Flow 1 or Flow 3), then:
gcloud pubsub subscriptions pull rakshak-alerts-desk --auto-ack --limit 5 --project "$PROJECT"
```

Messages carry the attribute `event_type=trusted_contact_alert` and a JSON body with `alert_id`, `case_id`, `user_id`, `contact_name`, `contact_phone`, `message`, `created_at`, `channels`. A minimal Python subscriber for an SMS or push sender:

```python
from google.cloud import pubsub_v1
import json, os

sub = pubsub_v1.SubscriberClient()
path = sub.subscription_path(os.environ["PROJECT"], "rakshak-alerts-desk")

def handle(msg):
    alert = json.loads(msg.data)
    print(alert["contact_name"], alert["contact_phone"], alert["message"])  # send SMS / push here
    msg.ack()

sub.subscribe(path, callback=handle).result()
```

On the hold screen and in `/api/alerts`, `channels` contains `pubsub` when the publish succeeded.

## 9. Optional: Twilio real phone number

1. Buy a voice-capable number in the Twilio console.
2. Set its Voice webhook to `HTTP POST` `https://<your-run-url>/twilio/voice?session=phone`.
3. Set the phone Twilio should dial as the "scammer" leg and, optionally, the SMS credentials for trusted-contact alerts. Keep the auth token in Secret Manager:

```bash
printf '%s' "$TWILIO_AUTH_TOKEN" | gcloud secrets create twilio-auth-token --data-file=- --project "$PROJECT"
gcloud secrets add-iam-policy-binding twilio-auth-token --project "$PROJECT" --member="serviceAccount:${RUN_SA}" --role=roles/secretmanager.secretAccessor
gcloud run services update rakshak --project "$PROJECT" --region "$REGION" \
  --update-env-vars "TWILIO_DIAL_NUMBER=+91XXXXXXXXXX,TWILIO_ACCOUNT_SID=ACxxxx,TWILIO_FROM_NUMBER=+1XXXXXXXXXX" \
  --update-secrets "TWILIO_AUTH_TOKEN=twilio-auth-token:latest"
```

`PUBLIC_BASE_URL` is already set by `deploy.sh`; the TwiML uses it to build `wss://<host>/ws/twilio/phone`. Open `https://<your-run-url>/?session=phone` on the victim app, call the Twilio number from the victim's phone: Twilio says "Rakshak guardian mode is on for this call", dials `TWILIO_DIAL_NUMBER`, and forks both tracks (inbound = victim = `user`, outbound = dialed party = `caller`) to the bridge. Without `TWILIO_DIAL_NUMBER` the TwiML pauses for 600 s so a single caller is transcribed as the victim leg. The Media Stream is a one-way fork, so the hold voice plays on the app device, not into the phone call.

## 10. Optional: ngrok for local Twilio testing

```bash
uv run uvicorn app.main:app --port 8080
ngrok http 8080                                   # note the https://xxxx.ngrok.app URL
# in .env:  PUBLIC_BASE_URL=https://xxxx.ngrok.app  (restart uvicorn)
# Twilio Voice webhook: https://xxxx.ngrok.app/twilio/voice?session=phone
```

## 11. Custom domain or Firebase Hosting front

The pages compute the WebSocket base from `location.host` (`web/common.js`), so the pages and the WebSocket endpoints must be served from the same host.

* **Cloud Run domain mapping** (simplest, keeps WebSockets):
  `gcloud beta run domain-mappings create --service rakshak --domain rakshak.example.com --region "$REGION" --project "$PROJECT"` and add the DNS records it prints.
* **Firebase Hosting rewrite to Cloud Run**: `firebase.json` with `{"hosting": {"rewrites": [{"source": "**", "run": {"serviceId": "rakshak", "region": "asia-southeast1"}}]}}`. Firebase Hosting rewrites do not carry WebSocket connections, so with this front the three `/ws/*` paths would need to point at the `run.app` host (a one-line change to `WS_BASE` in `web/common.js`) and CORS stays open. Prefer the domain mapping or a global external HTTPS load balancer with a serverless NEG, both of which pass WebSockets through.

## 12. Cost estimate per demo session

Order-of-magnitude only; check the current pricing pages before quoting.

* **Cloud Run**: with `--min-instances 1` at 1 vCPU / 1 GiB the always-on instance is the dominant cost (tens of USD per month if left running); set `MIN_INSTANCES=0` outside demo windows to pay only per request.
* **Gemini, per 3-minute scam demo**: two Live transcription sessions of about 3 minutes each, roughly 10 to 20 rubric calls of a few thousand tokens on `gemini-3.5-flash`, one TTS synthesis on a cache miss (none on the prewarmed profiles), one ADK run (two agents, two to three tool calls, a few thousand tokens on `gemini-3.8-flash`), one narrative call, and an optional one-minute `gemini-3.8-live` conversation. At flash-tier list prices this is well under one US dollar per session, and zero on the AI Studio free tier within its rate limits.
* **Firestore, Pub/Sub, BigQuery**: a few documents, a few messages and a 60-row table per session; within free tiers.
* **Twilio**: per-minute voice for two legs plus the number rental.

## 13. Scaling knobs

| Knob | Where | Note |
|---|---|---|
| `--concurrency 40` | `deploy.sh` | Requests per instance; WebSockets count as long requests, so size for simultaneous calls times 3 sockets |
| `--min-instances` / `--max-instances` | `MIN_INSTANCES`, `MAX_INSTANCES` | Keep at least 1 during judging so TTS prewarm and ADK runners are warm |
| `--timeout 3600` | `deploy.sh` | Required for WebSockets; Cloud Run closes a request after 60 minutes, and the browser pages reconnect the event socket automatically |
| `--session-affinity` | `deploy.sh` | Keeps a phone and its caller console on the instance that owns the `CallSession` |
| `--cpu 1 --memory 1Gi` | `deploy.sh` | Audio resampling is light; raise memory if many parallel Live sessions |
| `--no-cpu-throttling` | not set | Background work after the response (agent follow-up, narrative, hold expiry loop) runs while event sockets are open; set this for production so CPU is always allocated |
| `RAKSHAK_AGENT_SYNC_WAIT_S` | env | Seconds `/api/payments` waits for the agent (default 6) |
| `RAKSHAK_AGENT_TIMEOUT_S` | env | Agent hard timeout (default 60) |
| `RAKSHAK_PREWARM_TTS` | env | Set `0` to skip startup synthesis |

## 14. Monitoring

* **Cloud Logging**: all `rakshak.*` loggers write to stdout; useful filters are `"generate_json"` (rubric and narrative failures and retries), `"transcriber["` (Live reconnects), `"ADK run failed"`, `"hold expired"`, `"Pub/Sub publish failed"`. Tail with `gcloud run services logs tail rakshak --region "$REGION" --project "$PROJECT"`.
* **Cloud Run metrics**: request latency, instance count, container CPU and memory, and open WebSocket connections per instance in the console.
* **Uptime check**: `GET /api/health` returns `ok: true` and `llm: true`.
* **Agent observability**: in this prototype every ADK event is captured per case (`case.trace`) and rendered on `/desk`. When the pipeline moves to Vertex AI Agent Runtime, Agent Observability (traces, tool-call spans, token usage) replaces the hand-rolled trace.

## 15. Rollback

```bash
gcloud run revisions list --service rakshak --region "$REGION" --project "$PROJECT"
gcloud run services update-traffic rakshak --region "$REGION" --project "$PROJECT" --to-revisions <previous-revision>=100
```

To roll back a key, pin the secret version: `--update-secrets "GEMINI_API_KEY=gemini-api-key:<version>"`. With the in-memory store, cases live in the container filesystem and are lost on every new revision; with Firestore they persist across rollbacks.
