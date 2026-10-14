# Rakshak evaluation (gemini-3.5-flash)

n=50 calls, hold threshold 0.7

| metric | value |
|---|---|
| precision (scam detection at payment moment) | 1.0 |
| recall | 1.0 |
| F1 | 1.0 |
| signal accuracy (8 signals x calls) | 0.932 |
| payment decision accuracy (fusion policy) | 0.974 |
| mean rubric latency | 5294 ms |

| id | label | lang | risk | pred type | action | payee band |
|---|---|---|---|---|---|---|
| call_001 | scam | hi | 0.98 | digital_arrest | hold_and_alert | critical |
| call_002 | scam | hi | 1.00 | digital_arrest | hold_and_alert | critical |
| call_003 | scam | hinglish | 1.00 | digital_arrest | hold_and_alert | critical |
| call_004 | scam | hinglish | 0.95 | digital_arrest | hold_and_alert | critical |
| call_005 | scam | en | 1.00 | digital_arrest | hold_and_alert | critical |
| call_006 | scam | hi | 0.95 | investment | hold_and_alert | high |
| call_007 | scam | hinglish | 0.95 | investment | hold_and_alert | high |
| call_008 | scam | en | 0.80 | investment | hold_and_alert | critical |
| call_009 | scam | hinglish | 0.85 | job_task | warn | low |
| call_010 | scam | en | 0.90 | job_task | hold_and_alert | high |
| call_011 | scam | hi | 0.95 | kyc_otp | hold_and_alert | critical |
| call_012 | scam | hinglish | 0.95 | kyc_otp | hold_and_alert | critical |
| call_013 | scam | hi | 0.95 | lottery | hold_and_alert | high |
| call_014 | scam | hinglish | 0.95 | family_emergency | hold_and_alert | critical |
| call_015 | scam | en-sg | 1.00 | sg_official_impersonation | hold_and_alert | critical |
| call_016 | benign | hi | 0.00 | none | - | - |
| call_017 | benign | hi | 0.00 | none | proceed | low |
| call_018 | benign | hi | 0.00 | none | - | - |
| call_019 | benign | hi | 0.00 | none | - | - |
| call_020 | benign | hi | 0.10 | none | proceed | low |
| call_021 | benign | hinglish | 0.00 | none | proceed | low |
| call_022 | benign | hinglish | 0.10 | none | - | - |
| call_023 | benign | hinglish | 0.00 | none | proceed | low |
| call_024 | benign | hinglish | 0.00 | none | - | - |
| call_025 | benign | en | 0.00 | none | proceed | low |
| call_026 | benign | en | 0.05 | none | - | - |
| call_027 | benign | en | 0.00 | none | - | - |
| call_028 | benign | en-sg | 0.05 | none | - | - |
| call_029 | benign | en-sg | 0.00 | none | proceed | low |
| call_030 | benign | en | 0.00 | none | - | - |
| call_031 | benign | en | 0.05 | none | - | - |
| call_032 | benign | hi | 0.00 | none | - | - |
| call_033 | benign | hinglish | 0.10 | none | proceed | low |
| call_034 | benign | kn | 0.10 | none | proceed | low |
| call_035 | benign | hi | 0.05 | none | proceed | low |
| call_036 | benign | hinglish | 0.05 | none | proceed | low |
| call_037 | benign | ta | 0.05 | none | proceed | low |
| call_038 | benign | hinglish | 0.05 | none | proceed | low |
| call_039 | benign | en | 0.00 | none | proceed | low |
| call_040 | benign | en | 0.00 | none | proceed | low |
| call_041 | scam | hi | 0.98 | digital_arrest | hold_and_alert | critical |
| call_042 | scam | hinglish | 0.85 | family_emergency | hold_and_alert | critical |
| call_043 | scam | en | 0.90 | investment | hold_and_alert | high |
| call_044 | scam | hi | 0.85 | other | hold_and_alert | high |
| call_045 | scam | hinglish | 0.75 | job_task | hold_and_alert | critical |
| call_046 | scam | hi | 0.95 | kyc_otp | hold_and_alert | critical |
| call_047 | scam | kn | 0.90 | loan_app | hold_and_alert | high |
| call_048 | scam | ta | 0.85 | lottery | hold_and_alert | high |
| call_049 | scam | en-sg | 0.95 | sg_official_impersonation | hold_and_alert | critical |
| call_050 | scam | en | 0.95 | kyc_otp | hold_and_alert | critical |
