# Rakshak demo video: how to record it, what to say, how to submit it

Read this one document. It replaces the longer shot list. Everything in it was tested on the live service. Team: Prod Pilots (team leader: Lohith DS).

## 1. Your doubts, answered

**How long must the video be?** 3 to 4 minutes. Our target is **3:30**. The hard window is 3:00 to 4:00, and to stay clear of any rounding by the player or the portal, never export under 3:05 or over 3:55. The organisers may penalise a longer video, and a video that does not clearly show the working product means the submission does not progress. So everything after the 15-second title card is the live product on the public URL, recorded from a real phone.

**Should I show slides before the demo?** No slides. Open with a 15-second title card that carries the problem, then go straight to the product. The deck is a separate submission item (the official template file `Rakshak_Pitch_Deck_Prod_Pilots.pptx`); the video is the product in action, which is what the organisers asked for. Two deck stills appear only at the very end, under the closing line.

**Must the risk score and the voice both be in the video?** Yes, and both are on screen and audible without any trick:

| What the judge must see or hear | Where it happens | How it is captured |
|---|---|---|
| Balance hidden behind a PIN | Customer home screen: the balance shows dots until the demo PIN `1234` is entered | Screen recording of the phone |
| Risk score climbing | Call screen on the customer phone: gauge goes about 50%, 80%, 90%, 98%, 100% as the caller speaks | Screen recording of the phone |
| Live transcript and signal chips | Same screen, below the gauge | Screen recording |
| Rakshak's private whisper | When the risk first passes 85% (after caller line 3), a short English voice (about 7 seconds) plays on the customer phone only | Phone's internal audio |
| The payment pause and Rakshak's spoken warning | Right after Pay: red hold screen, 30:00 countdown, English voice for about 26 seconds | Phone's internal audio |
| Talking to Rakshak (Gemini Live) | Hold screen, **Talk to Rakshak**: the customer asks "Why did you stop my payment?" aloud, Rakshak answers by voice, then "Keep the hold and call my sister" fires the `call_trusted_contact` tool and a toast "Calling Priya..." appears | Phone's internal audio **plus microphone** (the only beat that needs the mic) |
| The family alert | A second device on `/family?user=demo-user`: a chime, "Payment paused", and the button "Call Lohith now" | Screen recording of the second device with its internal audio |
| Post-call carry-over (optional) | After hanging up, a fresh app launch and Pay to the same payee within 60 minutes is still held, with the reason "A high-risk call (...) ended N minutes ago" | Screen recording of the phone |
| The same risk score on the bank side | Fraud desk, top of the case: risk score 1.0, policy score, agent decision | Laptop screen recording |

**What is the safest way to get the audio?** Record the phone's screen with the recorder set to **device audio (internal sound)**, not the microphone. The caller's voice, the whisper and Rakshak's voice are all played by the app, so the recorder captures them digitally, with no echo and no room noise. Your own voiceover is recorded separately afterwards and mixed in. This is the single most important decision in this guide. The one exception is the 20-second "Talk to Rakshak" beat, where your own spoken question must be heard: record it as a separate short take with the recorder on **device audio plus microphone**, wearing earphones (section 4, step 8).

**One person or two?** Method A below needs one person and one phone (plus any second device for the family alert), and it cannot fail on audio. Method B uses a teammate for a real two-way call and looks more impressive. Record Method A first. If time allows, record Method B and use it instead.

## 2. What the finished video looks like (target 3:30, hard window 3:00 to 4:00)

| Time | What is on screen | Audio |
|---|---|---|
| 0:00 to 0:15 | Title card: "Rakshak. Stop the scam at the moment of payment." with the three numbers (81.8%, 22,495 crore, 24% recovered) | Voiceover 1 |
| 0:15 to 0:31 | Customer phone home screen: "Hello, Lohith"; tap the hidden balance, type PIN `1234`, the balance appears (about 10 seconds); then the Guardian card: Guardian on, trusted contact Priya | Voiceover 2 |
| 0:31 to 1:06 | The call: incoming call, transcript, gauge climbing, chips, reasons, the whisper after caller line 3 | Voiceover 3 with gaps for the caller's voice and the whisper |
| 1:06 to 1:16 | The demand, Open UPI pay, the filled form, tap Pay | Voiceover 4 |
| 1:16 to 1:56 | **The hold (climax)**: red screen, countdown, evidence cards, payee card, "Priya has been told", the typed-amount override sheet | Rakshak's voice first (no voiceover), then voiceover 5 |
| 1:56 to 2:16 | **Talk to Rakshak**: tap Talk to Rakshak, ask "Why did you stop my payment?", Rakshak answers by voice through Gemini Live, say "Keep the hold and call my sister", the toast "Calling Priya..." appears | Voiceover 6 around the live exchange (no voiceover over it) |
| 2:16 to 2:28 | **The family phone**: the second device on `/family?user=demo-user` chimes and shows "Payment paused" and "Call Lohith now" | Chime first, then voiceover 7 |
| 2:28 to 2:43 | **Post-call carry-over (optional)**: call ended, fresh app launch, Pay to the same payee, held again with "A high-risk call (...) ended N minutes ago" | Voiceover 8 |
| 2:43 to 3:10 | Fraud desk: risk score, policy versus agent, ADK trace, drafted 1930 referral, "SMS versus Rakshak" | Voiceover 9 |
| 3:10 to 3:30 | Two stills from the deck: evaluation and architecture, then the end card with URL, repo and "Team Prod Pilots" | Voiceover 10 |

Total: **3:30**. If you drop the optional carry-over beat, the video is 3:15, still inside the window; do not cut anything else, or it falls under 3:05.

Rule: the payment screen is the climax. Spend about 15 seconds on the risk gauge and about 40 seconds on the hold, followed by the 20-second conversation on the same hold screen.

## 3. Before you record (25 minutes)

1. **Check the service is up.** Open https://rakshak-223197895518.asia-southeast1.run.app/api/health in a browser. It must show `"ok":true`. The service runs one always-on instance, so there is no cold start.
2. **Charge and tidy the phone.** Do Not Disturb on, brightness about 80%, portrait lock on, media volume at about 70%, close all other tabs and apps, hide notifications. Remove the `Developer options` section from view (leave it collapsed).
3. **Use a fresh session code every take**: `vid1`, `vid2`, `vid3`. The customer URL is
   `https://rakshak-223197895518.asia-southeast1.run.app/?session=vid1&user=demo-user`
   The home screen must read "Hello, Lohith", Guardian on, trusted contact Priya (sister), Rakshak speaks English. If it shows anything else, add `&user=demo-user` to the URL. The carry-over beat uses one extra code per take (`vid2b`), because it must be a fresh app launch.
4. **Check the balance is hidden.** Under "Savings account" the balance shows dots until a PIN is entered (demo PIN `1234`). In the video you show the reveal: tap the balance, type `1234`, let the balance show for a few seconds (about 10 seconds for the whole moment). It hides itself again after 30 seconds, so rehearse the tap once.
5. **Set the screen recorder to internal audio.**
   - **Pixel or stock Android 11 or later**: Quick Settings, Screen record, tap the gear, choose "Record audio from: Device audio". Do not choose microphone. (For the Talk to Rakshak take you switch to "Device audio and microphone".)
   - **Samsung**: Quick Panel, Screen recorder, Sound settings, "Media sounds". Not "Media sounds and mic". (For the Talk to Rakshak take: "Media sounds and mic".)
   - **iPhone**: Control Centre, Screen Recording. Long-press the button and make sure the microphone is **off**. iOS records the app's sound by default. (For the Talk to Rakshak take, see section 4 step 8.)
6. **Ten-second audio test (do not skip).** Start the recorder, open the customer URL, tap **Test an incoming call**, choose the English script and tap **Auto-play script**, wait about 10 seconds so the caller's voice speaks, stop. Play the clip back. If you hear the caller's deep synthetic voice, the setup is correct. If the clip is silent, switch the recorder setting (step 5) or use the fallback in section 8.
7. **Prepare the family device.** A second phone is best (a teammate's or an old phone); a laptop browser window works too. Open `https://rakshak-223197895518.asia-southeast1.run.app/family?user=demo-user`, tap the page once so the browser allows the chime, and leave it open. It chimes only for alerts that arrive after the page loaded, so it must be open **before** you tap Pay. Set its screen recorder to device audio as in step 5.
8. **Dry run the whole flow once without recording**, including Talk to Rakshak and the family device. This also pre-generates Rakshak's spoken warning for the amount, so on the real take the voice starts instantly instead of a few seconds late. Use the same payee and amount you will use in the take.

## 4. Method A: solo, one phone (recommended)

The caller is a synthetic voice played by the app, so you need no teammate. The microphone is used only for the short Talk to Rakshak take.

1. Phone: open `https://rakshak-223197895518.asia-southeast1.run.app/?session=vid2&user=demo-user`. Finish or skip onboarding. Stay on the home screen; make sure the balance shows dots.
2. Laptop: open `https://rakshak-223197895518.asia-southeast1.run.app/desk` in a second window for later. Do not record it yet.
3. Family device: open `/family?user=demo-user` (section 3 step 7), tap it once, and **start its screen recording now**. Leave it running until after the hold.
4. **Start the phone screen recording** (device audio only). Wait one second.
5. Beat 2 (about 16 seconds): tap the hidden balance, type `1234`, let the balance show for about 3 seconds (about 10 seconds for the whole PIN moment). Then slowly scroll so the Guardian card (Guardian on, Priya, English) is visible.
6. Beat 3: tap **Test an incoming call**. On the call screen the script is already set to "Cyber Crime Branch money-laundering case (English)". Tap **Auto-play script**. Do not touch the phone for about 95 seconds. The caller speaks in a deep voice; the transcript fills in; the gauge climbs; signal chips appear; after the third caller line the whisper plays (about 7 seconds). Do not scroll; keep the gauge and transcript in the frame.
7. When a toast says the caller is demanding payment, tap **Open UPI pay**. The form is filled in: `police.hq.escrow@rakshakdemo`, Police HQ Escrow, 5,40,000. Tap **Pay**. Beat 5: the hold screen appears at once and Rakshak speaks in English. **Stay completely still for 26 seconds** so the voice plays in full. Then scroll slowly down through "What Rakshak found": the call, the payee card with its lineage line, the trusted-contact alert. Tap **I know this person, pay anyway** so the typed-amount sheet appears, wait 3 seconds, tap **Go back**. **Stop the phone recording**; stay on the hold screen. Stop the family device's recording too: it now holds the chime and the alert.
8. **Beat 6, the Talk to Rakshak take** (about 20 seconds in the edit). Put your earphones in, so the microphone picks up only your voice and not the phone's speaker. Switch the recorder to **device audio and microphone** (Pixel: "Device audio and microphone"; Samsung: "Media sounds and mic"), start a new short recording, then:
   - Tap **Talk to Rakshak** and allow the microphone if asked.
   - Say clearly: **"Why did you stop my payment?"** Rakshak answers by voice through Gemini Live. Let it finish.
   - Say: **"Keep the hold and call my sister."** The `call_trusted_contact` tool fires and a toast appears: "Calling Priya...". (Rakshak may also keep the hold through its `keep_hold` tool, with the toast "Hold kept. You are safe."; both are fine on screen.)
   - Wait 2 seconds, tap **End conversation**, stop the recording.
   - Alternative if you prefer one continuous take: set the whole Method A recording to device audio and microphone from step 4 and wear earphones throughout, in a quiet room. Then the voiceover-free gaps also carry room sound, so keep the room silent.
   - iPhone: iOS screen recording and a web page using the microphone do not combine reliably. Try once; if your question or Rakshak's answer is missing, record this beat on an Android phone with the same URL, or film the iPhone with a second device in a quiet room.
9. **Beat 8, post-call carry-over (optional, about 15 seconds).** Switch the recorder back to device audio only. Leave the hold screen, go back to the call and tap **End call**. Wait about two minutes (so the reason reads "ended 2 minutes ago" rather than "0 minutes ago"). Then open the customer URL with a fresh code, which is a fresh app launch: `https://rakshak-223197895518.asia-southeast1.run.app/?session=vid2b&user=demo-user`. Start the recording, tap **Pay via UPI**, enter the same payee (`police.hq.escrow@rakshakdemo`, Police HQ Escrow, 540000), tap **Pay**. The payment is held again; scroll to the reasons and hold on "A high-risk call (...) ended 2 minutes ago" for 3 seconds. Stop. The fresh code matters: on the same session code the hold still happens, but it shows the call's own reasons instead of the carry-over line. The carry-over window is 60 minutes.
10. Total raw recording is about 4 to 5 minutes across the takes; the edit trims it.
11. **Laptop recording (fraud desk).** Press Cmd+Shift+5, choose "Record Selected Portion" over the `/desk` window, start, click the case from the first hold (not the carry-over case), scroll slowly through: status timeline, "SMS versus Rakshak", decision versus policy, call rubric, payee evidence and lineage, ADK trace, fraud-desk record and the drafted 1930 referral. About 40 seconds raw for 27 seconds in the edit. Stop.
12. **Two stills**: export the evaluation slide and the architecture slide from the submission deck `Rakshak_Pitch_Deck_Prod_Pilots.pptx` as PNG images. If that deck is not final yet, use slide 10 (evaluation) and slide 6 (architecture) of `Rakshak_Deck.pdf`, and swap them later only if the numbers differ.

## 5. Method B: live two-way call with a teammate (more impressive)

Use this if you can rehearse once. It needs two phones and two people, both wearing earphones, plus the family device from section 3 step 7 (a third phone or the laptop).

- **Customer phone (you):** `https://rakshak-223197895518.asia-southeast1.run.app/?session=vid3&user=demo-user`. Stay on the home screen. Screen recorder on **"Device audio and microphone"** with earphones plugged in, so your own voice is captured by the microphone and the caller and Rakshak by internal audio, with no echo. Because the microphone is already on, the Talk to Rakshak beat is recorded in the same take. (iPhone users should use Method A instead; iOS screen recording and a web page using the microphone do not combine reliably.)
- **Caller phone (teammate):** `https://rakshak-223197895518.asia-southeast1.run.app/call?session=vid3`. Before tapping Call, check the pill says **"Customer's phone: open"**. Then tap the green **Call**, allow the microphone. Your phone rings; tap **Answer** and allow the microphone.

Start with the PIN moment (Method A step 5) before the call rings. Teammate reads this short script, one sentence at a time with a pause. Lohith (you) replies naturally. The risk values were measured on the live service:

| # | Teammate says (caller) | You say (Lohith) | Gauge shows |
|---|---|---|---|
| 1 | "Good afternoon, this is the Cyber Crime Branch, Mumbai. Am I speaking with Lohith?" | "Yes, speaking. What is this about?" | about 50% |
| 2 | "An account opened with your PAN has moved three crore rupees for a trafficking syndicate. A non-bailable warrant has been issued in your name." | "What? I have never opened any account in Mumbai." | about 80% |
| 3 | "If you are innocent, cooperate. You are under digital arrest. Do not tell anyone, not even your family, or they become accused too. Do not hang up." | "Okay. What do I have to do?" | about 90%, **whisper plays** |
| 4 | "Your savings must be moved to the Police Headquarters escrow account for verification. You will get every rupee back in forty-eight hours." | "That is all my money." | about 98% |
| 5 | "Open your UPI app. The ID is police dot h q dot escrow at rakshakdemo. Transfer five lakh forty thousand now, while I watch." | "Okay, opening the app." | 100% |

The call lasts about 70 seconds. Then, on your phone: tap **Open UPI pay**, type `police.hq.escrow@rakshakdemo`, name `Police HQ Escrow`, amount `540000`, tap **Pay**. (Type the three values quickly; the edit cuts the typing.) Keep the recording running through the hold, exactly as in Method A step 7, then do the Talk to Rakshak beat in the same take (Method A step 8, without switching the recorder). The teammate ends the call afterwards; the carry-over beat (Method A step 9) is recorded the same way.

## 6. The voiceover (record it after, not during)

Record in a quiet room, phone or laptop microphone, held at a steady distance. Speak calmly, a little slower than normal. About 470 words in total. Read each block while watching the matching part of your edited video.

| Block | Time on the timeline | Say exactly this |
|---|---|---|
| 1 | 0:00 to 0:15 | "In Singapore, eighty-two percent of scam cases in 2025 were transfers the victim made themselves, on a call, under pressure. India lost over twenty-two thousand crore rupees, and recovered about a quarter. An alert after the debit is too late. This is Rakshak." |
| 2 | 0:15 to 0:31 | "Meet Lohith, a small-business owner and SafePay customer. Even his balance stays hidden until he enters his PIN. Guardian mode is on. Rakshak listens only during calls, and it tells his sister Priya only if a payment is paused." |
| 3a | 0:31 to 0:38 | "A call comes in from an unknown number. Rakshak transcribes both sides live and scores the conversation for coercion." |
| 3b | 0:38 to 0:46, pause about 8 seconds | (say nothing; let the caller's voice and the rising gauge play) |
| 3c | 0:46 to 0:55 | "Authority, a warrant, a threat: the risk is already high. Then secrecy, 'tell no one', and it crosses eighty-five percent." |
| 3d | 0:55 to 1:06 | "Rakshak now speaks to Lohith privately. The caller hears nothing." (then say nothing for 7 seconds while the whisper plays) |
| 4 | 1:06 to 1:16 | "The scammer demands the money: five lakh forty thousand rupees to a so-called police escrow account. Lohith opens the payment screen and taps Pay." |
| 5a | 1:16 to 1:26 | (say nothing; let Rakshak's spoken warning play at full volume for its first three sentences, about 10 seconds; it runs 26 seconds in all, so let it continue quietly under the voiceover that follows) |
| 5b | 1:26 to 1:56 | "In under a second the payment is paused for thirty minutes, and Rakshak explains why, in his own language. It checks the payee against the bank's ledger: an account twelve days old that received money from several people and moved almost all of it out within hours, flagged by the telecom risk indicator and named in cybercrime complaints. His sister Priya has been told. Lohith can cancel, talk to Rakshak by voice, or, if he truly knows the payee, override by typing the amount." |
| 6a | 1:56 to 1:59 | "He taps Talk to Rakshak and asks it himself." |
| 6b | 1:59 to 2:11 | (say nothing; let Lohith's question, Rakshak's spoken answer, "Keep the hold and call my sister" and the toast play) |
| 6c | 2:11 to 2:16 | "That was Gemini Live: it answers by voice, and calls a tool to ring Priya." |
| 7 | 2:16 to 2:28 | (let the chime play for one second first) "Priya's phone chimed the moment the payment stopped: who he was paying, how much, that it looks like a scam, and one button, call Lohith now." |
| 8 | 2:28 to 2:43 (optional beat) | "Scammers often say: hang up, and pay later. So Lohith hangs up, opens the app afresh and tries the same account again. It is still held, with the reason on screen. Rakshak remembers a high-risk call for an hour." |
| 9 | 2:43 to 3:10 | "On the bank's fraud desk, the same case, with a risk score of one point zero. A deterministic policy decided in under a hundred milliseconds. An A D K agent running Gemini then investigated the payee and checked the official advisories, and confirmed within seconds. It can make the decision stricter, never weaker. The desk gets the full trace, a drafted cybercrime helpline referral, and the contrast: an S M S arrives after the money has gone." |
| 10 | 3:10 to 3:30 | "On our own fifty labelled calls in six languages, including hard negatives and adversarial scams, precision and recall were one point zero, with a mean scoring time of about three seconds. It runs on Google Cloud: Gemini, A D K and Cloud Run, with a live ledger stream. Rakshak, by Prod Pilots: stop the scam at the moment of payment." |

Two honesty rules for the voiceover: say "demo ledger" or add the on-screen caption "Synthetic ledger and calls (demo data)" during blocks 5, 8 and 9, and say "our own labelled calls", not "real calls". Judges respect it, and the deck says the same.

## 7. Editing (60 minutes, any free editor)

Use CapCut, iMovie or DaVinci Resolve. Steps:

1. Import the phone recordings (main take, Talk to Rakshak take, carry-over take), the family device recording, the laptop recording, the two PNG stills and your voiceover.
2. **Cut the recordings into beats** and trim all waiting: remove the home-screen idle time, the typing in the pay form (jump cut), the pause before Gemini Live answers, the two-minute wait before the carry-over, and any time the phone sits unchanged. Do not speed up Rakshak's own voice. Trim Rakshak's spoken answer in beat 6 to its first two sentences (about 7 seconds) if it runs long.
3. **Put the voiceover on its own track.** Lower the phone's audio to about 25% while the voiceover is speaking. Keep it at 100% during the silent gaps in blocks 3b, 3d, 5a and 6b and the chime at the start of block 7, so the caller's voice, the whisper, Rakshak's warning, the conversation and the chime are heard clearly.
4. **Title card (0:00 to 0:15):** use the title slide of the template deck as a still, or a plain navy card with the headline and the three numbers.
5. **Captions (small, bottom of screen):** "Balance hidden behind a PIN", "Risk 85%: private whisper", "Payment paused for 30 minutes", "Gemini Live: voice conversation with tools", "Priya's phone: the family alert", "After hanging up: still held", "Synthetic demo data". Add the live URL as a caption on the end card.
6. **End card (last 5 seconds):** the URL `https://rakshak-223197895518.asia-southeast1.run.app`, the GitHub repo `github.com/devaramanelohith/rakshak-agent`, and "Team Prod Pilots".
7. **Export:** 1080p, H.264, about 30 fps, AAC audio. Open the exported file and read the length. **It must be between 3:00 and 4:00; aim for 3:30, and never export under 3:05 or over 3:55.** If it is over 3:55, cut idle frames or shorten the fraud-desk scroll. If it is under 3:05 (for example after dropping the optional carry-over beat and trimming hard), restore the carry-over beat or let the hold screen run a few seconds longer. Never pad with slides; every added second must show the working product.

## 8. If something goes wrong

| Problem | Fix |
|---|---|
| The recorded clip has no caller or Rakshak voice | The recorder is on microphone mode or the app audio was blocked. Switch to device audio (section 3 step 5); tap the screen once after opening the page so the browser allows sound; re-run the ten-second test. Fallback: record the phone's screen normally and also film it with a second phone or the laptop camera in a quiet room with the phone's speaker up, and use that audio. |
| Gauge stays at 0% for a few seconds | The first scoring takes about 3 seconds after each line. Wait; it updates after the first caller line. |
| Rakshak's warning starts a few seconds after the hold screen appears | The voice for that amount was not pre-generated. Run the dry run (section 3 step 8) with the same amount, or cut the gap in the edit. |
| No whisper | It plays only when the risk first passes 85%. The scripted line 3 reaches 90%. If you changed the wording, the risk may stay lower; use the script above. |
| Talk to Rakshak does not answer, or your question is missing from the clip | Allow the microphone when the browser asks; check the recorder is on device audio and microphone for that take; wear earphones so there is no echo. On iPhone, record this beat on an Android phone or film it (section 4 step 8). |
| No "Calling Priya..." toast | Say the sentence again, clearly: "Keep the hold and call my sister." Gemini Live decides when to call the tool; a second ask usually fires it. Cut the first attempt in the edit. |
| The family device shows the alert but makes no sound | The page was not tapped after loading, or it was opened after Pay (it chimes only for new alerts). Re-open it, tap once, and run the hold again on a fresh session code. On a Mac, Cmd+Shift+5 does not record system sound, so prefer a second phone for this beat. |
| The carry-over hold does not show "A high-risk call (...) ended N minutes ago" | You paid on the same session code, so the call's own reasons are shown. Open the customer URL with a fresh code (`vid2b`) and pay again, within 60 minutes of the call. |
| Caller phone says "Customer's phone: NOT open on this code" | The two phones are on different session codes. Re-open both URLs with exactly the same code. |
| Payee card numbers differ from the voiceover | The ledger is live, so values move a little. The voiceover avoids exact figures on purpose; do not read numbers off the card. |
| iPhone screen recording misses the mic | Use Method A on iPhone; only the Talk to Rakshak beat needs the microphone (section 4 step 8). |
| Exported length is outside 3:05 to 3:55 | Section 7 step 7. |
| Anything fails near the deadline | Use the voiced replay (Method A). It depends only on the app and the recorder. |

## 9. Upload and submit (today)

1. **Upload to YouTube.** Title: "Rakshak by Prod Pilots: stop the scam at the moment of payment | AI Builder Cup 2026". Description: the live URL, the GitHub repo, "Team Prod Pilots (team leader: Lohith DS), BFSI theme", and a note that data is synthetic. Audience: not made for kids. Visibility: **Public** (the brief asks for a public link; Unlisted usually works but Public removes any doubt).
2. **Check the length on YouTube.** The player must show a duration between 3:00 and 4:00 (about 3:30). If it shows anything else, re-export and re-upload before submitting.
3. **Test the link logged out.** Open it in a private window on a different device and watch the first 10 seconds, including audio, then skip to the hold and the Talk to Rakshak beat to check the voices are there.
4. **Submission items for the portal** (all from this package):

| Item | File or link |
|---|---|
| Team | Prod Pilots, team leader Lohith DS |
| Theme | BFSI: Intelligent Risk, Fraud and Financial Experiences |
| Pitch deck (official template only) | `Rakshak_Pitch_Deck_Prod_Pilots.pptx`. A deck not on the organisers' template may be disqualified; `Rakshak_Deck.pdf` is supporting material only |
| Demo video | your public YouTube link (3 to 4 minutes) |
| Deployed prototype | https://rakshak-223197895518.asia-southeast1.run.app |
| Public GitHub repository | https://github.com/devaramanelohith/rakshak-agent (tag v1.0) |
| Brief description (what we built; how Firebase, Firestore, Cloud Run and Gemini are used) | `submission/BRIEF_DESCRIPTION.md` |

5. **Supporting documents** to keep ready or attach if the portal allows: `Rakshak_Evaluation_Report.pdf` (the evals), `Rakshak_Judge_Pitch_and_QA.pdf` (spoken pitch and answers to likely questions), `Rakshak_Submission_Checklist.pdf` (portal steps, pre-flight checks and how to keep everything alive during evaluation).
6. **Submit, then screenshot the confirmation.** Do not wait for the last hour; the portal's exact cut-off time is not published. Keep Discord and portal notifications on.
7. **Leave the video alone during evaluation (19 October to 6 November).** Do not delete, unlist, re-upload or trim it; the link in the portal must keep working. The deployed link and the repository have the same rule (see the checklist, "Keep it alive during evaluation").

## 10. Order of work if you have about three and a half hours

| Minutes | Task |
|---|---|
| 0 to 25 | Section 3: health check, recorder setting, ten-second audio test, family device ready, dry run including Talk to Rakshak |
| 25 to 65 | Record Method A: main phone take with the family device recording, the Talk to Rakshak take, the carry-over take; then the fraud-desk recording and the two stills |
| 65 to 85 | Record the voiceover (read section 6 aloud twice, record the second time) |
| 85 to 145 | Edit and export (section 7); check the length is between 3:05 and 3:55 |
| 145 to 165 | Upload, check the YouTube duration, test logged out |
| 165 to 200 | Confirm the template deck `Rakshak_Pitch_Deck_Prod_Pilots.pptx` and `submission/BRIEF_DESCRIPTION.md` are final, fill the portal fields, submit, screenshot the confirmation |
