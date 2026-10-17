# Rakshak demo video: how to record it, what to say, how to submit it

Read this one document. It replaces the longer shot list. Everything in it was tested on the live service on submission day.

## 1. Your doubts, answered

**Should I show slides before the demo?** No slides. Open with a 15-second title card that carries the problem, then go straight to the product. The deck PDF is a separate submission item; the video is the product in action, which is what the organisers asked for.

**Must the risk score and the voice both be in the video?** Yes, and both are on screen and audible without any trick:

| What the judge must see or hear | Where it happens | How it is captured |
|---|---|---|
| Risk score climbing | Call screen on the customer phone: gauge goes about 50%, 80%, 90%, 98%, 100% as the caller speaks | Screen recording of the phone |
| Live transcript and signal chips | Same screen, below the gauge | Screen recording |
| Rakshak's private whisper | When the risk first passes 85%, a short English voice (about 7 seconds) plays on the customer phone only | Phone's internal audio |
| The payment pause and Rakshak's spoken warning | Right after Pay: red hold screen, 30:00 countdown, English voice for about 26 seconds | Phone's internal audio |
| The same risk score on the bank side | Fraud desk, top of the case: risk score 1.0, policy score, agent decision | Laptop screen recording |

**What is the safest way to get the audio?** Record the phone's screen with the recorder set to **device audio (internal sound)**, not the microphone. The caller's voice, the whisper and Rakshak's voice are all played by the app, so the recorder captures them digitally, with no echo and no room noise. Your own voiceover is recorded separately afterwards and mixed in. This is the single most important decision in this guide.

**One person or two?** Method A below needs one person and one phone, and it cannot fail on audio. Method B uses a teammate for a real two-way call and looks more impressive. Record Method A first. If time allows, record Method B and use it instead.

## 2. What the finished video looks like (target 2:50, never over 3:00)

| Time | What is on screen | Audio |
|---|---|---|
| 0:00 to 0:15 | Title card: "Rakshak. Stop the scam at the moment of payment." with the three numbers (81.8%, 22,495 crore, 24% recovered) | Voiceover 1 |
| 0:15 to 0:28 | Customer phone home screen: "Hello, Lohith", Guardian on, trusted contact Priya | Voiceover 2 |
| 0:28 to 1:10 | The call: incoming call, transcript, gauge climbing, chips, reasons | Voiceover 3 with gaps for the caller's voice and the whisper |
| 1:10 to 1:22 | The demand, Open UPI pay, the filled form, tap Pay | Voiceover 4 |
| 1:22 to 2:00 | **The hold (climax)**: red screen, countdown, evidence cards, payee card, "Priya has been told", the typed-amount override sheet | Rakshak's voice first (no voiceover), then voiceover 5 |
| 2:00 to 2:30 | Fraud desk: risk score, policy versus agent, ADK trace, drafted 1930 referral, "SMS versus Rakshak" | Voiceover 6 |
| 2:30 to 2:50 | Two stills from the deck: evaluation (slide 10) and architecture (slide 6), then the end card with URL and repo | Voiceover 7 |

Rule: the payment screen is the climax. Spend about 15 seconds on the risk gauge and about 40 seconds on the hold.

## 3. Before you record (20 minutes)

1. **Check the service is up.** Open https://rakshak-223197895518.asia-southeast1.run.app/api/health in a browser. It must show `"ok":true`. The service runs one always-on instance, so there is no cold start.
2. **Charge and tidy the phone.** Do Not Disturb on, brightness about 80%, portrait lock on, media volume at about 70%, close all other tabs and apps, hide notifications. Remove the `Developer options` section from view (leave it collapsed).
3. **Use a fresh session code every take**: `vid1`, `vid2`, `vid3`. The customer URL is
   `https://rakshak-223197895518.asia-southeast1.run.app/?session=vid1&user=demo-user`
   The home screen must read "Hello, Lohith", Guardian on, trusted contact Priya (sister), Rakshak speaks English. If it shows anything else, add `&user=demo-user` to the URL.
4. **Check the balance is hidden.** Under "Savings account" the balance shows dots until a PIN is entered (demo PIN `1234`). Leave it hidden in the video, or show the reveal for 4 seconds as a privacy point.
5. **Set the screen recorder to internal audio.**
   - **Pixel or stock Android 11 or later**: Quick Settings, Screen record, tap the gear, choose "Record audio from: Device audio". Do not choose microphone.
   - **Samsung**: Quick Panel, Screen recorder, Sound settings, "Media sounds". Not "Media sounds and mic".
   - **iPhone**: Control Centre, Screen Recording. Long-press the button and make sure the microphone is **off**. iOS records the app's sound by default.
6. **Ten-second audio test (do not skip).** Start the recorder, open the customer URL, tap **Test an incoming call**, choose the English script and tap **Auto-play script**, wait about 10 seconds so the caller's voice speaks, stop. Play the clip back. If you hear the caller's deep synthetic voice, the setup is correct. If the clip is silent, switch the recorder setting (step 5) or use the fallback in section 8.
7. **Dry run the whole flow once without recording.** This also pre-generates Rakshak's spoken warning for the amount, so on the real take the voice starts instantly instead of a few seconds late. Use the same payee and amount you will use in the take.

## 4. Method A: solo, one phone (recommended)

The caller is a synthetic voice played by the app, so you need no teammate and no microphone.

1. Phone: open `https://rakshak-223197895518.asia-southeast1.run.app/?session=vid2&user=demo-user`. Finish or skip onboarding. Stay on the home screen.
2. Laptop: open `https://rakshak-223197895518.asia-southeast1.run.app/desk` in a second window for later. Do not record it yet.
3. **Start the phone screen recording.** Wait one second.
4. Beat 2 (about 13 seconds): rest on the home screen. Slowly scroll so the Guardian card (Guardian on, Priya, English) is visible.
5. Beat 3: tap **Test an incoming call**. On the call screen the script is already set to "Cyber Crime Branch money-laundering case (English)". Tap **Auto-play script**. Do not touch the phone for about 95 seconds. The caller speaks in a deep voice; the transcript fills in; the gauge climbs; signal chips appear; at the third caller line the whisper plays. Do not scroll; keep the gauge and transcript in the frame.
6. When a toast says the caller is demanding payment, tap **Open UPI pay**. The form is filled in: `police.hq.escrow@rakshakdemo`, Police HQ Escrow, 5,40,000. Tap **Pay**.
7. Beat 5: the hold screen appears at once and Rakshak speaks in English. **Stay completely still for 26 seconds** so the voice plays in full. Then scroll slowly down through "What Rakshak found": the call, the payee card with its lineage line, the trusted-contact alert. Tap **I know this person, pay anyway** so the typed-amount sheet appears, wait 3 seconds, tap **Go back**.
8. Stop the recording. Total length is about 3 to 3.5 minutes; the edit trims it.
9. **Laptop recording (fraud desk).** Press Cmd+Shift+5, choose "Record Selected Portion" over the `/desk` window, start, click the newest case, scroll slowly through: status timeline, "SMS versus Rakshak", decision versus policy, call rubric, payee evidence and lineage, ADK trace, fraud-desk record and the drafted 1930 referral. About 40 seconds. Stop.
10. **Two stills**: open `Rakshak_Deck.pdf`, export slide 10 (evaluation) and slide 6 (architecture) as PNG images.

## 5. Method B: live two-way call with a teammate (more impressive)

Use this if you can rehearse once. It needs two phones and two people, both wearing earphones.

- **Customer phone (you):** `https://rakshak-223197895518.asia-southeast1.run.app/?session=vid3&user=demo-user`. Stay on the home screen. Screen recorder on **"Device audio and microphone"** with earphones plugged in, so your own voice is captured by the microphone and the caller and Rakshak by internal audio, with no echo. (iPhone users should use Method A instead; iOS screen recording and a web page using the microphone do not combine reliably.)
- **Caller phone (teammate):** `https://rakshak-223197895518.asia-southeast1.run.app/call?session=vid3`. Before tapping Call, check the pill says **"Customer's phone: open"**. Then tap the green **Call**, allow the microphone. Your phone rings; tap **Answer** and allow the microphone.

Teammate reads this short script, one sentence at a time with a pause. Lohith (you) replies naturally. The risk values were measured on the live service:

| # | Teammate says (caller) | You say (Lohith) | Gauge shows |
|---|---|---|---|
| 1 | "Good afternoon, this is the Cyber Crime Branch, Mumbai. Am I speaking with Lohith?" | "Yes, speaking. What is this about?" | about 50% |
| 2 | "An account opened with your PAN has moved three crore rupees for a trafficking syndicate. A non-bailable warrant has been issued in your name." | "What? I have never opened any account in Mumbai." | about 80% |
| 3 | "If you are innocent, cooperate. You are under digital arrest. Do not tell anyone, not even your family, or they become accused too. Do not hang up." | "Okay. What do I have to do?" | about 90%, **whisper plays** |
| 4 | "Your savings must be moved to the Police Headquarters escrow account for verification. You will get every rupee back in forty-eight hours." | "That is all my money." | about 98% |
| 5 | "Open your UPI app. The ID is police dot h q dot escrow at rakshakdemo. Transfer five lakh forty thousand now, while I watch." | "Okay, opening the app." | 100% |

The call lasts about 70 seconds. Then, on your phone: tap **Open UPI pay**, type `police.hq.escrow@rakshakdemo`, name `Police HQ Escrow`, amount `540000`, tap **Pay**. (Type the three values quickly; the edit cuts the typing.) Keep the recording running through the hold, exactly as in Method A step 7.

## 6. The voiceover (record it after, not during)

Record in a quiet room, phone or laptop microphone, held at a steady distance. Speak calmly, a little slower than normal. About 360 words in total. Read each block while watching the matching part of your edited video.

| Block | Time on the timeline | Say exactly this |
|---|---|---|
| 1 | 0:00 to 0:15 | "In Singapore, eighty-two percent of scam cases in 2025 were transfers the victim made themselves, on a call, under pressure. India lost over twenty-two thousand crore rupees, and recovered about a quarter. An alert after the debit is too late. This is Rakshak." |
| 2 | 0:15 to 0:28 | "Meet Lohith, a SafePay customer. Guardian mode is on. Rakshak listens only during calls, and it tells his sister Priya only if a payment is paused." |
| 3a | 0:28 to 0:36 | "A call comes in from an unknown number. Rakshak transcribes both sides live and scores the conversation for coercion." |
| 3b | pause about 8 seconds | (say nothing; let the caller's voice and the rising gauge play) |
| 3c | 0:44 to 0:54 | "Authority, a warrant, a threat: the risk is already high. Then secrecy, 'tell no one', and it crosses eighty-five percent." |
| 3d | 0:54 to 1:02 | "Rakshak now speaks to Lohith privately. The caller hears nothing." (then say nothing for 7 seconds while the whisper plays) |
| 4 | 1:10 to 1:22 | "The scammer demands the money: five lakh forty thousand rupees to a so-called police escrow account. Lohith opens the payment screen and taps Pay." |
| 5a | 1:22 to 1:32 | (say nothing; let Rakshak's spoken warning play at full volume for its first three sentences, about 10 seconds; it runs 26 seconds in all, so let it continue quietly under the voiceover that follows) |
| 5b | 1:32 to 2:00 | "In under a second the payment is paused for thirty minutes, and Rakshak explains why, in his own language. It checks the payee against the bank's ledger: an account twelve days old that received money from several people and moved almost all of it out within hours, flagged by the telecom risk indicator and named in cybercrime complaints. His sister Priya has been told. Lohith can cancel, talk to Rakshak by voice, or, if he truly knows the payee, override by typing the amount." |
| 6 | 2:00 to 2:30 | "On the bank's fraud desk, the same case, with a risk score of one point zero. A deterministic policy decided in under a hundred milliseconds. An A D K agent running Gemini then investigated the payee and checked the official advisories, and confirmed within seconds. It can make the decision stricter, never weaker. The desk gets the full trace, a drafted cybercrime helpline referral, and the contrast: an S M S arrives after the money has gone." |
| 7 | 2:30 to 2:50 | "On our own fifty labelled calls in six languages, including hard negatives and adversarial scams, precision and recall were one point zero, with a mean scoring time of about three seconds. It runs on Google Cloud: Gemini, A D K and Cloud Run, with a live ledger stream. Rakshak: stop the scam at the moment of payment." |

Two honesty rules for the voiceover: say "demo ledger" or add the on-screen caption "Synthetic ledger and calls (demo data)" during blocks 5 and 6, and say "our own labelled calls", not "real calls". Judges respect it, and the deck says the same.

## 7. Editing (45 minutes, any free editor)

Use CapCut, iMovie or DaVinci Resolve. Steps:

1. Import the phone recording, the laptop recording, the two PNG stills and your voiceover.
2. **Cut the phone recording into beats** and trim all waiting: remove the home-screen idle time, the typing in the pay form (jump cut), and any time the phone sits unchanged. Do not speed up Rakshak's own voice.
3. **Put the voiceover on its own track.** Lower the phone's audio to about 25% while the voiceover is speaking. Keep it at 100% during the silent gaps in blocks 3b, 3d and 5a so the caller's voice, the whisper and Rakshak's warning are heard clearly.
4. **Title card (0:00 to 0:15):** use slide 1 of the deck as a still, or a plain navy card with the headline and the three numbers.
5. **Captions (small, bottom of screen):** "Risk 85%: private whisper", "Payment paused for 30 minutes", "Priya notified", "Synthetic demo data". Add the live URL as a caption on the end card.
6. **End card (last 5 seconds):** the URL `https://rakshak-223197895518.asia-southeast1.run.app`, the GitHub repo `github.com/devaramanelohith/rakshak-agent`, and "Team Rakshak".
7. **Export:** 1080p, H.264, about 30 fps, AAC audio. Open the exported file and read the length. **It must be under 3:00.** If it is 2:58 or more, cut more.

## 8. If something goes wrong

| Problem | Fix |
|---|---|
| The recorded clip has no caller or Rakshak voice | The recorder is on microphone mode or the app audio was blocked. Switch to device audio (section 3 step 5); tap the screen once after opening the page so the browser allows sound; re-run the ten-second test. Fallback: record the phone's screen normally and also film it with a second phone or the laptop camera in a quiet room with the phone's speaker up, and use that audio. |
| Gauge stays at 0% for a few seconds | The first scoring takes about 3 seconds after each line. Wait; it updates after the first caller line. |
| Rakshak's warning starts a few seconds after the hold screen appears | The voice for that amount was not pre-generated. Run the dry run (section 3 step 7) with the same amount, or cut the gap in the edit. |
| No whisper | It plays only when the risk first passes 85%. The scripted line 3 reaches 90%. If you changed the wording, the risk may stay lower; use the script above. |
| Caller phone says "Customer's phone: NOT open on this code" | The two phones are on different session codes. Re-open both URLs with exactly the same code. |
| Payee card numbers differ from the voiceover | The ledger is live, so values move a little. The voiceover avoids exact figures on purpose; do not read numbers off the card. |
| iPhone screen recording misses the mic | Use Method A on iPhone; you do not need the microphone. |
| Anything fails near the deadline | Use the voiced replay (Method A). It depends only on the app and the recorder. |

## 9. Upload and submit (today)

1. **Upload to YouTube.** Title: "Rakshak: stop the scam at the moment of payment | AI Builder Cup 2026". Description: the live URL, the GitHub repo, "Team Rakshak, BFSI theme", and a note that data is synthetic. Audience: not made for kids. Visibility: **Public** (the brief asks for a public link; Unlisted usually works but Public removes any doubt).
2. **Test the link logged out.** Open it in a private window on a different device and watch the first 10 seconds, including audio.
3. **Submission items for the portal** (all from this package):

| Item | File or link |
|---|---|
| Deployed prototype | https://rakshak-223197895518.asia-southeast1.run.app |
| Public GitHub repository | https://github.com/devaramanelohith/rakshak-agent (tag v1.0) |
| Demo video | your public YouTube link |
| Deck as PDF | `Rakshak_Deck.pdf` (fill the team names on slides 1 and 14 first, then re-export) |
| Theme | BFSI: Intelligent Risk, Fraud and Financial Experiences |

4. **Supporting documents** to keep ready or attach if the portal allows: `Rakshak_Evaluation_Report.pdf` (the evals), `Rakshak_Judge_Pitch_and_QA.pdf` (spoken pitch and answers to likely questions), `Rakshak_Submission_Checklist.pdf` (portal steps and pre-flight checks).
5. **Submit, then screenshot the confirmation.** Do not wait for the last hour; the portal's exact cut-off time is not published. Keep Discord and portal notifications on.

## 10. Order of work if you have about three hours

| Minutes | Task |
|---|---|
| 0 to 20 | Section 3: health check, recorder setting, ten-second audio test, dry run |
| 20 to 50 | Record Method A (phone), then the fraud-desk recording and the two stills |
| 50 to 70 | Record the voiceover (read section 6 aloud twice, record the second time) |
| 70 to 115 | Edit and export (section 7); check the length |
| 115 to 135 | Upload, test logged out |
| 135 to 160 | Fill team names in the deck, re-export, submit on the portal, screenshot the confirmation |
