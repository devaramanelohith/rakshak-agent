"""Function tools exposed to the ADK agents. Each is a plain Python function with a docstring: ADK turns
the signature + docstring into the tool schema the model sees."""
from __future__ import annotations

import logging
from contextvars import ContextVar

from google.genai import types

from ..config import settings
from ..llm import client
from ..payee_risk import lookup_payee
from .advisories import lookup_advisory

log = logging.getLogger("rakshak.tools")

# The payment being evaluated is set by the pipeline before the run; tools read it from here.
current_case: ContextVar[dict | None] = ContextVar("rakshak_current_case", default=None)


def lookup_payee_risk(vpa: str) -> dict:
    """Look up mule-account risk indicators for a UPI / PayNow payee ID.

    Args:
        vpa: the payee's virtual payment address, e.g. 'cbi.verification@rakshakdemo'.
    Returns:
        risk_band (critical/high/medium/low), mule_risk_score 0-1, account_age_days, fan_in_48h (distinct payers
        in 48h), cash_out_ratio_7d, dormant_days_before_burst, fri_level (telecom Financial Risk Indicator),
        linked_complaints_1930, kyc_tier and short reasons.
    """
    row = lookup_payee(vpa)
    keep = ("vpa", "display_name", "risk_band", "mule_risk_score", "account_age_days", "fan_in_48h", "fan_out_48h",
            "cash_out_ratio_7d", "dormant_days_before_burst", "fri_level", "linked_complaints_1930", "kyc_tier", "reasons", "source")
    return {k: row.get(k) for k in keep}


async def check_regulated_entity(claimed_organisation: str, claimed_role: str, what_they_asked_for: str) -> dict:
    """Check whether an organisation the caller claims to represent would legitimately contact a customer this
    way and ask for this. Uses the bank's table of official advisories (I4C, RBI, SPF/ScamShield, MAS, SEBI) and
    falls back to Google Search grounding for organisations not covered.

    Args:
        claimed_organisation: e.g. 'CBI Mumbai', 'RBI', 'Monetary Authority of Singapore', 'SEBI-registered adviser XYZ'.
        claimed_role: e.g. 'inspector', 'investment adviser'.
        what_they_asked_for: e.g. 'transfer money to a safe account for verification'.
    Returns:
        verdict ('legitimate_practice' | 'never_done_by_this_entity' | 'unclear'), explanation, and sources.
    """
    hit = lookup_advisory(claimed_organisation, claimed_role, what_they_asked_for)
    if hit:
        return hit
    if not settings.llm_enabled():
        return {"verdict": "unclear", "explanation": "no advisory matched (stub)", "sources": []}
    q = (
        f"A caller says they are a {claimed_role} from {claimed_organisation} and asked a bank customer to: {what_they_asked_for}. "
        "Using official public advisories, answer: does this organisation ever do this over a phone call? "
        "Reply in <= 3 sentences starting with one of: LEGITIMATE_PRACTICE / NEVER_DONE_BY_THIS_ENTITY / UNCLEAR."
    )
    try:
        import asyncio as _asyncio
        resp = await _asyncio.wait_for(client().aio.models.generate_content(
            model=settings.model_agent, contents=q,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())],
                                               thinking_config=types.ThinkingConfig(thinking_level="low"))), timeout=8)
        text = resp.text or ""
        up = text.upper()
        verdict = "never_done_by_this_entity" if "NEVER_DONE" in up else ("legitimate_practice" if "LEGITIMATE_PRACTICE" in up else "unclear")
        sources = []
        gm = resp.candidates[0].grounding_metadata if resp.candidates else None
        if gm and gm.grounding_chunks:
            for ch in gm.grounding_chunks[:4]:
                if ch.web:
                    sources.append({"title": ch.web.title, "uri": ch.web.uri})
        return {"verdict": verdict, "explanation": text.strip()[:600], "sources": sources, "source": "google_search_grounding"}
    except Exception as e:  # pragma: no cover
        log.warning("search grounding failed: %s", str(e)[:120])
        return {"verdict": "unclear", "explanation": f"search unavailable: {str(e)[:80]}", "sources": [], "source": "none"}


def get_customer_context() -> dict:
    """Return the customer's protection profile and the live-call rubric for the payment being evaluated."""
    case = current_case.get() or {}
    prof = case.get("profile", {})
    return {
        "customer": {k: prof.get(k) for k in ("name", "age_band", "language", "trusted_contact_name", "typical_transfer_inr", "prior_alerts")},
        "thresholds": {"warn": prof.get("warn_threshold", settings.warn_threshold), "hold": prof.get("hold_threshold", settings.hold_threshold)},
        "payment": case.get("payment"),
        "call_rubric": case.get("rubric"),
        "transcript_excerpt": case.get("transcript_excerpt", ""),
    }


def place_payment_hold(action: str, hold_minutes: int, notify_trusted_contact: bool, confidence: float, reasons: list[str], user_message: str) -> dict:
    """Record the guardian's decision for this payment. This is the action node: the system executes it and the
    customer keeps a one-tap override, so it behaves as a human-in-the-loop pause rather than a block.

    Args:
        action: one of 'proceed', 'warn', 'hold', 'hold_and_alert'.
        hold_minutes: cooling-off period for hold actions (0 for proceed/warn).
        notify_trusted_contact: whether to alert the customer's trusted contact now.
        confidence: 0-1 confidence in the decision.
        reasons: up to 4 short evidence-based reasons.
        user_message: one or two sentences to say to the customer, in the customer's language.
    Returns:
        status 'recorded' plus the case id; for holds the status is 'pending_user_override'.
    """
    case = current_case.get()
    decision = {
        "action": action if action in ("proceed", "warn", "hold", "hold_and_alert") else "hold",
        "hold_minutes": int(hold_minutes or 0),
        "notify_trusted_contact": bool(notify_trusted_contact),
        "confidence": float(confidence),
        "reasons": list(reasons or [])[:4],
        "user_message": user_message,
        "decided_by": "adk_agent",
    }
    if case is not None:
        case["_agent_decision"] = decision
    status = "pending_user_override" if decision["action"] in ("hold", "hold_and_alert") else "recorded"
    return {"status": status, "case_id": (case or {}).get("case_id"), "decision": decision}
