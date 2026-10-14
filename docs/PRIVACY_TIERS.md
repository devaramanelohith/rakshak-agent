# Privacy tiers and data lineage

Two objections come up in every conversation about Rakshak: "a bank cannot listen to my calls" and "where does the
payee risk data come from". This page is the answer we give, and it is what the product implements or is designed for.

## 1. Call audio: the customer chooses the tier, the product works at every tier

| Tier | What Rakshak uses | What leaves the phone | Permission needed | Status |
|---|---|---|---|---|
| **0: no audio** | Call in progress from an unsaved number + the customer opening the pay screen + payee risk + profile | Nothing about the call; only the payment request | Phone-state (Android) or nothing (in-app) | Design; the fusion policy already runs with call_risk = 0 |
| **1: on-device transcript, opt-in** | A rolling 60-second transcript kept on the device and discarded continuously; only when a payment is attempted during the call are the rubric scores and the last window sent | Rubric scores + last 60 s of text at the payment moment only | Microphone, explicit Guardian opt-in, visible indicator | Design; needs an OS/OEM audio channel (Pixel-class on-device models) |
| **2: cloud analysis through a lawful channel** | Live transcription and rubric in the cloud for in-app calls, telco-forked audio, or OS-vendor feeds | Audio stream (not retained), transcript on the case | Guardian opt-in; the channel's own consent (in-app call notice, telco consent) | Implemented (this prototype) |

Rules that hold at every tier:

- Guardian mode is off until the customer switches it on, and a persistent indicator shows when Rakshak is listening.
- Raw audio is never written to disk (`RAKSHAK_RETAIN_AUDIO` defaults to false). Transcripts are kept only on a case the customer can see, for the bank's audit trail.
- The caller never hears Rakshak's whisper; the barge-in is to the customer's own device.
- The customer always keeps the override (typed amount), and holds expire on their own after 30 minutes.
- Family guardian (a daughter enabling it for a parent) follows the same opt-in flow, on the parent's device, with the parent present. This mirrors Truecaller's Family Protection and Pixel Scam Detection, both of which are off by default and are switched on by users who want protection.

Why the tiers matter: no third-party app can tap a cellular call on Android or iOS, so Tier 2 only exists where audio is lawfully available (the bank's own in-app calls, a telco partner as in FICO Scam Signal with Jersey Telecom, or the OS vendor). Google is the one company that can wire Pixel's on-device detection to a payment hold inside GPay; Rakshak is the bank-side half of that pairing.

Legal basis is a counsel question. One-party consent is the norm in India and Singapore, fraud prevention is a recognised purpose, and the bank acts as data fiduciary under the DPDP Act; we state that on the security slide and claim nothing more.

## 2. Payee risk: ledger-derived features with lineage

The mule-risk features are the payment provider's own ledger, not the customer's data. The customer grants nothing new, because the question is about the recipient.

| Feature | Meaning | Source in production | Source in this prototype |
|---|---|---|---|
| fan_in_48h | distinct payers in the last 48 h | bank/PSP ledger | simulated ledger stream (`app/ledger.py`) |
| cash_out_ratio_7d | share of this week's inflow moved out | ledger | simulated ledger |
| dormant_days_before_burst | silence before sudden activity | ledger history | simulated ledger |
| account_age_days | age of the VPA | ledger / KYC | simulated ledger |
| fri_level | DoT Financial Risk Indicator for the linked mobile | DoT FRI feed (already live inside UPI apps) | static demo value |
| linked_complaints_1930 | complaints naming this payee | I4C Suspect Registry via the bank | static demo value |
| kyc_tier | min or full KYC | bank KYC | static demo value |

The score and band are computed with one formula, in `sql/payee_risk.sql` for BigQuery and in `app/ledger.py` for the stream: 0.30 x (fan_in >= 8) + 0.20 x (cash-out >= 0.8) + 0.15 x (dormant >= 30 days) + 0.15 x (FRI high) + 0.15 x (complaints > 0) + 0.05 x (age < 30 days). Many payers alone is normal for a shop or a hospital; it is the combination with cash-out, dormancy, a new account or registry hits that marks a mule.

Every payee card carries a lineage record: where the features came from (`simulated_ledger`, `bigquery` or `demo_risk_table`), how many transactions were in the window, when they were computed, which fields are registry values, and which sinks (Pub/Sub, BigQuery) the stream is mirrored to. The fraud desk shows it; RBI's FREE-AI survey found most regulated entities lack exactly this lineage.

Production path: set `BIGQUERY_LEDGER_TABLE` to stream the transactions into BigQuery, run `sql/payee_risk.sql` as a scheduled query, and set `BIGQUERY_PAYEE_TABLE` so lookups read the scored table. `scripts/load_bigquery.py` and the public PaySim / IBM AMLSim datasets give a realistic ledger without a bank partner.
