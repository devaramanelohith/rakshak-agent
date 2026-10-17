# Rakshak submission checklist

**One line:** Submit on Friday 17 October on the aibuildercup.com dashboard with the deployed link, the public GitHub repository, the public video link and the deck PDF under theme BFSI; screenshot the confirmation; keep Discord and dashboard notifications on until results.

## 1. Organiser requirements and our artefacts

The brief, verbatim: "Comprehensive Documentation: submit a compelling vision for your AI solution, highlighting its positive impact and alignment with one of the problem statements in a deck/PPT converted into a PDF; clearly articulate the problem your solution addresses and how it will benefit the community; demonstrate the feasibility of your project and its potential for scalability. Functional Prototype: working prototype using Google Cloud AI tools, deployed on Cloud Run/GCP/Firebase; ensure it effectively demonstrates capabilities and benefits. Demo Video: public YouTube/Vimeo/Drive link, 3 minutes, showcasing your AI creation in action. GitHub Repository: public link."

| Organiser item | Our artefact | Link or path | Status |
|---|---|---|---|
| Documentation: deck as PDF (vision, impact, problem statement, community benefit, feasibility, scalability) | 14-slide deck: problem (2), gap (3), what it does (4), payment moment (5), architecture (6), Google Cloud AI usage (7), agent (8), data (9), evaluation (10), privacy (11), impact and business case (12), roadmap and limitations (13), judge self-test (14) | `submission/Rakshak_Deck.pdf` (source `submission/deck.html`) | Built. Add team names on slides 1 and 14; add the hold-screen screenshot on slide 5 |
| Functional prototype on Cloud Run, GCP or Firebase | Cloud Run service, asia-southeast1: customer app `/`, caller phone `/call`, trusted contact `/family`, fraud desk `/desk`, health `/api/health` | https://rakshak-223197895518.asia-southeast1.run.app | Live. `/api/health` returned ok, llm, live and vertex all true on 17 Oct |
| Demo video, public link, 3 minutes | 2:50 video per `submission/DEMO_VIDEO_SCRIPT.md`: title and problem card, live two-phone call, hold screen as the climax, fraud desk, architecture and evaluation cards, close | [paste the public YouTube link here] | To record and upload |
| GitHub repository, public | README with the 60-second judge self-test, the two-phone flow, the curl flow, architecture, evaluation, deployment, limitations | https://github.com/devaramanelohith/rakshak-agent | Public. Tag `v1.0` before submitting |
| Theme (one per team) | BFSI: Intelligent Risk, Fraud and Financial Experiences | portal field | Select on the portal |
| Team details | Team Rakshak: names, roles, contact | portal fields | Fill in; mirror on deck slides 1 and 14 and the README team line |

Supporting documents in the repository (not required by the organiser, useful for judges who read): `submission/Rakshak_Evaluation_Report.pdf`, `submission/Rakshak_Judge_Pitch_and_QA.pdf`, `docs/ARCHITECTURE.md`, `docs/PRIVACY_TIERS.md`, `docs/SECURITY_PRIVACY.md`, `docs/EVAL_RESULTS.md`, `docs/DEPLOYMENT.md`.

## 2. Rubric coverage check

| Rubric line | Weight | Where a judge sees it |
|---|---|---|
| Technical merit and Gen AI implementation (meaningful use of Gen AI, implementation, scalability) | 40% | Deck slides 6, 7, 8, 12; the fraud-desk trace on `/desk`; `app/agents/pipeline.py`; README "Google Cloud services" table; video 1:40 to 2:42 |
| Problem alignment and impact | 25% | Deck slides 2, 3, 12; README "The gap"; video 0:05 to 0:15 and 2:10 to 2:30 |
| Innovation and creativity (non-superficial Gen AI) | 25% | Deck slides 4, 5, 8: call semantics x payee risk at authorisation, voice barge-in in the customer's language, agent with a policy floor, Live voice Q&A with tools; video 1:08 to 2:10 |
| UX and solution design | 10% | Deck slides 5, 11; the hold screen; onboarding with privacy tiers; `/family` and `/desk` |

Special awards: Best use of Google Cloud AI tools (slides 6, 7, 8 name five Gemini models, ADK 2.11, Search grounding, Cloud Run, Secret Manager, Vertex AI, and the Firestore, BigQuery, Pub/Sub paths, with implemented versus documented kept explicit); Most Impactful Solution (slides 2, 3, 12); Social Choice (the video's hold moment, a Hindi-speaking grandmother stopped from paying a fake CBI inspector); Best UI/UX (slides 5 and 11, the hold screen, the typed-amount override).

## 3. Portal steps (aibuildercup.com dashboard)

1. Sign in to the dashboard with the team lead's account on Friday 17 October, morning IST. Do not wait for Saturday; the portal's cut-off time on 18 October is not published.
2. Open the submission form for the team. Confirm the team name reads "Team Rakshak" and every member is listed with name, role and contact.
3. Select the theme: **BFSI**. One theme per team; do not select a second.
4. Paste the deployed link: `https://rakshak-223197895518.asia-southeast1.run.app`. Open it from the form's own link if the form renders one.
5. Paste the GitHub link: `https://github.com/devaramanelohith/rakshak-agent`. Confirm the repository is public by opening it in a private browser window.
6. Paste the video link (public YouTube, Vimeo or Drive). Confirm it plays in a private browser window and on a phone.
7. Upload the deck PDF: `submission/Rakshak_Deck.pdf` (14 pages, 16:9). If the portal has a size limit, the file is well under it; if it asks for PPT, it accepts PDF per the brief ("deck/PPT converted into a PDF").
8. Fill any free-text fields (problem statement, solution summary) from deck slides 2 and 4 and the README's first paragraph. Keep the model ids exactly as deployed: gemini-3.5-transcribe-live, gemini-3.5-flash, gemini-3.8-flash, gemini-3.8-flash-tts, gemini-3.8-live, Google ADK 2.11.
9. Save, then submit. Screenshot the confirmation page and any confirmation email; store both in `submission/` and in the team chat.
10. Re-open the dashboard after submitting to confirm the status reads submitted, and check all four links once more from the saved form.
11. Keep Discord and dashboard notifications switched on through results day. Failing to respond to an organiser message can disqualify a team.

## 4. Eligibility reminders

- Every member is a working professional, aged 21 or over, resident in the JAPAC region.
- No students on the team.
- Team size two to four members.
- If shortlisted, only two members travel to the finals; visas are self-arranged.
- One submission per team, one theme per team.

Confirm each point for each member before the form is submitted; the portal's team details must match.

## 5. Pre-submission technical checks (Thursday 16 and Friday 17 October)

| Check | Command or action | Expected | Done |
|---|---|---|---|
| Always-on instance | `scripts/deploy.sh` defaults to `--min-instances 1` (deploy7.log confirms revision rakshak-00009-mhj); verify with `gcloud run services describe rakshak --region asia-southeast1 --format 'value(spec.template.metadata.annotations)'` | `autoscaling.knative.dev/minScale: '1'` present; no cold start for judges | [ ] |
| Health | `curl -s https://rakshak-223197895518.asia-southeast1.run.app/api/health` | `ok: true, llm: true, live: true, vertex: true` and the five model ids | [ ] (passed 17 Oct) |
| Pages | Open `/`, `/call`, `/family`, `/desk` | All return 200 and render | [ ] (all 200 on 17 Oct) |
| API and Live voice path | `uv run python scripts/smoke_ws.py https://rakshak-223197895518.asia-southeast1.run.app` | Hold event within about a second of Pay; voice message present; agent update `adk_agent` within 60 s; Live conversation answered | [ ] |
| Live audio path | `uv run python scripts/smoke_live_audio.py https://rakshak-223197895518.asia-southeast1.run.app` | `LIVE AUDIO PATH: PASS`, 3 transcript turns, risk above 0.7, whisper fired | [ ] |
| Judge steps on a clean browser | A non-team member follows the README "60-second self-test" in a private browser window on a phone | Hold screen within a second, Hindi voice audible, case visible on `/desk` | [ ] |
| Two-phone flow | Phone B `/call?session=x`, phone A `/?session=x&user=demo-user`; Call, Answer, talk, Pay; phone C on `/family` | Both hear each other; transcript labelled; hold and family chime | [ ] |
| Offline tests | `uv run pytest` | 10 passed | [ ] |
| Evaluation artefacts committed | `docs/EVAL_RESULTS.md` matches `data/runtime/eval_results.json` (n=50, precision 1.0, recall 1.0, payment accuracy 1.0, signal accuracy 0.932) | Committed | [ ] |
| README team line and LICENSE | Replace "add names, roles and contact here"; the README's licence paragraph says the `LICENSE` file is missing but the repository root contains it, so fix the sentence | Updated | [ ] |
| Deck placeholders | Slide 1 and 14 team names; slide 5 screenshot of the hold screen captured from the public URL | Updated and re-rendered to PDF (14 pages) | [ ] |
| Tag | `git tag -a v1.0 -m "AI Builder Cup 2026 submission" && git push origin v1.0` | Tag visible on GitHub | [ ] |
| Quota | Vertex AI handles text, agents and TTS on the deployed service; the AI Studio key handles the two Live models; confirm billing is on for the AI Studio project so a day of judging does not hit a free-tier daily cap | No 429s in `gcloud run services logs read rakshak --region asia-southeast1 --limit 100` | [ ] |
| Secrets | `.env` is git-ignored; no key in the repository history; Secret Manager mounts `gemini-api-key` | `git log -p --all -S "AIza" -- . ` returns nothing | [ ] |
| Links from a phone | Deployed URL, repo, video, deck opened from a phone outside the team's network | All load | [ ] |

## 6. Files in this package

| File | Purpose | Pages |
|---|---|---|
| `submission/Rakshak_Deck.pdf` | The deck for the portal | 14 |
| `submission/deck.html` | Deck source; edit and re-render with headless Chrome | source |
| `submission/DEMO_VIDEO_SCRIPT.md` | Shot list, voice-over, recording setup, takes, editing notes | source |
| `submission/EVALUATION_REPORT.md` and `Rakshak_Evaluation_Report.pdf` | Methodology, confusion matrix, breakdowns, latency, system tests, limitations | see PDF |
| `submission/JUDGE_PITCH_AND_QA.md` and `Rakshak_Judge_Pitch_and_QA.pdf` | 3-minute and 90-second pitches, the climax rule, self-test, Q&A | see PDF |
| `submission/SUBMISSION_CHECKLIST.md` and `Rakshak_Submission_Checklist.pdf` | This checklist | see PDF |

Copies of the four PDFs are also in `/Users/lohithds/Projects/Portfolio-Website/reports/`.

## 7. Do not

- Do not use any Gemini 2.5 model id anywhere: not in the deck, the video, the portal text or the README. The deployed ids are gemini-3.5-transcribe-live, gemini-3.5-flash, gemini-3.8-flash, gemini-3.8-flash-tts and gemini-3.8-live.
- Do not show mockups. Every screen in the video and the deck's slide 5 must be captured from the running service on the public URL.
- Do not let the video run to 3:00 or beyond. Export at 2:50 and check the file's duration before uploading.
- Do not record on localhost; the address bar must show the Cloud Run domain.
- Do not claim bank data, real payees or a bank partner. Say "synthetic ledger in this prototype" wherever the payee numbers appear.
- Do not claim Tier 1 on-device, Agent Runtime, Memory Bank or a bidirectional telco stream as built; they are documented paths.
- Do not describe Rakshak as a phone app that taps cellular calls; it is bank-side, through in-app calls, telco forks or OS-vendor feeds.
- Do not quote evaluation numbers from memory; quote `docs/EVAL_RESULTS.md` (n=50) and `submission/Rakshak_Evaluation_Report.pdf`.
- Do not change the deployed service after the smoke tests pass on Friday; if a redeploy is unavoidable, re-run both smoke scripts and the judge self-test.
- Do not submit on Saturday; Friday is the submission day, Saturday is buffer only.
- Do not leave the team placeholder ("Team Rakshak", "add names") on any artefact.
- Do not miss an organiser message on Discord or the dashboard.
