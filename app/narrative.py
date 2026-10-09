"""Fraud-desk narrative + 1930 / ASCom referral text. In production the same prompt runs as
BigQuery `AI.GENERATE` over the cases table (sql/narrative_ai_generate.sql)."""
from __future__ import annotations

import json
import logging

from .config import settings
from .llm import generate_json

log = logging.getLogger("rakshak.narrative")

SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {"type": "string", "description": "4-6 sentence incident narrative for the bank's fraud desk, past tense, factual"},
        "referral_text": {"type": "string", "description": "text the bank files with the 1930 cybercrime helpline / ASCom, including payee, amount, timestamps, signals"},
        "evidence_points": {"type": "array", "items": {"type": "string"}},
        "recommended_bank_actions": {"type": "array", "items": {"type": "string"}},
        "customer_followup_user_language": {"type": "string", "description": "2 sentences to send the customer in their language"},
    },
    "required": ["narrative", "referral_text", "evidence_points", "recommended_bank_actions", "customer_followup_user_language"],
}

SYSTEM = "You write concise, auditable fraud-desk records for an Indian/Singapore bank. Never invent facts not in the input. Use the customer's language for the follow-up."


def _stub(case: dict) -> dict:
    p, r, d = case["payment"], case["rubric"], case["decision"]
    return {
        "narrative": f"Customer attempted ₹{p['amount_inr']:,.0f} to {p['vpa']} during a live call scored {r.get('risk_score')} ({r.get('scam_type')}). Rakshak took action '{d.get('action')}'.",
        "referral_text": f"Payee {p['vpa']} ({case['payee'].get('risk_band')} band). Signals: {', '.join(k for k, v in r.get('signals', {}).items() if v)}.",
        "evidence_points": d.get("reasons", []),
        "recommended_bank_actions": ["Review payee for freeze", "Call customer", "File 1930 referral"],
        "customer_followup_user_language": "We paused a suspicious payment. Our team will call you.",
    }


async def generate_case_narrative(case: dict) -> dict:
    if not settings.llm_enabled():
        return _stub(case)
    slim = {
        "case_id": case["case_id"],
        "created_at": case.get("created_at"),
        "customer": {k: case["profile"].get(k) for k in ("name", "age_band", "language")},
        "payment": case["payment"],
        "call_rubric": {k: case["rubric"].get(k) for k in ("scam_type", "stage", "signals", "risk_score", "reasons", "summary")},
        "transcript_excerpt": case.get("transcript_excerpt", ""),
        "payee_risk": {k: case["payee"].get(k) for k in ("vpa", "risk_band", "mule_risk_score", "fan_in_48h", "cash_out_ratio_7d", "dormant_days_before_burst", "fri_level", "linked_complaints_1930", "reasons")},
        "decision": case["decision"],
        "status": case.get("status"),
    }
    try:
        return await generate_json(settings.model_narrative, json.dumps(slim, ensure_ascii=False), SCHEMA, system=SYSTEM, thinking="low")
    except Exception as e:  # pragma: no cover
        log.warning("narrative generation failed: %s", e)
        return _stub(case)
