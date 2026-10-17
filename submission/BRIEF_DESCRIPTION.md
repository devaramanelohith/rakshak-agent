# Brief description for the submission portal

Team: **Prod Pilots** · Team leader: **Lohith DS** · Theme: **BFSI: Intelligent Risk, Fraud and Financial Experiences**

Paste the short version if the portal limits length; otherwise paste the full version.

## Short version (about 120 words)

Rakshak is a scam-moment guardian for bank and UPI apps. With the customer's opt-in it listens to a call from an unknown number and scores the caller's coercion live with Gemini. When the customer taps Pay, it fuses that call risk with the payee's mule-account risk from the bank's ledger and, in under 100 ms, pauses the payment, explains why in the customer's language, alerts a trusted contact and files an auditable case. A Google ADK agent confirms with evidence; the customer keeps a typed-amount override. It runs on Cloud Run, stores cases, profiles and alerts in Firestore, serves the app through Firebase Hosting, and uses Gemini 3.5 and 3.8 models for live transcription, scoring, agents, voice and conversation.

## Full version (about 260 words)

**What we built.** Rakshak stops authorised-push-payment scams at the moment of payment. Victims of digital-arrest and investment scams send the money themselves, on a call, so bank fraud engines see a genuine customer and an SMS alert arrives after the money has gone. Rakshak, built into a bank or UPI app, listens (opt-in) from the first ring, scores eight coercion signals live, whispers privately at 85% risk, and when the customer taps Pay it fuses the call risk with the payee's mule-account risk to decide in under 100 ms: proceed, warn, a 30-minute hold, or hold plus a trusted-contact alert. Rakshak speaks the reason in the customer's language; an ADK agent confirms with evidence; the bank's fraud desk gets the case, the agent trace and a drafted 1930 cybercrime referral. It works in six languages and supports a live two-way call between two phones. On our 50-call labelled evaluation, precision and recall were 1.0.

**Gemini.** Gemini 3.5 Transcribe Live transcribes each speaker in real time; Gemini 3.5 Flash scores the coercion rubric as structured JSON, runs the two ADK 2.11 agents (payee investigator with official-advisory and Search-grounding tools, and the decision agent with a hold tool) and drafts the case narrative; Gemini 3.8 Flash TTS voices the whisper and the hold; Gemini 3.8 Live powers a post-hold voice conversation with function calling.

**Cloud Run.** The whole product (FastAPI, WebSocket call relay, customer app, caller phone, family phone and fraud desk) runs as one always-on Cloud Run service in asia-southeast1, with Secret Manager for the key.

**Firestore.** Cases, customer profiles and trusted-contact alerts are persisted in Firestore, so every intervention survives restarts and is auditable.

**Firebase.** Firebase Hosting serves the same installable app at https://fde-cloud-run-lab-123456.web.app and forwards every page and API request to the Cloud Run service; live call audio connects straight to Cloud Run over WebSockets. Firestore, the Firebase database, is the case store described above.

Live: https://rakshak-223197895518.asia-southeast1.run.app (also https://fde-cloud-run-lab-123456.web.app) · Code: https://github.com/devaramanelohith/rakshak-agent
