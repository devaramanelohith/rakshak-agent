# Rakshak: implementation, demo and submission plan (15 to 18 October 2026)

This is the working document for the last three days: what exists, what gets built, how every technical part works, what the demo shows, and exactly what to submit.

## 1. Scope freeze

**Ship this, nothing more.** The prototype already runs end to end on Cloud Run. The remaining work closes the three credibility gaps judges will see (hand-typed risk table, perfect eval on self-written calls, no real-phone recording) and raises the UI to award level.

| # | Work item | Why it matters for the score | Owner | Day |
|---|---|---|---|---|
| 1 | Ledger-derived payee features: a synthetic UPI ledger streams transactions; features (fan-in, cash-out, dormancy, age) are computed from it with the same formula as the production SQL; lineage shown on every payee card; optional Pub/Sub and BigQuery sinks | Removes the "mock table" objection; demonstrates event-driven data on Google Cloud | backend | Wed 15 |
| 2 | Adversarial evaluation: 20 more labelled calls (10 hard negatives, 10 rubric-gaming scams), confusion matrix published even if imperfect | A 1.0/1.0 score on 30 self-authored calls reads as written to pass | data + backend | Wed 15 |
| 3 | UI/UX overhaul: design system, onboarding with privacy tiers, senior-friendly type, hero hold screen, drill (practice) mode, fraud desk timeline and trace, accessibility | Best UI/UX award; UX is 10% of the rubric and the hold screen is the climax | front end | Wed 15 to Thu 16 |
| 4 | Real-phone recording: unedited two-device call on two physical phones, plus a 10-second Twilio real-number clip | The "validation story" past winners had | demo | Thu 16 |
| 5 | Redeploy, README judge instructions re-verified on a clean machine, tag v1.0 | Submission hygiene | backend | Fri 17 |
| 6 | Video (under 3:00) and deck (12 slides, architecture + business case) | Mandatory submission items | all | Fri 17 |
| 7 | Submit on the official portal; keep Sat 18 as buffer only | Deadline | lead | Fri 17 |

Not in scope: a native Android app, a bank integration, Kannada/Tamil voice QA beyond a smoke test, Twilio two-way audio.

## 2. Architecture, part by part

The system is one Cloud Run service (FastAPI, Python 3.12) serving three web UIs and a WebSocket API, calling Gemini models, with optional Google Cloud data services. Everything below is in the repository; file names are given so you can read the code next to this text.

### 2.1 The call: how audio gets in

- **Victim app** (`web/index.html`, `web/app.js`): the customer's bank app. The browser captures the microphone with an AudioWorklet (`web/worklet.js`), downsamples to 16 kHz 16-bit PCM and streams it over `ws://.../ws/call/{session}/user`.
- **Caller console** (`web/scammer.html`): the other party (a teammate playing the scammer, or a legitimate caller). Same capture, role `caller`. The server relays each party's audio to the other, so the two browsers are a tiny VoIP call.
- **Scripted replay** (`app/replay.py`): the 12 demo scripts in `data/scripts/demo_scripts.json` are played as caller lines, voiced with the caller TTS voice so the victim phone hears a voice, and paused at the line that demands payment.
- **Twilio bridge** (`app/telephony/twilio.py`): a judge can dial a real number; Twilio dials the "scammer" phone and streams both legs (8 kHz mu-law) to `/ws/twilio/{session}`; `app/audio.py` decodes and resamples. One-way: Rakshak's voice does not reach the phone call (documented limitation).
- **Why this design:** no third-party app can tap a cellular call on Android or iOS, so Rakshak lives on the bank/telco side where audio is lawfully available (in-app calls, telco partner, OS vendor). See `docs/DEMO_STRATEGY.md`.

### 2.2 Understanding the call

- **Transcription** (`app/analysis.py`, class `LiveTranscriber`): one Gemini Live session per speaker on `gemini-3.5-transcribe-live`, so the transcript is labelled "caller" and "user" without diarization guesswork. Utterances arrive as `transcript` events.
- **Coercion rubric** (`app/analysis.py`, `analyze_transcript`): after each new utterance (debounced 1.2 s, at most every 3 s) the full transcript is sent to `gemini-3.5-flash` with a JSON schema. Output: language, scam type, stage, eight boolean signals (authority impersonation, threat, secrecy, urgency, remote-app install, safe account, investment pressure, OTP request), a risk score 0 to 1, reasons in English and in the customer's language. Measured latency about 2.4 to 3 s. `gemini-3.8-flash` was 8 s and rejects the fastest thinking level, so it is reserved for the agents.
- **Whisper** (`app/session.py`): at risk 0.85 the server sends a short private TTS warning to the victim device only; the caller never hears it.
- **Offline stub**: with `RAKSHAK_FAKE_LLM=1` a keyword rubric replaces Gemini so tests and a no-network demo still work.

### 2.3 The payment moment

- **Fusion policy** (`app/policy.py`): `score = 0.65 x call_risk + 0.35 x payee_risk`, plus bumps for safe-account/OTP demands, authority + threat, high-risk payee during coercion, high value, and amount far above the customer's usual transfer. Thresholds: warn 0.45, hold 0.70. The action is graded: proceed, warn, hold, hold + alert (if a trusted contact exists). This runs in under 100 ms and decides immediately.
- **Payee risk** (`app/payee_risk.py`, `app/ledger.py`): features for the payee VPA come from the simulated ledger (or BigQuery when `BIGQUERY_PAYEE_TABLE` is set), scored with the formula in `sql/payee_risk.sql`; a lineage record says where the numbers came from and when they were refreshed.
- **Execution** (`app/payment.py`): the hold is written to the case store, the trusted-contact alert is sent (`app/alerts.py`: in-app always; Pub/Sub when `PUBSUB_ALERT_TOPIC` is set; SMS when Twilio is configured), the decision event is broadcast so the screen changes first, and the voice barge-in (`app/intervention.py`, `gemini-3.8-flash-tts`, cached and prewarmed per amount) follows within 100 ms when cached.
- **ADK agents** (`app/agents/pipeline.py`, ADK 2.11): a `SequentialAgent` of `risk_investigator` (tools: `lookup_payee_risk`, `check_regulated_entity`) and `decision_agent` (tool: `place_payment_hold`). The investigator calls both tools in one turn, writes a findings note; the decision agent applies the bank's policy and records its action through the tool. The agent runs concurrently with the fast path and may confirm or upgrade the action, never relax it (policy floor). Its trace is stored on the case and shown on the fraud desk. Typical completion 11 to 17 s on `gemini-3.8-flash`, with automatic fallback to `gemini-3.5-flash`.
- **Authority check** (`app/agents/advisories.py`): a table of official advisories (I4C, RBI, SPF/ScamShield, MAS, SEBI, NPCI) answers instantly with sources; Google Search grounding is used only for organisations not covered.
- **Override and cancel** (`app/payment.py`, `app/main.py`): the customer can cancel and report, or override after typing the exact amount. Holds expire after 30 minutes. Everything is on the case timeline.

### 2.4 After the hold

- **Talk to Rakshak** (`app/guardian_voice.py`): a `gemini-3.8-live` audio session with the case as context and three function tools (keep hold, request release, call trusted contact). The customer asks "why did you stop this?" and hears the answer in their language; a release request routes back to the typed-amount confirmation.
- **Fraud-desk record** (`app/narrative.py`): `gemini-3.8-flash` writes the incident narrative, the 1930 / ASCom referral text, evidence points and recommended bank actions; `sql/narrative_ai_generate.sql` shows the same step as BigQuery `AI.GENERATE`.
- **Fraud desk UI** (`web/desk.html`): cases, status timeline, decision vs policy, rubric, payee evidence with lineage, agent trace, narrative, "SMS alert vs Rakshak" comparison.

### 2.5 State, storage and deployment

- **Store** (`app/store.py`): `MemoryStore` persists cases, profiles and alerts to `data/runtime/*.json`; `FirestoreStore` (set `USE_FIRESTORE=true`) is the multi-instance path on Cloud Run.
- **Models and credentials** (`app/config.py`, `app/llm.py`): text, agents and TTS go through Vertex (`GOOGLE_GENAI_USE_VERTEXAI=true`, location `global`, no daily free-tier cap); the two Live models use the AI Studio key. Health: `/api/health`.
- **Deployment** (`Dockerfile`, `scripts/deploy.sh`, `docs/DEPLOYMENT.md`): Cloud Run in asia-southeast1 with WebSockets, session affinity, 1-hour timeout, Secret Manager for the key, scale to zero. Public URL: https://rakshak-223197895518.asia-southeast1.run.app
- **Evaluation** (`scripts/eval.py`, `docs/EVAL_RESULTS.md`): runs every labelled call through the rubric and the fusion policy and writes precision, recall, signal accuracy and payment-decision accuracy.

## 3. The working demo

Three layers, always with the lower one ready (details in `docs/DEMO_STRATEGY.md`):

1. **Voiced replay (video and judge self-test).** Open the app, tap "Simulate incoming call", auto-play "Parcel from Taiwan"; the transcript, gauge and Hindi reasons appear; at the payment demand tap "Open UPI pay" (fields are pre-filled), tap Pay; the hold screen, voice, payee card and daughter alert appear; show the fraud desk.
2. **Two-device live call (stage).** Phone A is the victim app, laptop B the caller console on the same session; a teammate speaks the script; the judge holds Phone A and pays.
3. **Real number (optional).** The judge dials the Twilio number from their own phone.

Demo rule: the payment screen is the climax. Spend ten seconds on the risk meter and ninety on the hold.

## 4. What to submit, and how

Mandatory items on the official portal (aibuildercup.com dashboard; the FAQ and T&C are the source):

| Item | Requirement | Ours |
|---|---|---|
| Deployed prototype link | working, on Google Cloud (Cloud Run or Firebase) | https://rakshak-223197895518.asia-southeast1.run.app (set `MIN_INSTANCES=1` before submission so judges never hit a cold start) |
| Public GitHub repository | fresh code from the hackathon window, README with judge instructions | https://github.com/devaramanelohith/rakshak-agent (tag `v1.0`) |
| Demo video | strictly under 3 minutes, public YouTube/Vimeo or public Drive link, in English | record per `docs/DEMO_STRATEGY.md` section 5; target 2:55 |
| Deck (PDF) | solution in detail: problem, architecture, business case, feasibility and scalability | `docs/DECK_OUTLINE.md` (12 slides) exported to PDF |
| Theme | one theme per team | BFSI: Intelligent Risk, Fraud & Financial Experiences |

Steps:

1. Thursday: freeze code, redeploy, run `scripts/smoke_ws.py` against the public URL, run `scripts/eval.py`, commit `docs/EVAL_RESULTS.md`.
2. Thursday: record the video; upload unlisted/public; test the link in a private browser window.
3. Friday morning: export the deck to PDF; a non-team member opens every link from a phone.
4. Friday: fill the portal form (links, theme, team), save, and screenshot the confirmation. Do not wait for Saturday; the portal's cut-off time is not published.
5. Keep the Discord/dashboard channel open; failing to respond to organiser messages disqualifies a team.

Eligibility reminders: every member a working professional, 21+, JAPAC resident; no students; only two members travel if shortlisted; visas are self-arranged.

## 5. Day plan

| Day | Build | Demo/doc |
|---|---|---|
| Wed 15 | ledger-derived features + lineage; adversarial eval; UI overhaul in progress | update README and deck outline with the three-tier privacy design and path to production |
| Thu 16 | finish UI, drill mode, redeploy, smoke test on public URL | record two-device call on real phones; record video takes |
| Fri 17 | fix anything the recording exposed; tag v1.0; `MIN_INSTANCES=1` | cut video to 2:55; deck PDF; submit; screenshot confirmation |
| Sat 18 | buffer only | nothing new |

## 6. Known limitations to state openly

Synthetic ledger and calls; no bank partner; Twilio bridge is one-way; Kannada and Tamil voices not tested with native speakers; the agent's own decision lands 11 to 17 s after the fast path (shown as "confirmed" on screen); on-device Tier 1 is a design, not implemented (it needs an OS or OEM partner).
