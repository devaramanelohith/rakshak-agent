# Rakshak submission checklist

**One line:** Team Prod Pilots (team leader: Lohith DS) submits on the aibuildercup.com dashboard under theme BFSI with the deployed link, the public GitHub repository, the public video link (3 to 4 minutes, target 3:30), the official template deck `Rakshak_Pitch_Deck_Prod_Pilots.pptx` and the brief description; screenshot the confirmation; then keep every link alive and unchanged through evaluation (19 October to 6 November) and keep Discord and dashboard notifications on until results.

## 1. Organiser requirements and our artefacts

The original brief, verbatim (its "3 minutes" and "deck/PPT converted into a PDF" are superseded by the final rules below: the video is 3 to 4 minutes, target 3:30, and the deck is the official template file): "Comprehensive Documentation: submit a compelling vision for your AI solution, highlighting its positive impact and alignment with one of the problem statements in a deck/PPT converted into a PDF; clearly articulate the problem your solution addresses and how it will benefit the community; demonstrate the feasibility of your project and its potential for scalability. Functional Prototype: working prototype using Google Cloud AI tools, deployed on Cloud Run/GCP/Firebase; ensure it effectively demonstrates capabilities and benefits. Demo Video: public YouTube/Vimeo/Drive link, 3 minutes, showcasing your AI creation in action. GitHub Repository: public link."

**Final submission rules (published by the organisers; these override the brief where they differ):**

1. **Pitch deck:** must use the prescribed template, the PowerPoint provided by the organisers. Non-template decks may be disqualified. We submit `Rakshak_Pitch_Deck_Prod_Pilots.pptx`. The older 14-slide `Rakshak_Deck.pdf` is supporting material only, not the submission deck.
2. **Video demonstration:** 3 to 4 minutes (target 3:30); it must clearly demonstrate the working functionality. Longer videos may be penalised, and a video that does not show working functionality stops the submission from progressing.
3. **Deployed prototype link:** must stay valid and functional throughout evaluation, with no retries or allowances.
4. **Public GitHub repository:** must stay accessible throughout evaluation.
5. **Brief description:** what was built, including how Firebase, Firestore, Cloud Run and Gemini are leveraged (`submission/BRIEF_DESCRIPTION.md`).

| Organiser item | Our artefact | Link or path | Status |
|---|---|---|---|
| Pitch deck on the organisers' prescribed template (vision, impact, problem statement, community benefit, feasibility, scalability) | The official template deck, filled with Rakshak's content | `Rakshak_Pitch_Deck_Prod_Pilots.pptx` | Being built on the template. Only this file is uploaded as the deck; a non-template deck may be disqualified |
| Supporting material only (not the submission deck) | 14-slide deck: problem (2), gap (3), what it does (4), payment moment (5), architecture (6), Google Cloud AI usage (7), agent (8), data (9), evaluation (10), privacy (11), impact and business case (12), roadmap and limitations (13), judge self-test (14) | `submission/Rakshak_Deck.pdf` (source `submission/deck.html`) | Built. Use for stills and as reference; do not upload it as the deck |
| Functional prototype on Cloud Run, GCP or Firebase | Cloud Run service, asia-southeast1: customer app `/`, caller phone `/call`, trusted contact `/family`, fraud desk `/desk`, health `/api/health` | https://rakshak-223197895518.asia-southeast1.run.app | Live. `/api/health` returned ok, llm, live and vertex all true on 17 Oct |
| Demo video, public link, 3 to 4 minutes (target 3:30), clearly showing the working product | 3:30 video per `submission/VIDEO_RECORDING_GUIDE.md`: title and problem card, PIN-hidden balance, the call with the whisper, hold screen as the climax, Talk to Rakshak (Gemini Live with a tool call), the family phone, post-call carry-over, fraud desk, evaluation and architecture stills, close | [paste the public YouTube link here] | To record and upload. Export between 3:05 and 3:55 |
| GitHub repository, public | README with the 60-second judge self-test, the two-phone flow, the curl flow, architecture, evaluation, deployment, limitations | https://github.com/devaramanelohith/rakshak-agent | Public. Tag `v1.0` before submitting |
| Theme (one per team) | BFSI: Intelligent Risk, Fraud and Financial Experiences | portal field | Select on the portal |
| Team details | Team Prod Pilots, team leader Lohith DS | portal fields | Fill in; mirror in the template deck and the README team line |
| Brief description | What we built and how Firebase, Firestore, Cloud Run and Gemini are leveraged | `submission/BRIEF_DESCRIPTION.md` | Being written; paste into the portal's description field |

Supporting documents in the repository (not required by the organiser, useful for judges who read): `submission/Rakshak_Evaluation_Report.pdf`, `submission/Rakshak_Judge_Pitch_and_QA.pdf`, `docs/ARCHITECTURE.md`, `docs/PRIVACY_TIERS.md`, `docs/SECURITY_PRIVACY.md`, `docs/EVAL_RESULTS.md`, `docs/DEPLOYMENT.md`.

## 2. Rubric coverage check

| Rubric line | Weight | Where a judge sees it |
|---|---|---|
| Technical merit and Gen AI implementation (meaningful use of Gen AI, implementation, scalability) | 40% | Deck slides 6, 7, 8, 12; the fraud-desk trace on `/desk`; `app/agents/pipeline.py`; README "Google Cloud services" table; video 1:56 to 3:10 (Gemini Live conversation with tools, fraud-desk ADK trace) |
| Problem alignment and impact | 25% | Deck slides 2, 3, 12; README "The gap"; video 0:00 to 0:15 and 3:10 to 3:30 |
| Innovation and creativity (non-superficial Gen AI) | 25% | Deck slides 4, 5, 8: call semantics x payee risk at authorisation, voice barge-in in the customer's language, agent with a policy floor, Live voice Q&A with tools, post-call carry-over; video 1:06 to 2:43 |
| UX and solution design | 10% | Deck slides 5, 11; the hold screen; onboarding with privacy tiers; `/family` and `/desk` |

Special awards: Best use of Google Cloud AI tools (slides 6, 7, 8 name five Gemini models, ADK 2.11, Search grounding, Cloud Run, Secret Manager, Vertex AI, and the Firestore, BigQuery, Pub/Sub paths, with implemented versus documented kept explicit); Most Impactful Solution (slides 2, 3, 12); Social Choice (the video's hold moment, a Hindi-speaking grandmother stopped from paying a fake CBI inspector); Best UI/UX (slides 5 and 11, the hold screen, the typed-amount override).

## 3. Portal steps (aibuildercup.com dashboard)

1. Sign in to the dashboard with the team lead's account on Friday 17 October, morning IST. Do not wait for Saturday; the portal's cut-off time on 18 October is not published.
2. Open the submission form for the team. Confirm the team name reads "Prod Pilots", the team leader is Lohith DS, and every member is listed with name, role and contact.
3. Select the theme: **BFSI**. One theme per team; do not select a second.
4. Paste the deployed link: `https://rakshak-223197895518.asia-southeast1.run.app`. Open it from the form's own link if the form renders one.
5. Paste the GitHub link: `https://github.com/devaramanelohith/rakshak-agent`. Confirm the repository is public by opening it in a private browser window.
6. Paste the video link (public YouTube, Vimeo or Drive). Confirm it plays in a private browser window and on a phone.
7. Upload the deck: the official template file `Rakshak_Pitch_Deck_Prod_Pilots.pptx`. Do not upload `Rakshak_Deck.pdf` as the deck; it is not on the template and a non-template deck may be disqualified. Open the uploaded file from the form, if the form allows, to confirm it is the template version.
8. Paste the brief description from `submission/BRIEF_DESCRIPTION.md` (what we built, and how Firebase, Firestore, Cloud Run and Gemini are leveraged); fill any other free-text fields (problem statement, solution summary) from the template deck and the README's first paragraph. Keep the model ids exactly as deployed: gemini-3.5-transcribe-live, gemini-3.5-flash, gemini-3.8-flash, gemini-3.8-flash-tts, gemini-3.8-live, Google ADK 2.11.
9. Save, then submit. Screenshot the confirmation page and any confirmation email; store both in `submission/` and in the team chat.
10. Re-open the dashboard after submitting to confirm the status reads submitted, and check all four links once more from the saved form.
11. Keep Discord and dashboard notifications switched on through results day. Failing to respond to an organiser message can disqualify a team.

### Portal fields at a glance

| Field | Value |
|---|---|
| Team name | Prod Pilots |
| Team leader | Lohith DS |
| Theme | BFSI: Intelligent Risk, Fraud and Financial Experiences |
| Pitch deck | `Rakshak_Pitch_Deck_Prod_Pilots.pptx` (official template) |
| Video link | [paste the public YouTube link here] (3 to 4 minutes, target 3:30) |
| Product link (deployed prototype) | https://rakshak-223197895518.asia-southeast1.run.app |
| GitHub link | https://github.com/devaramanelohith/rakshak-agent (tag v1.0) |
| Brief description | from `submission/BRIEF_DESCRIPTION.md` |

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
| README team line and LICENSE | Team line reads "Team Prod Pilots, team leader Lohith DS"; the licence paragraph points to the `LICENSE` file | Updated | [ ] |
| Template deck | `Rakshak_Pitch_Deck_Prod_Pilots.pptx` is on the organisers' template, carries team Prod Pilots and team leader Lohith DS, and every screenshot is captured from the public URL | Final file ready to upload | [ ] |
| Video length | Read the exported file's duration and the YouTube player's duration | Between 3:00 and 4:00 (export between 3:05 and 3:55, target 3:30) | [ ] |
| Brief description | `submission/BRIEF_DESCRIPTION.md` covers what we built and how Firebase, Firestore, Cloud Run and Gemini are leveraged | Final text ready to paste | [ ] |
| Tag | `git tag -a v1.0 -m "AI Builder Cup 2026 submission" && git push origin v1.0` | Tag visible on GitHub | [ ] |
| Quota | Vertex AI handles text, agents and TTS on the deployed service; the AI Studio key handles the two Live models; confirm billing is on for the AI Studio project so a day of judging does not hit a free-tier daily cap | No 429s in `gcloud run services logs read rakshak --region asia-southeast1 --limit 100` | [ ] |
| Secrets | `.env` is git-ignored; no key in the repository history; Secret Manager mounts `gemini-api-key` | `git log -p --all -S "AIza" -- . ` returns nothing | [ ] |
| Links from a phone | Deployed URL, repo, video, deck opened from a phone outside the team's network | All load | [ ] |

## 6. Keep it alive during evaluation (19 Oct to 6 Nov)

The organisers allow no retries or allowances: if the product link or the repository fails while a judge is looking, the submission is judged as it is. From the moment of submission until results:

| Rule | How |
|---|---|
| Keep the Cloud Run service at min-instances 1 | Never deploy with `--min-instances 0`; verify with `gcloud run services describe rakshak --region asia-southeast1 --format 'value(spec.template.metadata.annotations)'` (expect `autoscaling.knative.dev/minScale: '1'`) |
| Keep the billing account active | Check the billing account is open and the payment method is valid; set a budget alert, not a hard cap that shuts the project down |
| Do not rotate or delete the Gemini API key secret | Leave the Secret Manager secret `gemini-api-key` and its current version untouched; do not revoke the key in AI Studio |
| Do not change the default customers | Leave `demo-user` (Lohith, English) and `demo-user-hi` (Sunita Rao, Hindi) as they are; the judge self-test and the video depend on them |
| Watch `/api/health` daily | `curl -s https://rakshak-223197895518.asia-southeast1.run.app/api/health` must return `ok: true, llm: true, live: true, vertex: true`; if not, fix it the same day |
| Keep the GitHub repository public | Do not rename, archive or make it private; do not delete tag `v1.0` |
| Do not push breaking changes after submission | Tag `v1.0` is the submitted build. Any change, to the repository or the deployed service, must keep `scripts/smoke_ws.py` and `scripts/smoke_live_audio.py` passing against the public URL; run both before and after any redeploy |
| Keep the video public | Do not delete, unlist, re-upload or trim the YouTube video |

## 7. Files in this package

| File | Purpose | Pages |
|---|---|---|
| `Rakshak_Pitch_Deck_Prod_Pilots.pptx` | The deck for the portal (official template) | template |
| `submission/Rakshak_Deck.pdf` | Supporting material only, not the submission deck | 14 |
| `submission/deck.html` | Deck source; edit and re-render with headless Chrome | source |
| `submission/VIDEO_RECORDING_GUIDE.md` and `Rakshak_Video_Recording_Guide.pdf` | The 3:30 video: timeline, both recording methods, word-for-word voiceover, editing, upload | see PDF |
| `submission/DEMO_VIDEO_SCRIPT.md` | Older shot list, superseded by the recording guide | source |
| `submission/BRIEF_DESCRIPTION.md` | The portal's brief description (Firebase, Firestore, Cloud Run, Gemini) | source |
| `submission/EVALUATION_REPORT.md` and `Rakshak_Evaluation_Report.pdf` | Methodology, confusion matrix, breakdowns, latency, system tests, limitations | see PDF |
| `submission/JUDGE_PITCH_AND_QA.md` and `Rakshak_Judge_Pitch_and_QA.pdf` | 3-minute and 90-second pitches, the climax rule, self-test, Q&A | see PDF |
| `submission/SUBMISSION_CHECKLIST.md` and `Rakshak_Submission_Checklist.pdf` | This checklist | see PDF |

Copies of the PDFs are also in `/Users/lohithds/Projects/Portfolio-Website/reports/`.

## 8. Do not

- Do not use any Gemini 2.5 model id anywhere: not in the deck, the video, the portal text or the README. The deployed ids are gemini-3.5-transcribe-live, gemini-3.5-flash, gemini-3.8-flash, gemini-3.8-flash-tts and gemini-3.8-live.
- Do not show mockups. Every screen in the video and the deck's slide 5 must be captured from the running service on the public URL.
- Do not let the video fall outside 3 to 4 minutes. Target 3:30; export between 3:05 and 3:55 and check the file's duration before uploading. A longer video may be penalised; a video that does not show the working product does not progress.
- Do not upload any deck other than the official template file `Rakshak_Pitch_Deck_Prod_Pilots.pptx`.
- Do not record on localhost; the address bar must show the Cloud Run domain.
- Do not claim bank data, real payees or a bank partner. Say "synthetic ledger in this prototype" wherever the payee numbers appear.
- Do not claim Tier 1 on-device, Agent Runtime, Memory Bank or a bidirectional telco stream as built; they are documented paths.
- Do not describe Rakshak as a phone app that taps cellular calls; it is bank-side, through in-app calls, telco forks or OS-vendor feeds.
- Do not quote evaluation numbers from memory; quote `docs/EVAL_RESULTS.md` (n=50) and `submission/Rakshak_Evaluation_Report.pdf`.
- Do not change the deployed service after the smoke tests pass on Friday; if a redeploy is unavoidable, re-run both smoke scripts and the judge self-test.
- Do not submit on Saturday; Friday is the submission day, Saturday is buffer only.
- Do not leave a team placeholder ("Team Rakshak", "add names", "[name]") on any artefact. The team is Prod Pilots, team leader Lohith DS.
- Do not miss an organiser message on Discord or the dashboard.
