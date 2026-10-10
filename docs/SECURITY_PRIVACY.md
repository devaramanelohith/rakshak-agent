# Security and privacy

Rakshak listens to phone calls and intervenes in payments, so its consent model, data handling and safeguards against over-blocking are part of the design, not an afterthought. This document states what the prototype does today and what the production path is. It is not legal advice; a bank deploying this would run it past its data protection officer and its regulator.

## Scope of the prototype

* All data in the repository is synthetic: 30 evaluation calls, 12 demo scripts, 60 payees, two demo customers and their trusted contacts. Names, phone numbers and VPAs are invented; every payee handle ends in `@rakshakdemo`, a suffix that does not exist on UPI.
* No real bank, telco or customer data was used, and nothing moves money: "proceed", "hold" and "override" change a case status only.
* The deployment is a demo on Cloud Run with unauthenticated endpoints and open CORS so judges can use it; the production client path is described below.

## Consent model: opt-in Guardian mode

* Guardian mode is a per-customer profile flag (`guardian_enabled`) set by the customer on the home screen with the label "Guardian mode (opt-in: Rakshak listens to calls on this device)" and saved through `PUT /api/profiles/{user_id}`.
* The state is always visible: a "Rakshak ON" or "Rakshak OFF" pill in the app's top bar, and a "Rakshak listening" pill on the call screen.
* Listening only starts when the customer acts: tapping "Use my mic" triggers the browser's microphone permission prompt, and auto-playing a script is an explicit demo action. In the Twilio mode the call announces "Rakshak guardian mode is on for this call" to both parties before any audio is streamed.
* In the code, `guardian_enabled` gates the private in-call whisper (`session.run_analysis`). The payment-moment check (`/api/payments`) runs for every payment because it is the bank's own transaction control on its own channel, in the same way a step-up check runs today; in a production SDK the call-listening feature and the payment check would be governed by separate consents.
* The caller is not recorded. Their audio is streamed to the transcription model and relayed to the customer's device for the call itself; no audio file is created at any point. What remains of the caller is text.

## Data minimisation and retention

| Data | Where it goes | Retained? |
|---|---|---|
| Call audio (both parties) | Streamed as 16 kHz PCM to `gemini-3.5-transcribe-live`, relayed between the two devices, discarded | No. `RAKSHAK_RETAIN_AUDIO` exists in `app/config.py` (default false) for a future opt-in recording feature; the current code never writes call audio to disk even when it is set |
| Transcript turns | In-memory `CallSession` for the duration of the call; the last 500 UI events (audio stripped) | Session memory only, lost on restart |
| Transcript excerpt | Up to the last 2,500 characters stored on the case when a payment is evaluated | Yes, per case, for audit and the 1930 referral |
| Call rubric, payee row, policy result, decision, ADK trace, narrative, timeline | Case document | Yes, per case |
| Customer profile (name, age band, language, trusted contact name and phone, typical transfer, thresholds) | Store (`data/runtime/profiles.json` or Firestore `rakshak_profiles`) | Yes |
| Trusted-contact alert (contact name and phone, message) | In-app feed; Pub/Sub message when configured; Twilio SMS when configured | Yes (last 200 in memory); Pub/Sub retention per subscription |
| Rakshak's own synthesised speech | `data/tts_cache/*.wav` keyed by a hash of model, voice and text | Cache only; contains no customer or caller audio |
| Rubric prompt | Transcript plus age band and language to `gemini-3.5-flash` | Not stored by the app; subject to the Gemini API data terms of the chosen endpoint |
| Search grounding query | The caller's claimed organisation, role and request (text only) to Google Search grounding, only when the local advisory table has no match | Not stored by the app |
| Post-hold conversation | Audio both ways with `gemini-3.8-live`; the case summary is in the system prompt | Transcribed text is shown on screen; not stored on the case |

Retention controls that exist today: `data/runtime/` and `data/tts_cache/` are git-ignored and live in the container; Firestore documents persist until deleted. A production deployment would add a retention schedule per case status (for example, cancelled and expired cases purged after the complaint window, overridden cases kept for the chargeback window) and a customer-facing deletion path.

## DPDP Act and MAS considerations, in plain words

**India, Digital Personal Data Protection Act 2023.** The bank is the data fiduciary. The customer's consent for Guardian mode must be free, specific, informed and unambiguous, given after a plain-language notice of what is processed and why, and withdrawable as easily as it was given: the opt-in checkbox and the visible pill are the prototype's version of that; a production notice would list the purposes (scam detection on calls, payment protection, case filing with law enforcement), the data (call transcript, payment details, trusted-contact details) and the retention period. Purpose limitation means the transcript is used for scam detection and the referral only, never for marketing or credit decisions. Data minimisation is why audio is not retained and only an excerpt of the transcript is kept. The caller's words are also personal data of a third party who has not consented; keeping only the text needed to document a suspected offence, and sharing it only through the 1930 helpline referral, is the narrow use a bank's legal team would need to confirm. The trusted contact's phone number is personal data too, collected from the customer, and the alert should be the minimum needed ("please call them now"). Breach notification and security safeguards obligations apply to the case store.

**Singapore, MAS and PDPA.** The Shared Responsibility Framework for phishing scams sets out duties for financial institutions and telcos and allocates losses when a duty is breached; real-time fraud surveillance and timely customer notification are the kind of control Rakshak implements, which is why the bank-side placement matters. MAS's Technology Risk Management guidelines would govern the deployment itself (secrets, logging, access control, vendor and model risk). The PDPA's consent, purpose limitation and retention obligations apply in the same way as the DPDP Act above. Singapore's ScamShield and SPF advisories are already encoded in the authority-check table so the agent cites official guidance rather than inventing it.

## Secrets handling

* The Gemini key is read from `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in the environment. Locally it lives in `.env`, which is git-ignored and must never be committed; `.env.example` has placeholders only.
* On Cloud Run the key is stored in Secret Manager (`gemini-api-key`) and mounted as an environment variable by `scripts/deploy.sh` with `--set-secrets`; the runtime service account needs only `roles/secretmanager.secretAccessor` on that secret.
* The Vertex AI alternative (`GOOGLE_GENAI_USE_VERTEXAI=true`) uses the service account's identity for text, TTS, agent and narrative calls and removes the key from the process environment for those clients; the two Live API models still use the AI Studio key through a separate client unless `RAKSHAK_LIVE_VIA_VERTEX=1`. `RAKSHAK_ACCESS_TOKEN` (a short-lived `gcloud` access token) exists for local development without Application Default Credentials and must never be set on a deployed service.
* Twilio credentials, when used, go in Secret Manager the same way (see `docs/DEPLOYMENT.md`); the auth token is used server-side only for the SMS REST call.
* Logs truncate error messages and never print keys; prompts are not logged.

## Production client path: Firebase App Check and Firebase Auth

Not implemented in this repository. The prototype exposes every REST and WebSocket endpoint without authentication and with `allow_origins=["*"]`, which is acceptable for a judged demo on synthetic data and nothing else. The production shape:

* **Firebase Auth** identifies the customer; the bank's existing identity provider is federated through it. `user_id` is then taken from the verified ID token on every request and socket, never from the request body or query string as it is today, and `PUT /api/profiles/{user_id}`, `/api/cases/*/override` and `/ws/call/{session}/user` are bound to that identity.
* **Firebase App Check** attests that requests come from the bank's genuine app build (Play Integrity, App Attest), so a scammer who learns a session id cannot join as the caller or replay a script into a victim's session.
* **Cloud Run** is deployed with `--no-allow-unauthenticated` behind the bank's API gateway or a load balancer with IAP; the fraud desk (`/desk`, `/api/cases`, `/ws/events/all`) is restricted to fraud-team identities; CORS is limited to the app's origins.
* **Session ids** become unguessable server-issued tokens tied to the authenticated customer, and the caller console is removed from the customer build (it exists only to play the scammer in the demo).

## Abuse and false-positive safeguards

A guardian that blocks legitimate payments would be switched off by customers in a week. The design keeps the customer in control:

* **A hold is a pause, not a block.** The hold screen always offers "I know this person, pay anyway". For a hold the override requires typing the exact amount into a confirmation dialog that restates the payee and the fact that the trusted contact has been told; for a warn, "Continue payment" is one tap. The override reason is recorded on the case (`overridden_by_user`) and the fraud desk still reviews the payee.
* **Holds expire.** A background loop marks `on_hold` cases as `hold_expired` after `RAKSHAK_HOLD_MINUTES` (30). Nothing stays frozen indefinitely.
* **The agent can only ever be stricter than the policy.** The deterministic policy's action is a floor; the ADK agent may upgrade it with evidence but a lenient agent cannot release a hold. A failed or slow agent leaves the policy decision in force. This bounds the blast radius of a model error to "slightly more cautious".
* **Benign urgency is not a scam.** The rubric prompt and the decision agent's instructions both say that a relative needing fees or a landlord is not a hold; the evaluation set contains 15 benign calls, including hard negatives, to measure false positives, and the policy's thresholds are per profile.
* **Unknown payees are treated as thin-file, not criminal.** A payee missing from the risk table gets a medium 0.3 score, so an ordinary new payee during a calm call still proceeds.
* **Trusted-contact alerts are a feature the customer configures.** The contact name and phone come from the customer's own profile; with no contact set, `hold_and_alert` degrades to a plain hold.
* **Everything is auditable.** Every case carries the policy result, the agent decision, the trace, the timeline and the narrative, so a wrong hold can be explained to the customer and to the regulator.

Known gaps in the prototype that the production path above closes: anyone who knows a session id can join it or inject lines; profiles are editable without authentication; the case store on a non-Firestore deployment is a JSON file on the container disk.

## Synthetic-data statement

The evaluation calls (`data/eval/calls.json`), the demo scripts (`data/scripts/demo_scripts.json`) and the payee table (`data/payees.json`) were written for this project to resemble digital-arrest, investment, job-task, KYC/OTP, lottery, family-emergency and Singapore official-impersonation scams as described in public advisories, and benign calls that share their surface features. The payee features (fan-in, cash-out ratio, dormancy burst, telecom FRI, 1930 complaint counts, KYC tier) follow the shape of AMLSim and PaySim-style mule indicators; the values are made up. The SQL in `sql/payee_risk.sql` shows how a bank would derive the same features from its own ledger. No model was trained on any data in this repository.
