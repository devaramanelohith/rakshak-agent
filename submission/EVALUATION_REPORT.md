# Rakshak evaluation report

**Bottom line:** On 50 labelled synthetic calls (25 scam, 25 benign; Hindi, Hinglish, English, Singapore English, Kannada, Tamil; 10 hard negatives and 10 adversarial scams written to evade keyword detection), the gemini-3.5-flash coercion rubric separates every scam from every benign call at the 0.70 hold threshold (precision 1.0, recall 1.0, F1 1.0). The deterministic fusion policy makes the labelled payment decision on 38 of 39 payment attempts (0.974); the one miss is a by-design warn on an ambiguous job-scam call. Per-signal accuracy over the eight coercion signals is 0.932. The mean rubric latency was 2.4 s uncontended and 5.3 s in the contended evaluation run. Three system tests exercise the live audio path end to end on the deployed service. The dataset is self-authored and small; the next step with a bank partner is a human-labelled corpus of real calls.

## 1. What is measured and how

### 1.1 The two decisions under test

Rakshak makes two decisions, and the harness (`scripts/eval.py`) scores both:

1. **Call-level detection.** The transcript up to the payment attempt (or the whole call when there is none) is sent to the coercion rubric on `gemini-3.5-flash` with a strict JSON schema. The rubric returns a language, a scam type (10 classes), a stage, eight boolean coercion signals, a risk score from 0 to 1 and reasons in English and in the customer's language. A call is counted as "detected" when its risk score is at or above the hold threshold of 0.70, which is the same threshold the product uses.
2. **Payment-level decision.** For every call that contains a payment attempt, the fusion policy (`app/policy.py`) combines the rubric's risk score and signals with the payee's mule-risk row and the customer profile and returns one of proceed, warn, hold or hold_and_alert. The decision is correct when a scam call gets hold or hold_and_alert and a benign call gets proceed or warn. This is the deterministic fast path that executes in under 100 ms at the payment moment; the ADK agent, which runs in parallel and can only make the action stricter, is not part of the evaluation loop.

A third measurement, per-signal accuracy, compares each of the eight predicted signals against the labelled expectation for every call (8 x 50 = 400 comparisons).

### 1.2 Dataset design

The dataset is `data/eval/calls.json`: 50 synthetic calls written for this project, each with an id, label, scam type, language, a victim profile (age band, preferred language, trusted contact), the turn-by-turn transcript with speaker labels (Hindi and other scripts carry romanised and English renderings for review), the eight expected signals, an expected risk band, an optional payment attempt (payee VPA, amount, the turn index at which it happens) and a note explaining what the call is meant to test.

| Block | Ids | Count | Purpose |
|---|---|---|---|
| Base scams | call_001 to call_015 | 15 scam | Digital arrest, investment, job task, KYC/OTP, lottery, family emergency, Singapore official impersonation; the patterns described in I4C, RBI, SPF and MAS advisories |
| Base benign | call_016 to call_030 | 15 benign | Everyday calls that mention money, deadlines or officials without coercion |
| Hard negatives | call_031 to call_040 | 10 benign | Benign calls that share the surface vocabulary of scams: a genuine bank fraud desk saying "blocked" and "OTP", a real police station about a found wallet, a hospital deposit for same-day surgery, a Kannada son abroad needing a visa fee by tomorrow, an insurance premium "due today", school fees with a late fee, a harsh Tamil landlord threatening a notice to vacate, a courier asking for a small COD amount, a SEBI-registered adviser discussing 30 percent returns, a friend asking to be repaid |
| Adversarial scams | call_041 to call_050 | 10 scam | Scams rewritten to defeat keyword rules: a digital arrest that never says police, arrest, OTP or safe account ("department", "case file", "monitoring account"); a family emergency with no authority and a soft "he's okay" framing; a slow-burn investment pitch that disowns the word "guarantee"; a refund scam that asks for a "confirmation amount"; a job scam framed as a refundable training kit; a KYC scam that calls the OTP a "matching code with nothing to do with money"; a Kannada loan-app scam citing "RBI rules" without claiming to be RBI; a Tamil prize scam that says "this isn't a lottery"; a Singapore parcel scam with "holding account for safekeeping"; a UPI customer-care scam that promises never to ask for a PIN and routes the balance through a "temporary migration wallet" |

Languages: Hindi (15 calls), Hinglish (15), English (12), Singapore English (4), Kannada (2), Tamil (2). Thirty-nine of the fifty calls include a payment attempt; the eleven without one are benign calls with no transfer, which still count for detection and signal accuracy.

Payee rows for the payment attempts come from the same 64-payee synthetic table the product uses (`data/payees.json`, bands low, medium, high and critical). Several adversarial scams deliberately pay a new high-risk or critical row so that the payee side of the fusion is tested in cases where the transcript alone is ambiguous. The victim profile used by the harness sets a typical transfer of 5,000 rupees so the "amount more than 5x usual" bump is exercised.

### 1.3 Run conditions

The reported run is `data/runtime/eval_results.json` written on 15 October 2026 (run_at 1792010287) with model `gemini-3.5-flash`, hold threshold 0.70, concurrency 4. The same results are rendered in `docs/EVAL_RESULTS.md`. An offline keyword stub (`--stub`) exists for CI and is not reported here.

## 2. Results

### 2.1 Call-level detection

Confusion matrix at the hold threshold 0.70 (rows are labels, columns are predictions):

| | Predicted scam (risk >= 0.70) | Predicted benign (risk < 0.70) |
|---|---|---|
| Scam (25) | 25 | 0 |
| Benign (25) | 0 | 25 |

| Metric | Value |
|---|---|
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| Lowest risk score on a scam call | 0.75 (call_045, the ambiguous job-scam call) |
| Highest risk score on a benign call | 0.10 (call_020, call_022, call_033, call_034) |
| Scam-type classification on scam calls | 25 of 25 match the label |

The margin matters more than the headline: the lowest scam score (0.75) sits just above the threshold, while the highest benign score (0.10) is far below the warn threshold of 0.45. The hard negatives, which were written to look like scams on vocabulary alone, all scored 0.10 or lower, including the genuine fraud-desk call that says "blocked", "OTP" and "safer" (call_031, 0.05) and the Tamil landlord threatening a notice to vacate (call_037, 0.05).

### 2.2 Payment-level decision (fusion policy)

| Metric | Value |
|---|---|
| Payment attempts | 39 (25 scam, 14 benign) |
| Correct decisions | 38 |
| Payment-decision accuracy | 0.974 |
| Benign payments that got warn instead of proceed | 0 |
| Scam payments that got a hold | 24 of 25, all hold_and_alert (every evaluation profile has a trusted contact) |

The single miss is call_009, a Hinglish job-task scam (risk 0.85, predicted type job_task) paying 2,000 rupees to `tasks.hr.payout@rakshakdemo`, which the ledger-derived lookup placed in the low band at run time. The fused score was 0.67, above the warn threshold (0.45) and below the hold threshold (0.70), so the policy returned warn. This is the intended behaviour of the fusion: a small amount to a payee with a clean ledger during a call with moderate coercion gets a caution rather than a 30-minute hold, because the same combination also describes a legitimate small payment. The policy check in section 4 shows why the threshold should not be lowered to catch it.

### 2.3 Per-signal accuracy

Over 400 signal comparisons (8 signals x 50 calls), 373 are correct (0.932).

| Signal | Correct of 50 | False positives | False negatives | Accuracy |
|---|---|---|---|---|
| secrecy | 50 | 0 | 0 | 1.00 |
| otp_or_credential_request | 49 | 0 | 1 | 0.98 |
| investment_pressure | 48 | 0 | 2 | 0.96 |
| threat_of_arrest_or_harm | 48 | 1 | 1 | 0.96 |
| authority_impersonation | 47 | 3 | 0 | 0.94 |
| remote_app_install | 46 | 3 | 1 | 0.92 |
| urgency | 43 | 0 | 7 | 0.86 |
| safe_account | 42 | 8 | 0 | 0.84 |

Two signals account for most of the disagreement. `safe_account` is over-predicted (8 false positives): the model marks the flag on scams whose payment destination is a "monitoring account", "holding account" or "migration wallet" even where the label reserved the flag for an explicit "safe account" demand. This over-prediction only ever occurs on scam calls, so it adds a +0.10 bump that pushes the fused score the right way; it does not affect any benign call. `urgency` is under-predicted (7 false negatives): the model declines to flag urgency on calls where the deadline is implied rather than stated. Both are labelling-convention disagreements rather than detection failures, and neither changed a call-level or payment-level outcome.

### 2.4 Per-language breakdown

Computed from `data/runtime/eval_results.json`.

| Language | Calls | Scam / benign | Detection correct | Payment decisions correct | Signal accuracy | Mean rubric latency |
|---|---|---|---|---|---|---|
| Hindi (hi) | 15 | 8 / 7 | 15 / 15 | 11 / 11 | 0.908 | 6.3 s |
| Hinglish | 15 | 8 / 7 | 15 / 15 | 12 / 13 | 0.917 | 4.3 s |
| English (en) | 12 | 5 / 7 | 12 / 12 | 8 / 8 | 0.958 | 5.7 s |
| Singapore English (en-sg) | 4 | 2 / 2 | 4 / 4 | 3 / 3 | 1.000 | 5.1 s |
| Kannada (kn) | 2 | 1 / 1 | 2 / 2 | 2 / 2 | 1.000 | 6.9 s |
| Tamil (ta) | 2 | 1 / 1 | 2 / 2 | 2 / 2 | 0.875 | 2.0 s |

Detection is perfect in every language. Signal accuracy is lowest in Hindi and Hinglish, where the `safe_account` and `urgency` conventions above are concentrated. Kannada and Tamil are covered by two calls each (one scam, one benign); this is a smoke test of the rubric's reading of those scripts, not a measurement of its accuracy in them.

### 2.5 Per-scam-type breakdown

| Scam type | Calls | Detection correct | Payment decisions correct | Signal accuracy | Mean rubric latency |
|---|---|---|---|---|---|
| digital_arrest | 6 | 6 / 6 | 6 / 6 | 0.958 | 4.9 s |
| investment | 4 | 4 / 4 | 4 / 4 | 0.844 | 13.0 s |
| kyc_otp | 4 | 4 / 4 | 4 / 4 | 0.906 | 11.0 s |
| job_task | 3 | 3 / 3 | 2 / 3 | 0.792 | 2.1 s |
| family_emergency | 2 | 2 / 2 | 2 / 2 | 0.812 | 2.5 s |
| lottery | 2 | 2 / 2 | 2 / 2 | 0.875 | 2.3 s |
| sg_official_impersonation | 2 | 2 / 2 | 2 / 2 | 1.000 | 3.2 s |
| loan_app | 1 | 1 / 1 | 1 / 1 | 1.000 | 3.2 s |
| other (refund scam) | 1 | 1 / 1 | 1 / 1 | 1.000 | 1.7 s |
| benign (all) | 25 | 25 / 25 | 14 / 14 | 0.965 | 4.5 s |

The adversarial block (call_041 to call_050) scored between 0.75 and 0.98, all above the threshold, with the predicted scam type matching the label in every case, including the refund scam labelled `other`. Investment and KYC calls are the longest transcripts in the set, which is why their mean latency is higher.

## 3. Latency

| Measurement | Value | Condition |
|---|---|---|
| Rubric, single request | 2.4 to 3 s | Uncontended, `thinking_level=minimal`, measured during development and in the smoke tests |
| Rubric, evaluation run | 5.3 s mean (median 2.3 s, minimum 1.4 s, maximum 28.5 s) | 50 calls at concurrency 4 against the API; the tail is rate-limit backoff, not model time |
| Fusion policy | under 100 ms | Pure arithmetic in the request; the case is stored with `latency_ms: 0` |
| Hold event on the phone after Pay | 20 ms to 1.2 s | Measured on the public URL by `scripts/smoke_ws.py` (decision event timestamp minus the Pay request) |
| Voice barge-in after the hold event | about 100 ms | When the clip was prewarmed (startup, pay-screen open, or replay start); otherwise after TTS synthesis of about 6 s, during which the hold screen is already up |
| ADK agent decision | 11 to 17 s | `gemini-3.8-flash` at `thinking_level=low`, two agents, two to three tool calls; off the critical path |

The design consequence: the rubric is scheduled with a 1.2 s debounce and at least 3 s between calls so that a 2 to 3 s model never falls behind a conversation, and the payment decision does not wait for any model at all.

## 4. The payment-decision policy check

The fusion formula is `score = 0.65 x call_risk + 0.35 x payee_risk`, plus +0.10 for a safe-account or credential demand, +0.05 for authority impersonation combined with a threat, +0.10 for a high or critical payee during a coercive call, +0.05 for amounts of 50,000 rupees or more and +0.05 for amounts above five times the customer's usual transfer; warn at 0.45, hold at 0.70, hold_and_alert when the profile has a trusted contact.

Checking the two boundary cases in the set:

- **call_009 (job scam, low-band payee at run time, 2,000 rupees):** 0.65 x 0.85 gives 0.55; the ledger-derived payee score of about 0.05 adds 0.02; the rubric flagged `safe_account` (the caller routed the fee through a "payout" account), which adds 0.10; no authority-plus-threat bump, no high-risk-payee bump, no amount bumps. Result 0.67, warn. Lowering the hold threshold to 0.65 would turn this into a hold, but it would also mean a hold on every small transfer to a clean payee whenever the call is merely suspicious, which is exactly the friction that makes customers switch a guardian off. The product's answer for this case is the spoken warn plus the agent path: the ADK decision agent sees the same evidence and may upgrade to a hold, and the policy floor guarantees it cannot go the other way.
- **call_033 (hospital deposit, benign, established hospital VPA):** rubric 0.10, low-band payee (0.19), amount 60,000 rupees, so both amount bumps apply (+0.05 for 50,000 or more, +0.05 for more than five times the 5,000-rupee typical transfer). Result about 0.23, well under 0.45, proceed. The other hard negatives with urgency and money (call_034 visa fee of 42,000, call_036 school fees of 21,500, call_037 rent of 18,000) resolve to proceed for the same reason: with call risk near zero, no payee bump and no safe-account bump, the amount bumps alone (at most 0.10) cannot reach the warn threshold.

The policy is unit-tested in `tests/test_policy_and_audio.py` and is the floor for the agent: `final = max(agent_action, policy_action)` in `app/payment.py`, so nothing the agent says can turn a policy hold into a proceed.

## 5. System tests on the deployed service

These are not scored like the dataset; each is a pass/fail check of a path the dataset cannot exercise.

| Test | What it does | Result |
|---|---|---|
| `scripts/smoke_ws.py <url>` | Creates a text-mode session, posts the four-line Hindi CBI script, pays 2 lakh to `cbi.verification@rakshakdemo`, measures time to the `decision` event and the first private `rakshak_audio` message, waits for the ADK `case_update`, then runs a typed turn through the post-hold `gemini-3.8-live` conversation socket | Passed on the public URL: hold event 20 ms to 1.2 s after Pay, voice about 100 ms when prewarmed, agent update `decided_by adk_agent` within the 60 s window, Live conversation answered |
| `scripts/smoke_live_audio.py <url>` | Synthesises three Hindi scam sentences as caller audio, rings the session over `/ws/call/{id}/caller`, accepts as the user, streams the audio at real-time pace in 100 ms chunks with 1.5 s pauses, and reads the events socket | Passed: 3 correct transcript turns from `gemini-3.5-transcribe-live`, risk updates 0.9 to 1.0, whisper fired, audio relayed to the user leg |
| Two-way relay | Two browsers on the same session, each with a microphone, speaking in turn | Both parties received each other's audio; each leg transcribed on its own Live session with the correct speaker label |
| `uv run pytest` | 10 offline tests with `RAKSHAK_FAKE_LLM=1`: the API flow, the policy, audio helpers | Passed |

## 6. Limitations

- **Self-authored data.** All 50 calls were written by the team to resemble patterns in public advisories. The adversarial block was written after the base set, by the same people, with the rubric prompt in front of them; it raises the bar but does not remove the authorship bias. A perfect score on this set is evidence that the rubric reads coercion rather than keywords, not evidence of field accuracy.
- **Small languages.** Kannada and Tamil have two calls each. Hindi output quality was checked by a Hindi speaker; Kannada and Tamil outputs (rubric reasons and TTS) have not been reviewed by native speakers.
- **Transcript, not audio.** The dataset evaluates the rubric on clean text. Transcription errors from real speech (accents, line noise, code-switching mid-sentence) are only covered by the single live-audio smoke test. The live transcriber emits per utterance, so a long sentence can land as two turns.
- **One run, one model.** The numbers are from one evaluation run of `gemini-3.5-flash`; model updates can move scores. The harness writes a timestamped result on every run so a later run can be compared.
- **The agent is not scored.** The ADK pipeline's decisions, tool calls and user messages are captured on every case but were not evaluated against labels; the policy floor means the agent cannot lower a score in the dataset sense, but its upgrade and message quality are unmeasured.
- **Synthetic payees and ledger.** Payee rows are synthetic; the ledger stream reproduces the profile shapes. The fusion's payee term is therefore tested on designed, not observed, distributions.
- **No override rate.** The product's most important field metric, how often customers override a hold and whether those overrides were right, cannot exist without users.

## 7. What a bank would do next

1. **Real call corpus, human-labelled.** Take consented recordings from the bank's own in-app calls or a telco partner's fork, transcribe them with the same `gemini-3.5-transcribe-live` path, and have two fraud analysts label scam type, stage and the eight signals with adjudication of disagreements. Target 500 calls with at least 100 confirmed scams and 100 hard negatives from the bank's complaints desk (genuine fraud-desk calls, collections calls, hospital and school payments).
2. **Audio-in evaluation.** Score the rubric on the transcriber's output rather than clean text, so transcription errors are inside the measurement, and report word error rate per language alongside.
3. **Threshold calibration per segment.** Fit the warn and hold thresholds (already per-profile fields) to the bank's loss and friction targets per customer segment, and publish the false-positive rate at the chosen operating point rather than at a single 0.70.
4. **Override and outcome tracking.** Log every override with its reason and follow the payment to its outcome (complaint filed, chargeback, nothing) so precision is measured on consequences, not labels.
5. **Agent evaluation.** Score the ADK decision agent's action and the user message against the analysts' labels, and the authority check against the advisory table, so the agent's upgrades can be trusted and its message quality improved in each language.
6. **Ledger features from real data.** Replace the synthetic ledger with `sql/payee_risk.sql` on the bank's own transactions and the DoT FRI, I4C and KYC feeds, and re-run the payment-level check with real payee rows.
7. **Native-speaker review.** Kannada and Tamil rubric reasons and TTS clips reviewed and corrected before any customer in those languages sees them.
