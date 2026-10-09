# Build plan: Rakshak for the AI Builder Cup 2026 (10 to 18 October)

Deadline: prototype submission closes **18 Oct 2026** (official page); rosters locked **11 Oct**. Team of 2 to 4;
every member must be a working professional aged 21+ resident in JAPAC (a student on the team disqualifies all).
Confirm both facts on aibuildercup.com before investing another hour.

## What exists on 10 Oct (day 1, evening)

Working end to end on a laptop with a free AI Studio key:

- Call understanding: Gemini Live transcription per speaker (`gemini-3.5-transcribe-live`), coercion rubric in JSON
  (`gemini-3.5-flash`, ~3 s), stage/scam-type, reasons in the customer's language, in-call whisper at 85%.
- Payment moment: deterministic fusion (call x payee x profile) in <100 ms, graded action, voice barge-in
  (`gemini-3.8-flash-tts`, cached), 30-minute hold with countdown, typed-amount override, trusted-contact alert
  (in-app, Pub/Sub and SMS hooks), case + narrative + 1930 referral.
- ADK 2.11 SequentialAgent (investigator with payee-risk and official-advisory tools; decision agent with the
  hold tool) that confirms or upgrades the fast-path decision and leaves a trace on the fraud desk.
- Post-hold voice Q&A on `gemini-3.8-live` with function calling (keep hold / request release / call contact).
- Three UIs: victim bank app, caller console (mic or scripted lines), fraud desk. Twilio bridge for real calls.
- Data: 30 labelled eval calls, 12 demo scripts, 60-row payee mule-risk table; eval script; 10 offline tests.
- Infra: Dockerfile, Cloud Run deploy script, BigQuery loader + SQL, Firestore/Pub/Sub adapters, docs.

Known blocker: the free tier allows only ~20 requests/day on `gemini-3.8-flash`. See "Day 2" item 1.

## Day-by-day

| Day | Date | Goal | Acceptance gate |
|---|---|---|---|
| 2 | Sat 11 Oct | **Unblock quota**: enable billing on the AI Studio project (or `GOOGLE_GENAI_USE_VERTEXAI=true` on the lab project). Lock the roster. Attend the 11 Oct organizer session. Re-run `scripts/eval.py` and `scripts/smoke_agent.py`. | eval completes with 0 errors; agent follow-up lands in <20 s; precision/recall printed in docs/EVAL_RESULTS.md |
| 3 | Sun 12 Oct | **Deploy**: `scripts/deploy.sh` to Cloud Run (asia-southeast1), Secret Manager key, min-instances 1. Enable Firestore + `USE_FIRESTORE=true`; load BigQuery payee table; create Pub/Sub topic. | public URL passes /healthz; L1 voiced replay works on a phone over 4G; case appears in Firestore |
| 4 | Mon 13 Oct | **Two-device live call (L2)** rehearsal on the deployed URL: phone + laptop, real mics. Tune `analysis_debounce_s`, whisper threshold, echo. Fix any transcription merge issues. | three consecutive clean runs of script_01 and script_04; decision rule: if voice is flaky, demo stays on L1 and L2 becomes the backup |
| 5 | Tue 14 Oct | **Polish UX** (Best UI/UX award): hold screen, payee card, desk trace rendering, Kannada/Tamil voice check, accessibility (font size, contrast). Record 10-call eval table into the deck. | judge can run the flow from the README without help |
| 6 | Wed 15 Oct | **Video**: record L1 on a phone + desk on a laptop; cut to 2:55; voice-over in English. | video under 3:00, uploaded unlisted |
| 7 | Thu 16 Oct | **Deck** (docs/DECK_OUTLINE.md): 12 slides, architecture, business case, eval, security. Export PDF. Optional L3 Twilio test. | deck PDF reviewed by a non-team member |
| 8 | Fri 17 Oct | **Freeze**: README judge instructions verified on a clean machine; repo public; tag v1.0; submission form filled with links. | submission saved; a teammate opens every link from a phone |
| 9 | Sat 18 Oct | Buffer. No new features. | - |

## Division of work (2 builders + 1 helper)

- Builder A (backend/agents): quota, eval, agent latency, Cloud Run, Firestore/BigQuery/Pub/Sub, Twilio.
- Builder B (front end/demo): UI polish, mic/echo tuning, scripts rehearsal, video recording and editing.
- Helper: deck, voice-over, scam-script voicing, judge dry-run of the README, visa planning for two travellers.

## Rules that protect the score

1. The video climaxes on the **payment screen** (hold + payee card + override + alert), not on the risk meter.
2. Everything shown must run on the deployed URL; no mock-ups.
3. Say "synthetic data" on the slide that shows the payee table.
4. Never use Gemini 2.5 model ids anywhere (retire on Vertex 16 Oct, inside the evaluation window).
5. Keep the transcript-driven path (`/api/sessions/{id}/turns`) documented so a judge can test without a mic.
