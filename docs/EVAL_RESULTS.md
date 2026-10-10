# Rakshak evaluation (gemini-3.5-flash)

n=30 calls, hold threshold 0.7

| metric | value |
|---|---|
| precision (scam detection at payment moment) | 1.0 |
| recall | 1.0 |
| F1 | 1.0 |
| signal accuracy (8 signals x calls) | 0.946 |
| payment decision accuracy (fusion policy) | 1.0 |
| mean rubric latency | 2381 ms |

| id | label | lang | risk | pred type | action | payee band |
|---|---|---|---|---|---|---|
| call_001 | scam | hi | 0.98 | digital_arrest | hold_and_alert | critical |
| call_002 | scam | hi | 1.00 | digital_arrest | hold_and_alert | critical |
| call_003 | scam | hinglish | 1.00 | digital_arrest | hold_and_alert | critical |
| call_004 | scam | hinglish | 0.98 | digital_arrest | hold_and_alert | high |
| call_005 | scam | en | 1.00 | digital_arrest | hold_and_alert | critical |
| call_006 | scam | hi | 0.95 | investment | hold_and_alert | critical |
| call_007 | scam | hinglish | 0.90 | investment | hold_and_alert | high |
| call_008 | scam | en | 0.90 | investment | hold_and_alert | critical |
| call_009 | scam | hinglish | 0.85 | job_task | hold_and_alert | medium |
| call_010 | scam | en | 0.90 | job_task | hold_and_alert | critical |
| call_011 | scam | hi | 1.00 | kyc_otp | hold_and_alert | critical |
| call_012 | scam | hinglish | 0.98 | kyc_otp | hold_and_alert | high |
| call_013 | scam | hi | 0.95 | lottery | hold_and_alert | critical |
| call_014 | scam | hinglish | 0.85 | family_emergency | hold_and_alert | high |
| call_015 | scam | en-sg | 1.00 | sg_official_impersonation | hold_and_alert | critical |
| call_016 | benign | hi | 0.00 | none | - | - |
| call_017 | benign | hi | 0.00 | none | proceed | low |
| call_018 | benign | hi | 0.00 | none | - | - |
| call_019 | benign | hi | 0.00 | none | - | - |
| call_020 | benign | hi | 0.10 | none | proceed | low |
| call_021 | benign | hinglish | 0.05 | none | proceed | low |
| call_022 | benign | hinglish | 0.05 | none | - | - |
| call_023 | benign | hinglish | 0.05 | none | proceed | medium |
| call_024 | benign | hinglish | 0.00 | none | - | - |
| call_025 | benign | en | 0.00 | none | proceed | low |
| call_026 | benign | en | 0.00 | none | - | - |
| call_027 | benign | en | 0.00 | none | - | - |
| call_028 | benign | en-sg | 0.05 | none | - | - |
| call_029 | benign | en-sg | 0.00 | none | proceed | low |
| call_030 | benign | en | 0.00 | none | - | - |
