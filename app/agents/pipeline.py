"""ADK multi-agent payment guardian.

    SequentialAgent "rakshak_payment_guardian"
      1. risk_investigator  (LlmAgent) - pulls customer context + call rubric, looks up payee mule risk,
                                          checks the caller's claimed authority with Search grounding.
      2. decision_agent     (LlmAgent) - applies the bank's graded policy and records the action through the
                                          place_payment_hold tool (the human-in-the-loop pause).

Every event from the run is captured as a trace for the fraud-desk UI and the demo video.
If the run fails or exceeds the timeout, `app.payment` falls back to the deterministic policy (flagged).
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid

from google.adk import Runner
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models import Gemini
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ..config import settings
from ..llm import client as genai_client
from . import tools

log = logging.getLogger("rakshak.adk")
APP_NAME = "rakshak"

RISK_INSTRUCTION = """You are the risk investigator inside Rakshak, a bank's scam-moment guardian.
A customer is about to authorise a payment while on a phone call. The user message contains the customer profile,
the payment, the live-call rubric and a transcript excerpt. In your FIRST turn call BOTH tools together (parallel):
- lookup_payee_risk with the payment's vpa;
- check_regulated_entity with the organisation/role the caller claimed and what they asked for (if no authority or
  investment claim is present, pass claimed_organisation='none').
Then write a compact findings note (<= 120 words): call risk score and decisive signals; payee risk band and its
strongest indicator; the authority-check verdict with its source; amount versus the customer's typical transfer; and
anything that argues the payment is legitimate. Do not decide the action; that is the next agent's job."""

DECISION_INSTRUCTION = """You are the decision agent inside Rakshak. Read the investigator's findings in {risk_findings}.
Apply the bank's graded policy:
- proceed: no coercion signals and payee risk low/medium.
- warn: one weak signal (urgency alone, unknown payee) - say a short caution and let the customer continue.
- hold: two or more strong signals (authority_impersonation, threat, secrecy, safe_account, otp request, remote app) OR
  call risk >= the hold threshold OR payee risk band high/critical with any coercion signal. Hold for the customer's
  configured cooling-off period (default 30 minutes).
- hold_and_alert: same as hold when the customer has a trusted contact; also notify them.
Legitimate urgency (a relative needing fees, a landlord) without authority/secrecy/safe-account signals is NOT a hold.
You MUST call place_payment_hold exactly once with your decision; write user_message in the customer's language
(language code from the context: hi = Hindi in Devanagari, en-sg = Singapore English, kn = Kannada, ta = Tamil) in
plain words a 70-year-old understands, naming the concrete evidence (e.g. 'this account received money from 12 people in 2 days').
After the tool call, reply with one line: ACTION=<action> CONFIDENCE=<0-1>."""


def build_agent(model: str | None = None) -> SequentialAgent:
    model = model or settings.model_agent
    llm = Gemini(model=model, client=genai_client())  # same client/credentials as the rest of the app (Vertex or AI Studio)
    investigator = LlmAgent(
        name="risk_investigator",
        model=llm,
        description="Gathers call risk, payee mule risk and authority checks for a payment.",
        instruction=RISK_INSTRUCTION,
        tools=[tools.lookup_payee_risk, tools.check_regulated_entity],
        output_key="risk_findings",
        generate_content_config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level=settings.agent_thinking)),
    )
    decider = LlmAgent(
        name="decision_agent",
        model=llm,
        description="Applies the graded hold policy and records the action.",
        instruction=DECISION_INSTRUCTION,
        tools=[tools.place_payment_hold],
        output_key="decision_note",
        generate_content_config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level=settings.agent_thinking)),
    )
    return SequentialAgent(name="rakshak_payment_guardian", sub_agents=[investigator, decider])


_runners: dict[str, Runner] = {}
_session_service = InMemorySessionService()


def runner(model: str | None = None) -> Runner:
    model = model or settings.model_agent
    if model not in _runners:
        _runners[model] = Runner(app_name=APP_NAME, agent=build_agent(model), session_service=_session_service)
    return _runners[model]


def _summarise_event(ev) -> list[dict]:
    out: list[dict] = []
    ts = time.time()
    for fc in ev.get_function_calls() or []:
        out.append({"t": ts, "agent": ev.author, "type": "tool_call", "name": fc.name, "args": fc.args})
    for fr in ev.get_function_responses() or []:
        resp = fr.response
        if isinstance(resp, dict):
            resp = {k: (v if not isinstance(v, (list, dict)) or k in ("reasons", "sources", "decision") else str(v)[:200]) for k, v in resp.items()}
        out.append({"t": ts, "agent": ev.author, "type": "tool_result", "name": fr.name, "result": resp})
    if ev.content and ev.content.parts:
        text = "".join(p.text for p in ev.content.parts if getattr(p, "text", None))
        if text.strip() and not (ev.get_function_calls() or ev.get_function_responses()):
            out.append({"t": ts, "agent": ev.author, "type": "text", "text": text.strip()[:1200]})
    return out


async def run_payment_guardian(case: dict) -> tuple[dict | None, list[dict]]:
    """Run the ADK pipeline for `case` (retrying once on the fallback model). Returns (decision or None, trace)."""
    decision, trace = await _run_once(case, settings.model_agent)
    if decision is None and settings.model_agent_fallback and settings.model_agent_fallback != settings.model_agent:
        # Retry on the faster fallback model whether the primary errored or ran out of its time budget.
        trace.append({"t": time.time(), "agent": "system", "type": "text", "text": f"retrying on {settings.model_agent_fallback}"})
        d2, t2 = await _run_once(case, settings.model_agent_fallback)
        return d2, trace + t2
    return decision, trace


async def _run_once(case: dict, model: str) -> tuple[dict | None, list[dict]]:
    trace: list[dict] = []
    token = tools.current_case.set(case)
    t0 = time.time()
    try:
        user_id = case["user_id"]
        session_id = f"pay-{case['case_id']}-{model.replace('.', '')}"
        await _session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        import json as _json
        ctx = tools.get_customer_context()
        msg = types.Content(role="user", parts=[types.Part(text=(
            f"Evaluate payment {case['payment']['amount_inr']:.0f} INR to {case['payment']['vpa']} "
            f"({case['payment'].get('payee_name', '')}) for customer {user_id}. Case id {case['case_id']}.\n"
            f"Context JSON:\n{_json.dumps(ctx, ensure_ascii=False)}"))])

        async def _run():
            async for ev in runner(model).run_async(user_id=user_id, session_id=session_id, new_message=msg):
                trace.extend(_summarise_event(ev))

        await asyncio.wait_for(_run(), timeout=settings.agent_timeout_s)
        decision = case.pop("_agent_decision", None)
        if decision:
            decision["latency_ms"] = int((time.time() - t0) * 1000)
            decision["model"] = model
        return decision, trace
    except asyncio.TimeoutError:
        trace.append({"t": time.time(), "agent": "system", "type": "error", "text": f"agent timeout after {settings.agent_timeout_s}s"})
        return None, trace
    except Exception as e:  # pragma: no cover - network
        log.exception("ADK run failed")
        trace.append({"t": time.time(), "agent": "system", "type": "error", "text": str(e)[:300]})
        return None, trace
    finally:
        tools.current_case.reset(token)


def new_case_id() -> str:
    return "case_" + uuid.uuid4().hex[:10]
