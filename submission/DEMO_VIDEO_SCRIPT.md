# Rakshak demo video: shot-by-shot script (2:50)

**One line:** The video is the product, the deck is the argument. A 15-second title and problem card, then the live two-phone call on the deployed Cloud Run URL, with the payment screen as the climax at the 1:00 mark and nothing after 2:50.

## 1. Decisions before the first take

**Slides first, or demo first?** A 15-second title and problem card, then the demo. The deck PDF already carries the full argument (problem, gap, architecture, evaluation, business case), so the video should not repeat it. Judges watch dozens of videos; a product that stops a scam in front of their eyes inside the first minute is what they remember. Architecture appears for 20 seconds near the end, over the fraud-desk trace, not as a slide stack at the start.

**The climax rule.** The payment screen is the climax. A live risk meter during a call is something Pixel already shows, and at least five Indian hackathon teams built one this year. What nobody shows is the moment the victim taps Pay and the bank app pauses the transfer, speaks in Hindi over the caller, shows the mule account's history and tells the daughter. The video spends 10 seconds on the risk meter and 55 seconds on the hold.

**Main take and backup take.** The main take is the live two-phone flow: phone B opens `/call?session=<id>` and rings phone A, the customer answers, a teammate speaks the scam script, the customer pays. The backup take is the scripted replay on one phone (`Test an incoming call`, `Parcel from Taiwan`, `Auto-play script`), which cannot fail on mic permission or Wi-Fi. Record both. Cut the main take into the video; keep the backup take ready as a drop-in for shots 3 to 5 if the live audio is unusable.

**Length.** Target 2:50. The organiser rule is 3 minutes; treat 3:00 as a hard ceiling and never export longer than 2:58.

**Language.** Voice-over in English. Rakshak's own voice on screen is Hindi; caption it in English. The scam script is Hindi; caption it in English.

**Recording location.** Always the deployed URL, never localhost: `https://rakshak-223197895518.asia-southeast1.run.app`. The browser address bar should be visible for at least one second in shot 2 so judges see the Cloud Run domain.

## 2. Recording setup

**Devices.**

- Phone A (the customer, Sunita Rao, demo-user): Android with Chrome or iPhone with Safari. Opens `/?session=video1&user=demo-user`. Finish the three onboarding taps before recording. Volume at maximum, phone on speaker.
- Phone B (the caller): any phone with Chrome or Safari. Opens `/call?session=video1`. The caller wears wired earphones so phone A's speaker does not feed back into phone B's microphone.
- Phone C (the trusted contact, Priya): optional third phone or a laptop tab on `/family?user=demo-user`. Its chime is the proof that the alert arrived.
- Laptop: `/desk` in Chrome at 1920x1080, browser zoom 110% so the trace is readable in the final frame.

**Network.** All devices on the same Wi-Fi or one hotspot. Run `scripts/smoke_ws.py https://rakshak-223197895518.asia-southeast1.run.app` ten minutes before recording to confirm the service is warm (MIN_INSTANCES=1) and the hold event arrives in about a second. Check `/api/health` returns `llm: true` and `live: true`.

**Quota.** Text, agents and TTS run through Vertex AI on the deployed service, so there is no daily cap on `gemini-3.8-flash`. The two Live models use the AI Studio key. Do not rehearse more than needed on a free key.

**Screen recording.**

- Phone A: the built-in screen recorder (Android: Quick Settings tile with "Record audio: media and mic"; iPhone: Control Centre screen recording with the microphone on). This captures the screen and, through the microphone, Rakshak's voice from the speaker and the caller's voice from the relay. Keep this recording as the primary audio of the hold moment.
- Laptop: QuickTime (File, New Screen Recording) or OBS for `/desk`.
- Camera: a second phone or a laptop webcam filming phone A in a hand, framed so the hold screen fills two thirds of the frame. This "over the shoulder" shot is what makes the hold feel real; the screen recording is cut in for legibility.

**Audio capture of Rakshak's voice.** Three sources, pick the cleanest in the edit: (1) the microphone track of phone A's screen recording, (2) the camera's microphone, (3) a clean copy from the service: open the case on `/desk`, copy the `spoken_text`, call `GET /api/tts?text=<spoken_text>&voice=Kore` on the laptop and save the returned audio. Use (3) under the screen recording if the room audio is noisy, keeping it synchronised to the moment the hold screen appears.

**Before each take.** Close other tabs on phone A, switch on Do Not Disturb on all phones (ringing in the demo is Rakshak's, not WhatsApp's), set phone A's language to Hindi in the profile, confirm the "Rakshak ON" pill is visible, and reset the session by using a fresh session id (`video2`, `video3`).

## 3. Shot list with timecodes and voice-over

Voice-over lines are spoken exactly as written. Captions are burned in for every line of Hindi.

| Time | Shot | On screen | Device or page | Voice-over (English) | Action |
|---|---|---|---|---|---|
| 0:00 to 0:05 | 1a Title card | Navy card: "Rakshak. Stop the scam at the moment of payment." Team Rakshak, BFSI, the Cloud Run URL | Deck slide 1 exported as PNG | "This is Rakshak, a guardian agent that lives inside a bank app." | none |
| 0:05 to 0:15 | 1b Problem card | Three numbers: 81.8% of Singapore's 2025 scam cases were self-effected transfers; India lost at least 22,495 crore rupees in 2025 with about 24% recovered; 123,672 digital-arrest cases in 2024 | Deck slide 2 exported as PNG | "In most scams today the victim makes the transfer themselves, while the scammer is still on the line. An alert after the debit is too late: the mule account is empty within hours." | none |
| 0:15 to 0:25 | 2 The customer's phone | Phone A home screen: balance, "Rakshak ON" pill, session id under Demo controls; the address bar with the run.app domain visible for one second | Phone A, `/` | "Sunita is 67, speaks Hindi, and has switched Guardian mode on. Her daughter Priya is her trusted contact." | Scroll once to show the profile card |
| 0:25 to 0:35 | 3 The call comes in | Phone B taps Call; phone A rings with the incoming-call sheet; the judge taps Answer; the "Rakshak listening" pill appears | Phone B `/call`, then phone A | "A call comes in. Rakshak starts listening from the first ring." | Phone B: Call. Phone A: Answer, allow the microphone |
| 0:35 to 0:55 | 4 The scam unfolds | Live transcript on phone A labelled caller and user; signal chips light up (authority, threat, secrecy, safe account); risk gauge climbs; reasons in Hindi | Phone A call screen | "The caller claims to be a CBI inspector. A parcel with drugs, an arrest warrant, do not tell anyone. Rakshak transcribes each speaker on its own Gemini Live session and scores the coercion after every sentence, in Hindi." | Teammate on phone B reads script_01 lines 1 to 4 in Hindi (or taps Say) |
| 0:55 to 1:00 | 5 The whisper | The private whisper banner and the short Hindi whisper audible from phone A; phone B hears nothing | Phone A | "At 85 percent risk, Rakshak whispers to Sunita only. The caller never hears it." | Pause the script for two seconds |
| 1:00 to 1:08 | 6 The demand | Caller says: transfer two lakh to the RBI safe account now. Toast: "the caller is demanding payment". Judge taps Open UPI pay; VPA and amount are pre-filled | Phone A pay screen | "Then the demand: two lakh rupees, now, to a safe account. Sunita opens UPI pay." | Teammate reads the payment_demand line; judge taps Open UPI pay |
| 1:08 to 1:12 | 7 Pay | Finger on Pay. Hold the camera here. | Camera on phone A, cut to screen recording | (silence) | Tap Pay |
| 1:12 to 1:40 | 8 The hold (climax) | Within a second: red HOLD screen, 30:00 countdown, Rakshak speaks in Hindi over the ducked caller; payee card: critical band, 12 payers in 48 hours, 96 percent cashed out in 7 days, 4 complaints on 1930; "Priya (daughter) has been notified"; phone C chimes | Phone A hold screen, cut-in of phone C | No voice-over while Rakshak speaks. Caption the Hindi. Then: "In under a hundred milliseconds the bank's own policy fused the call risk with the payee's mule risk and paused the transfer. The screen changed first, the voice followed." | Let the clip play; do not touch the phone |
| 1:40 to 1:55 | 9 The agent confirms | Event log on phone A: "agent_running" then "decided_by adk_agent, confirmed", agent reasons in Hindi; cut to `/desk` showing the same case appearing | Phone A event log, laptop `/desk` | "Fifteen seconds later the ADK agent lands: it looked up the payee, checked the claimed authority against official advisories, and confirmed the hold with evidence. It can make the decision stricter, never looser." | Laptop: click the case |
| 1:55 to 2:10 | 10 The exits | Judge taps "I know this person, pay anyway": the typed-amount dialog appears; cancel. Taps "Talk to Rakshak" and asks "why did you stop this?"; Rakshak answers by voice | Phone A | "Sunita keeps control. She can override by typing the exact amount, or ask Rakshak why. A hold is a pause, not a block, and it expires on its own in thirty minutes." | Open and cancel the override; one voice question |
| 2:10 to 2:30 | 11 The fraud desk | `/desk`: policy versus agent decision, the ADK trace with the two tool calls and the advisory source, the payee lineage record, the narrative and the drafted 1930 referral; the "SMS alert versus Rakshak" panel | Laptop `/desk` | "Every case is auditable: the deterministic policy, the agent's trace, where the payee numbers came from, and a referral to the 1930 helpline drafted by Gemini." | Scroll the case slowly |
| 2:30 to 2:42 | 12 Architecture and evaluation | Deck slide 6 (architecture) for 7 seconds, then deck slide 10 (evaluation) for 5 seconds | PNG exports | "Five Gemini models, Google ADK 2.11 and Cloud Run. On fifty labelled calls in six languages, including ten written to fool the rubric, precision and recall are one point zero." | none |
| 2:42 to 2:50 | 13 Close | Deck slide 14: URL, repo, "try it as a judge in 60 seconds" | PNG export | "Rakshak. Deployed on Cloud Run, open source, ready to try at the link on screen." | none |

Total: 2:50. If the edit runs long, shorten shot 11 first (to 12 seconds), then shot 4 (to 15 seconds). Never cut shot 8.

## 4. Takes to record

Record in this order; each take on a fresh session id.

1. **Take A1, main take, full run.** Phone A screen recording + camera + laptop `/desk` recording, all started before phone B taps Call. Run shots 3 to 11 without stopping. Keep going even if something is slow; the edit can cut.
2. **Take A2, main take, second run.** Same as A1. Two full runs give two chances at a clean hold moment with good audio.
3. **Take B, backup take, scripted replay.** Phone A only: `Test an incoming call`, `Parcel from Taiwan`, `Auto-play script`, Open UPI pay at the toast, Pay. Screen recording with microphone on. This covers shots 4 to 9 if the live audio from A1 and A2 is unusable.
4. **Take C, hold moment close-up.** Camera only, phone A in hand, start recording two lines before the payment demand, tap Pay, hold still for 25 seconds. Use for shot 7 and the first seconds of shot 8.
5. **Take D, exits.** Phone A on an existing held case: override dialog opened and cancelled; "Talk to Rakshak" with one question and the voice answer. Record twice.
6. **Take E, fraud desk.** Laptop recording of `/desk` on the case from A1 or A2: slow scroll through policy versus agent, trace, lineage, narrative, referral, the SMS comparison panel. Record at 1920x1080.
7. **Take F, family phone.** Phone C on `/family?user=demo-user` while A1 runs; two seconds of the chime and the alert card.
8. **Take G, benign hard negative (optional, 10 seconds).** Replay "Benign hard negative: daughter's hostel fee" and pay: "Payment sent". Use only if there is time left in shot 10 to say "and when the call is a daughter asking for fees, the payment simply goes through."
9. **Voice-over.** Record all lines in one sitting, in a quiet room, phone or USB microphone 15 cm from the mouth, each line twice. Read at a steady pace; the timings above assume about 150 words per minute.

Title, problem, architecture, evaluation and closing cards: export deck slides 1, 2, 6, 10 and 14 from `submission/Rakshak_Deck.pdf` as PNG at 1920x1080.

## 5. Editing notes

- **Timeline.** 1920x1080, 30 fps. Phone recordings are portrait: place them centred on a navy (#0b1f3a) background, scaled to full height, with the laptop or camera footage filling the frame where the table says so. Never stretch a phone recording.
- **Cuts.** Hard cuts only, no transitions except a 10-frame fade in at 0:00 and out at 2:50. Cut on action: the tap on Pay is the cut between the camera shot and the screen recording.
- **The hold moment.** Keep shot 8 as one unbroken screen recording from the Pay tap to the end of Rakshak's sentence. Do not speed it up. Duck the voice-over fully while Rakshak speaks.
- **Captions.** Burn in English captions for every Hindi line (caller, whisper, hold voice, agent message) in white on a semi-transparent navy bar at the bottom, 42 px sans-serif. Keep each caption under 12 words. Caption the voice-over too, for judges watching without sound.
- **Labels.** A small corner label on every shot: "Customer phone", "Caller phone", "Family phone", "Fraud desk". A persistent 24 px label bottom-right from 0:15 to 2:30: "Live on Cloud Run: rakshak-223197895518.asia-southeast1.run.app".
- **Audio.** Voice-over at -16 LUFS, Rakshak's voice and the caller at -20 LUFS, no music under the hold moment. A quiet bed under shots 1, 12 and 13 only, if at all.
- **Timing checks.** The hold screen must appear on the timeline within 1.5 seconds of the Pay tap; if the take was slower, trim the gap. The agent confirmation at 1:40 may be time-compressed with a visible "15 s later" label.
- **Honesty.** Nothing on screen may be mocked up. If a take shows a slow TTS (voice after the screen), keep it; the screen-before-voice ordering is the design.
- **Length.** Hard rule: under 3:00. Export at 2:50; check the exported file's duration before uploading.
- **Export and upload.** H.264, 1080p, 10 Mbps. Upload to YouTube as Public (or Unlisted only if the portal accepts it; the brief says public). Title: "Rakshak: stop the scam at the moment of payment (Google Cloud AI Builder Cup 2026)". Description: one paragraph, the live URL and the repo. Test the link from a private browser window and from a phone before putting it on the portal.
