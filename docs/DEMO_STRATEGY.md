# Demo strategy: how Rakshak "hears" a call, and how to run it live in Singapore

## 1. The honest answer about live call audio

**No third-party app can listen to a normal cellular phone call on a modern phone.**

- Android removed call-audio access for apps in Android 10 (2019). The only call recording that still works is the
  OEM's own dialer (Pixel, Samsung, Xiaomi), and the Play Store bans the accessibility-service workaround since 2022.
- iOS has never allowed it. iOS 26 call screening happens before pickup and gives apps nothing.
- Google's own Scam Detection runs *inside the Pixel phone app* with Gemini Nano precisely because only the OS vendor
  can touch that audio stream.

So a bank app cannot tap the cellular call. That is not a weakness of Rakshak, it is the reason Rakshak lives on the
**bank/telco side** and why the pitch says "Pixel can hear the call, FRI knows the payee, nothing joins them when the
money moves". There are three legitimate channels through which the bank side receives call audio, and the
prototype implements all three:

| Channel | Who provides the audio | Real-world precedent | In the prototype |
|---|---|---|---|
| **In-app call** (the bank app has its own VoIP calling, like "secure call" features in DBS/HDFC apps) | the bank's own app | banks already route "verified calls" through their apps | `/ws/call/{session}/{role}` WebSocket audio; victim device + caller device |
| **Telco media stream** (the carrier forks the call audio to the bank with consent) | the telecom operator | FICO Scam Signal with Jersey Telecom / Barclays (call-state today) | Twilio Media Streams bridge: `/twilio/voice` + `/ws/twilio/{session}` |
| **OS vendor hook** (Pixel Scam Detection feeding a bank API) | Google / OEM | none yet; this is the integration Rakshak proposes | out of scope; described on the roadmap slide |

Consent is explicit either way: the customer switches on "Guardian mode" in the app (opt-in, visible indicator), the
caller's audio is transcribed and not retained (`RAKSHAK_RETAIN_AUDIO=false`), and the transcript is kept only on a
case the customer can see.

## 2. Four demo layers (always have a lower layer ready)

| Layer | What happens | Needs | Fails how | Use it for |
|---|---|---|---|---|
| **L0 Transcript replay** | script lines are posted as text turns; rubric, fusion, hold, TTS all run for real | server + API key | practically never | video B-roll, eval, judge curl test |
| **L1 Voiced replay** | same as L0 but every caller line is voiced by Gemini TTS on the victim phone (cached) | speakers | TTS quota | **the 3-minute video**; a judge pressing one button |
| **L2 Two-device live call** | teammate on the caller console speaks into a mic; victim phone hears them; Gemini transcribe-live + rubric run on real speech; judge pays | two devices on the same server, mics, decent Wi-Fi | mic permission, network | **the Singapore stage demo** |
| **L3 Real phone number** | judge dials a real Twilio number from their own phone; Twilio dials the "scammer" phone and streams both legs to the server | Twilio number + public URL (Cloud Run) | telco/network, Twilio credit | the "wow" moment if L2 is stable; otherwise skip |

The product story is identical at every layer; only the audio source changes. Never go on stage with only L2/L3.

## 3. Exactly how the Singapore stage demo runs (L2): three phones, one call

**Primary script.** `script_03` "Cyber Crime Branch money-laundering case (English)" with the default customer `demo-user` (Lohith, English, trusted contact Priya (sister)). The competition is JAPAC-wide, so the headline run is in English end to end: the caller, the whisper, the hold voice and the reasons. The optional second run is the Hindi persona `demo-user-hi` (Sunita Rao, 60+, trusted contact Priya (daughter)) with `script_01` "Parcel from Taiwan"; use it only if time allows, to show the vernacular path.

**Pages.** Customer phone: `/?session=<id>&user=demo-user` (Lohith's bank app; `&user=demo-user-hi` switches to the Hindi persona). Caller phone: `/call?session=<id>` (a phone-style dialer: Call, mute, hang up, plus a script prompter). Family phone: `/family?user=demo-user` (Priya's phone; alerts arrive with a chime). Projector: `/desk`. The session id is under "Demo controls" on the customer phone, and the caller/family links there carry it.

**Flow.** The caller taps Call: the customer's phone rings (sheet with the number, Answer / Decline, ring tone and vibration). The judge answers; the mic switches on automatically and both parties hear each other through the relay. The teammate speaks `script_03` from the prompter (or taps "Say" lines if they prefer not to speak): "This is the Cyber Crime Branch, Mumbai", the non-bailable warrant, digital arrest, the PMLA secrecy line, the "Police Verification app". Transcript, gauge and English reasons update live; the whisper fires privately at 85% ("Rakshak here: careful. This call looks like a scam."). At the payment demand ("The ID is police.hq.escrow@rakshakdemo. Transfer five lakh forty thousand now, while I watch.") the judge opens Pay, the fields are pre-filled (`police.hq.escrow@rakshakdemo`, Rs 5,40,000), taps Pay, and the hold fires: the hold screen, Rakshak's English barge-in ("Please stop. I am Rakshak, your bank's safety assistant. No police, CBI or RBI officer ever asks for money over UPI..."), the payee card (high band, 5 payers in 48 h, 99% cashed out, 2 helpline complaints), and "Priya (sister) has been notified"; Priya's phone chimes with the alert at the same moment.

**Audio hygiene.** Both phones on the same Wi-Fi or hotspot; the caller wears earphones (otherwise the customer phone's speaker feeds back into the caller mic); the customer phone on speaker so the room hears Rakshak's barge-in. Chrome on Android or Safari on iOS; grant the microphone on first use (HTTPS, so the Cloud Run URL works; a laptop hotspot plus a local server needs `--ssl` or the scripted "Say" path).

### Legacy wording (operator console)


**Devices.** Phone A (victim) opens `https://<cloud-run-url>/?user=demo-user` (Lohith, English) in Chrome. Laptop B (caller) opens
`/scammer?session=<id>` (the session id is printed on Phone A's home screen). A third screen (projector) shows
`/desk`. Phone A on speaker is fine; the WebSocket relay has echo cancellation enabled in the mic constraints.

**Script (2 min 40 s).**

1. Phone A: Guardian mode is on (pill visible). Tap *Simulate incoming call*. Tap *Use my mic*. The judge holds Phone A.
2. Laptop B: teammate reads `script_03` ("Cyber Crime Branch", English) into the laptop mic. Phone A plays their
   voice; the live transcript appears; the risk meter climbs; reasons appear in English. At ~85% Rakshak **whispers**
   to the victim only (the "caller" does not hear it). Optional second run: `?user=demo-user-hi` with `script_01`
   ("Parcel from Taiwan", Hindi) or `?user=demo-user-en` with `script_04` (Singapore "MAS officer", PayNow).
3. On the line marked `payment_demand`, the judge taps *Open UPI pay*. The VPA and amount are pre-filled if a script
   is running, or the teammate reads them out. The judge taps *Pay*.
4. **Climax (keep the camera here).** Within ~1 s: the hold screen, the English voice barge-in, the 30:00
   countdown, the payee mule-risk card (`police.hq.escrow@rakshakdemo`: 5 payers in 48 h, 99% cashed out, 2 helpline
   complaints), and "Priya (sister) has been notified". A few seconds later the ADK trace lands on the fraud desk (investigator tool
   calls, authority check with its advisory source, decision agent, narrative, 1930 referral).
5. Show the override: tap *I know this person*, the app asks to type the amount, cancel. Then tap *Talk to Rakshak*
   and ask "why did you stop this?"; Rakshak answers by voice (Gemini Live) and can offer to call Priya.
6. Switch to `/desk`: the case, the trace, the "SMS alert vs Rakshak" comparison, the eval table.

**If the mic path misbehaves on stage:** on Laptop B click the script lines' *Say* buttons instead of speaking (L1).
The victim phone still hears a voice, the transcript and rubric still run; only the ASR step is skipped. If the
network dies, Phone A can run against a laptop hotspot and a local server (`uv run uvicorn app.main:app`), which is
why the repo runs with zero Google Cloud data services configured.

## 4. How to run L3 (judge calls a real number)

1. Buy a Twilio number (a US number works from Singapore; an SG number needs a regulatory bundle).
2. Deploy to Cloud Run (public URL) or expose a local server with ngrok; set `PUBLIC_BASE_URL`.
3. Set the number's Voice webhook to `POST https://<url>/twilio/voice?session=phone`.
4. Set `TWILIO_DIAL_NUMBER=+91...` (the teammate's phone, playing the scammer).
5. Open `/?session=phone` on the victim phone (same session id). The judge dials the Twilio number from their own
   phone; Twilio connects them to the teammate and streams both legs to Rakshak. The app shows the live risk; when the
   judge opens Pay, the same hold flow fires.

Cost: Twilio trial credit covers a demo; production would use the bank's telco partner, not Twilio.

## 5. What to record for the 3-minute video

Record L1 (voiced replay) on a phone screen-recorder, with the fraud desk on a second recording, and cut:

| Time | Shot |
|---|---|
| 0:00-0:20 | one slide: 81.8% of Singapore scam losses are self-authorised; India lost ₹22,495 crore in 2025; alerts after the transfer are too late |
| 0:20-0:50 | Phone: Guardian on, scripted Cyber Crime Branch call (English) plays, meter climbs, English reasons, whisper |
| 0:50-1:40 | **Payment screen**: Pay → barge-in voice → hold + payee card + Priya (sister) notified → override dialog (not used) |
| 1:40-2:20 | Fraud desk: ADK trace, advisory source, narrative, 1930 referral, SMS-vs-Rakshak |
| 2:20-2:50 | Architecture slide, eval table, Live Q&A clip |
| 2:50-2:58 | "Deployed on Cloud Run; Gemini 3.8 / 3.5, ADK 2.11; repo link" |

Keep it under 3:00 by the rules; aim for 2:55.

## 6. Quota warning (learned the hard way on 10 Oct)

The free AI Studio tier caps `gemini-3.8-flash` at **20 requests per day** per project, and the other 3.x models at
similarly small daily numbers. One rehearsal burns that. Before the video and before Singapore, either enable
billing on the AI Studio project (pay-as-you-go; a full demo costs a few rupees) or switch to the Agent Platform
endpoints with the $300 trial (`GOOGLE_GENAI_USE_VERTEXAI=true`). Keep the keyword stub (`RAKSHAK_FAKE_LLM=1`) as the
absolute last resort: the flow still works, only the reasons become generic.
