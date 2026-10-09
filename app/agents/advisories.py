"""Official advisory knowledge used by the authority check. Deterministic and instant; Search grounding is
only consulted for organisations not covered here. Sources are official portals the bank can cite."""
from __future__ import annotations

ADVISORIES: list[dict] = [
    {
        "keys": ["cbi", "police", "crime branch", "narcotics", "ncb", "enforcement directorate", " ed ", "customs", "cyber cell", "cybercrime", "trai", "telecom", "dot ", "court", "judge", "fedex", "courier", "parcel"],
        "entity": "Indian law-enforcement / regulators (CBI, police, ED, NCB, customs, TRAI, courts)",
        "verdict": "never_done_by_this_entity",
        "explanation": "No Indian agency performs a 'digital arrest', investigates over a video call, or asks a citizen to move money to a 'safe' / 'RBI' / 'verification' account. The Ministry of Home Affairs' I4C and PIB fact-checks state this explicitly; genuine notices arrive in writing, not by demanding an immediate UPI transfer.",
        "sources": [
            {"title": "I4C / National Cybercrime Reporting Portal (1930)", "uri": "https://cybercrime.gov.in/"},
            {"title": "PIB Fact Check", "uri": "https://factcheck.pib.gov.in/"},
            {"title": "Sanchar Saathi (DoT) - report suspected fraud communication", "uri": "https://sancharsaathi.gov.in/"},
        ],
    },
    {
        "keys": ["rbi", "reserve bank"],
        "entity": "Reserve Bank of India",
        "verdict": "never_done_by_this_entity",
        "explanation": "The RBI does not hold customer accounts, never calls individuals about their money, and never asks for transfers, OTPs or card details ('RBI Kehta Hai' public-awareness campaign).",
        "sources": [{"title": "RBI Kehta Hai - public awareness", "uri": "https://rbikehtahai.rbi.org.in/"}, {"title": "Reserve Bank of India", "uri": "https://www.rbi.org.in/"}],
    },
    {
        "keys": ["mas", "monetary authority", "singapore police", "spf", "ministry of manpower", "mom", "ica", "immigration", "cpib", "govt officer", "government officer", "dbs", "ocbc", "uob"],
        "entity": "Singapore government agencies and banks",
        "verdict": "never_done_by_this_entity",
        "explanation": "Singapore government officials and police never ask for money transfers, PayNow payments or bank credentials over a call; the national ScamShield programme and SPF advisories say to hang up and call 1799.",
        "sources": [{"title": "ScamShield (Singapore)", "uri": "https://www.scamshield.gov.sg/"}, {"title": "Singapore Police Force advisories", "uri": "https://www.police.gov.sg/Advisories"}, {"title": "Monetary Authority of Singapore", "uri": "https://www.mas.gov.sg/"}],
    },
    {
        "keys": ["sebi", "adviser", "advisor", "investment", "trading", "stock tips", "vip group", "crypto"],
        "entity": "Investment advisers / SEBI",
        "verdict": "never_done_by_this_entity",
        "explanation": "SEBI-registered intermediaries cannot guarantee returns, do not run 'VIP tip' groups, and never ask investors to pay a 'tax' or 'fee' to withdraw profits. Registration can be verified on SEBI's intermediary portal.",
        "sources": [{"title": "SEBI investor portal", "uri": "https://investor.sebi.gov.in/"}, {"title": "SEBI - recognised intermediaries", "uri": "https://www.sebi.gov.in/"}],
    },
    {
        "keys": ["bank", "kyc", "customer care", "card", "loan", "insurance", "paytm", "phonepe", "gpay", "npci", "upi"],
        "entity": "Banks, card networks, UPI apps",
        "verdict": "never_done_by_this_entity",
        "explanation": "Banks and UPI apps never ask for OTPs, PINs, passwords or 'KYC update' payments on a call, and KYC is never completed by sending money. Entering a UPI PIN only ever sends money, never receives it.",
        "sources": [{"title": "RBI Kehta Hai", "uri": "https://rbikehtahai.rbi.org.in/"}, {"title": "NPCI UPI safety", "uri": "https://www.npci.org.in/"}],
    },
]


def lookup_advisory(claimed_organisation: str, claimed_role: str = "", asked_for: str = "") -> dict | None:
    hay = f" {claimed_organisation} {claimed_role} {asked_for} ".lower()
    for adv in ADVISORIES:
        if any(k in hay for k in adv["keys"]):
            return {"verdict": adv["verdict"], "entity": adv["entity"], "explanation": adv["explanation"], "sources": adv["sources"], "source": "official_advisory_table"}
    return None
