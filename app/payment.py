"""Payment-moment orchestration.

Fast path (<100 ms): the deterministic fusion policy (call rubric x payee risk x profile) decides and the hold,
voice barge-in and trusted-contact alert fire immediately.
Agent path (seconds): the ADK investigator + decision agents run concurrently; they can CONFIRM or UPGRADE the
action (never relax it), replace the reasons/message with evidence-grounded ones, and their trace is filed on the
case. If they finish within `agent_sync_wait_s` the response already includes them; otherwise the UI gets a
`case_update` event when they do. The fraud-desk narrative is generated after the agent completes.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import time

from .agents.pipeline import new_case_id, run_payment_guardian
from .alerts import notify_trusted_contact
from .analysis import Rubric, format_turns
from .config import settings
from .intervention import compose, tts_pcm16
from .narrative import generate_case_narrative
from .payee_risk import lookup_payee
from .policy import fuse
from .store import store

log = logging.getLogger("rakshak.payment")
ORDER = ["proceed", "warn", "hold", "hold_and_alert"]
STATUS = {"proceed": "approved", "warn": "warned", "hold": "on_hold", "hold_and_alert": "on_hold"}


def public_case(case: dict) -> dict:
    return {k: v for k, v in case.items() if not k.startswith("_")}


async def _speak(text: str) -> str | None:
    try:
        pcm = await asyncio.wait_for(tts_pcm16(text), timeout=12)
        return base64.b64encode(pcm).decode() if pcm else None
    except Exception as e:  # pragma: no cover
        log.warning("TTS failed: %s", e)
        return None


async def evaluate_payment(session, vpa: str, payee_name: str, amount_inr: float, use_agent: bool = True, wait_s: float | None = None) -> dict:
    profile = store().get_profile(session.user_id)
    rubric: Rubric = session.rubric or Rubric()
    payee = lookup_payee(vpa)
    fusion = fuse(rubric.risk_score, rubric.signals, payee, amount_inr, profile)
    hold_minutes = settings.hold_minutes if fusion.action.startswith("hold") else 0
    lang, scripted = compose(fusion.action, profile, amount_inr, settings.hold_minutes)
    case = {
        "case_id": new_case_id(),
        "session_id": session.id,
        "user_id": session.user_id,
        "created_at": time.time(),
        "status": STATUS[fusion.action],
        "profile": profile,
        "payment": {"vpa": vpa, "payee_name": payee_name, "amount_inr": float(amount_inr)},
        "rubric": rubric.model_dump(),
        "transcript_excerpt": format_turns(session.turns, 2500),
        "payee": payee,
        "policy": {"score": fusion.score, "action": fusion.action, "reasons": fusion.reasons, "call_risk": fusion.call_risk, "payee_risk": fusion.payee_risk},
        "decision": {
            "action": fusion.action,
            "hold_minutes": hold_minutes,
            "notify_trusted_contact": fusion.action == "hold_and_alert",
            "confidence": round(min(0.95, 0.5 + abs(fusion.score - 0.5)), 2),
            "reasons": fusion.reasons[:4],
            "user_message": scripted,
            "decided_by": "policy_fast_path",
            "latency_ms": 0,
            "agent_status": "pending" if (use_agent and settings.llm_enabled() and session.mode != "eval") else "skipped",
        },
        "trace": [],
        "timeline": [{"t": time.time(), "event": "payment_initiated"}, {"t": time.time(), "event": f"fast_path:{fusion.action}", "score": fusion.score}],
    }
    if hold_minutes:
        case["hold_until"] = time.time() + 60 * hold_minutes
    store().put_case(case)
    session.case_ids.append(case["case_id"])

    # --- execute immediately -----------------------------------------------------------------
    audio_b64 = await _speak(scripted) if fusion.action != "proceed" and scripted else None
    if fusion.action == "hold_and_alert":
        alert = await notify_trusted_contact(case, profile)
        case["alert"] = alert
        case["timeline"].append({"t": time.time(), "event": "trusted_contact_notified", "channels": alert["channels"]})
        store().put_case(case)
    await session.broadcast({"type": "decision", "case": public_case(case), "audio_b64": audio_b64, "audio_rate": 16000, "spoken_text": scripted, "lang": lang})

    # --- agent path ------------------------------------------------------------------------------
    if case["decision"]["agent_status"] == "pending":
        task = asyncio.create_task(_agent_followup(case["case_id"], session))
        wait = settings.agent_sync_wait_s if wait_s is None else wait_s
        if wait > 0:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=wait)
            except asyncio.TimeoutError:
                pass
        case = store().get_case(case["case_id"]) or case
    else:
        asyncio.create_task(_write_narrative(case["case_id"]))
    return {"case": public_case(case), "audio_b64": audio_b64, "spoken_text": scripted, "lang": lang}


async def _agent_followup(case_id: str, session) -> None:
    case = store().get_case(case_id)
    if not case:
        return
    await session.broadcast({"type": "agent_running", "case_id": case_id})
    t0 = time.time()
    decision, trace = await run_payment_guardian(case)
    case = store().get_case(case_id) or case
    case["trace"] = trace
    fast = case["decision"]
    if decision is None:
        fast["agent_status"] = "failed"
        case["timeline"].append({"t": time.time(), "event": "agent_failed"})
    else:
        agent_action = decision["action"]
        final = ORDER[max(ORDER.index(agent_action), ORDER.index(fast["action"]))]  # never relax below the policy
        if agent_action != final:
            decision["reasons"].append(f"policy floor applied (agent said {agent_action})")
        upgraded = ORDER.index(final) > ORDER.index(fast["action"])
        profile = case["profile"]
        if final == "hold_and_alert" and not profile.get("trusted_contact_name"):
            final = "hold"
        case["decision"] = {
            **fast,
            "action": final,
            "hold_minutes": decision.get("hold_minutes") or (settings.hold_minutes if final.startswith("hold") else 0),
            "notify_trusted_contact": final == "hold_and_alert",
            "confidence": decision.get("confidence", fast["confidence"]),
            "reasons": (decision.get("reasons") or fast["reasons"])[:4],
            "user_message": decision.get("user_message") or fast["user_message"],
            "decided_by": "adk_agent",
            "agent_status": "confirmed" if not upgraded else "upgraded",
            "policy_action": fast["action"],
            "agent_action": agent_action,
            "model": decision.get("model"),
            "latency_ms": int((time.time() - t0) * 1000),
        }
        case["status"] = STATUS[final] if case["status"] in ("approved", "warned", "on_hold") else case["status"]
        case["timeline"].append({"t": time.time(), "event": f"agent:{final}", "upgraded": upgraded, "latency_ms": case["decision"]["latency_ms"]})
        if upgraded and final.startswith("hold"):
            case["hold_until"] = time.time() + 60 * case["decision"]["hold_minutes"]
            _, scripted = compose(final, profile, case["payment"]["amount_inr"], case["decision"]["hold_minutes"])
            audio_b64 = await _speak(scripted)
            await session.send_private_audio("user", audio_b64, scripted, kind="rakshak")
            if final == "hold_and_alert" and not case.get("alert"):
                alert = await notify_trusted_contact(case, profile)
                case["alert"] = alert
                case["timeline"].append({"t": time.time(), "event": "trusted_contact_notified", "channels": alert["channels"]})
    store().put_case(case)
    await session.broadcast({"type": "case_update", "case": public_case(case), "agent": True})
    await _write_narrative(case_id)


async def _write_narrative(case_id: str) -> None:
    case = store().get_case(case_id)
    if not case:
        return
    try:
        case["narrative"] = await generate_case_narrative(case)
        store().put_case(case)
    except Exception as e:  # pragma: no cover
        log.warning("narrative failed: %s", e)


async def override_case(case_id: str, reason: str, session=None) -> dict:
    case = store().get_case(case_id)
    if not case:
        raise KeyError(case_id)
    case["status"] = "overridden_by_user"
    case["override"] = {"t": time.time(), "reason": reason}
    case["timeline"].append({"t": time.time(), "event": "user_override", "reason": reason})
    store().put_case(case)
    if session:
        await session.broadcast({"type": "case_update", "case": public_case(case)})
    asyncio.create_task(_write_narrative(case_id))
    return public_case(case)


async def cancel_case(case_id: str, session=None) -> dict:
    case = store().get_case(case_id)
    if not case:
        raise KeyError(case_id)
    case["status"] = "cancelled_by_user"
    case["timeline"].append({"t": time.time(), "event": "user_cancelled_payment"})
    store().put_case(case)
    if session:
        await session.broadcast({"type": "case_update", "case": public_case(case)})
    asyncio.create_task(_write_narrative(case_id))
    return public_case(case)


def expire_holds() -> list[str]:
    now = time.time()
    released = []
    for case in store().list_cases():
        if case.get("status") == "on_hold" and case.get("hold_until") and now > case["hold_until"]:
            case["status"] = "hold_expired"
            case["timeline"].append({"t": now, "event": "hold_expired"})
            store().put_case(case)
            released.append(case["case_id"])
    return released
