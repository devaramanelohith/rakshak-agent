"""Deterministic fusion policy. Used (a) as the safety-net when the ADK agent is unavailable or
slow, (b) by the evaluation script, and (c) as the rule set the Decision agent is instructed to respect.

The whole point of Rakshak is this fusion: call semantics x payee risk x profile -> graded action.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import settings

ACTIONS = ("proceed", "warn", "hold", "hold_and_alert")


@dataclass
class FusionResult:
    score: float
    action: str
    reasons: list[str] = field(default_factory=list)
    call_risk: float = 0.0
    payee_risk: float = 0.0


def fuse(
    call_risk: float,
    signals: dict | None,
    payee: dict | None,
    amount_inr: float,
    profile: dict | None,
) -> FusionResult:
    signals = signals or {}
    payee = payee or {}
    profile = profile or {}
    payee_risk = float(payee.get("mule_risk_score") or 0.3)
    reasons: list[str] = []

    score = 0.65 * call_risk + 0.35 * payee_risk
    if signals.get("safe_account") or signals.get("otp_or_credential_request"):
        score += 0.10
        reasons.append("Caller demanded a transfer to a 'safe account' or asked for credentials")
    if signals.get("authority_impersonation") and signals.get("threat_of_arrest_or_harm"):
        score += 0.05
        reasons.append("Authority impersonation combined with threats (digital-arrest pattern)")
    if payee.get("risk_band") in ("critical", "high") and call_risk >= 0.5:
        score += 0.10
        reasons.append(f"Payee is in the {payee.get('risk_band')} mule-risk band while the call shows coercion")
    if payee.get("linked_complaints_1930", 0):
        reasons.append(f"Payee named in {payee['linked_complaints_1930']} cybercrime-helpline complaints")
    if amount_inr >= 50000:
        score += 0.05
        reasons.append("High-value transfer")
    typical = float(profile.get("typical_transfer_inr") or 0)
    if typical and amount_inr >= 5 * typical:
        score += 0.05
        reasons.append("Amount is more than 5x the customer's usual transfer")
    score = max(0.0, min(1.0, score))

    hold_t = float(profile.get("hold_threshold") or settings.hold_threshold)
    warn_t = float(profile.get("warn_threshold") or settings.warn_threshold)
    if score >= hold_t:
        action = "hold_and_alert" if profile.get("trusted_contact_name") else "hold"
    elif score >= warn_t:
        action = "warn"
    else:
        action = "proceed"
    if not reasons:
        reasons.append("No coercion signals on the call and the payee looks ordinary" if action == "proceed" else "Elevated combined risk")
    return FusionResult(score=round(score, 3), action=action, reasons=reasons, call_risk=call_risk, payee_risk=payee_risk)
