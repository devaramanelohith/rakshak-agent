"""Rakshak API + static UI. Run: uv run uvicorn app.main:app --reload --port 8080"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from . import payment as payment_mod  # noqa: E402
from .config import configure_env, settings  # noqa: E402
from .guardian_voice import run_guardian_voice  # noqa: E402
from .intervention import prewarm, tts_pcm16  # noqa: E402
from .payee_risk import all_payees, lookup_payee  # noqa: E402
from .replay import get_script, load_scripts, start_replay, stop_replay  # noqa: E402
from .session import registry  # noqa: E402
from .store import DEFAULT_PROFILES, store  # noqa: E402
from .telephony.twilio import router as twilio_router  # noqa: E402

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("rakshak.main")
configure_env()

app = FastAPI(title="Rakshak - scam-moment interception agent", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(twilio_router)
WEB = settings.web_dir
app.mount("/static", StaticFiles(directory=str(WEB)), name="static")


from contextlib import asynccontextmanager  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store()
    tasks = []
    if settings.llm_enabled() and os.getenv("RAKSHAK_PREWARM_TTS", "1") == "1":
        async def _pw():
            try:
                n = await prewarm(list(DEFAULT_PROFILES.values()))
                log.info("prewarmed %d guardian audio clips", n)
            except Exception as e:  # pragma: no cover
                log.warning("prewarm failed: %s", e)
        tasks.append(asyncio.create_task(_pw()))

    async def _expiry_loop():
        while True:
            await asyncio.sleep(30)
            for cid in payment_mod.expire_holds():
                log.info("hold expired %s", cid)
    tasks.append(asyncio.create_task(_expiry_loop()))
    yield
    for t in tasks:
        t.cancel()


app.router.lifespan_context = lifespan


# ----------------------------------------------------------------------------- pages
def _page(name: str) -> FileResponse:
    return FileResponse(str(WEB / name))


@app.get("/")
async def index():
    return _page("index.html")


@app.get("/scammer")
async def scammer_page():
    return _page("scammer.html")


@app.get("/desk")
async def desk_page():
    return _page("desk.html")


@app.get("/healthz")
async def healthz():
    return {"ok": True, "llm": settings.llm_enabled(), "live": settings.live_enabled(), "vertex": settings.use_vertex, "project": settings.project if settings.use_vertex else None, "models": {"rubric": settings.model_rubric, "transcribe": settings.model_transcribe_live, "tts": settings.model_tts, "live": settings.model_live, "agent": settings.model_agent}, "time": time.time()}


# ----------------------------------------------------------------------------- sessions
class SessionIn(BaseModel):
    session_id: str | None = None
    user_id: str = "demo-user"
    mode: str = "audio"
    caller_display: str | None = None


@app.post("/api/sessions")
async def create_session(body: SessionIn):
    s = registry.get_or_create(body.session_id, user_id=body.user_id, mode=body.mode, caller_display=body.caller_display)
    return s.snapshot()


@app.get("/api/sessions")
async def list_sessions():
    return [s.snapshot() | {"turns": len(s.turns)} for s in registry.sessions.values()]


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    s = registry.get(session_id)
    if not s:
        raise HTTPException(404, "unknown session")
    return s.snapshot()


class TurnIn(BaseModel):
    speaker: str  # caller | user
    text: str
    t: float | None = None


@app.post("/api/sessions/{session_id}/turns")
async def add_turn(session_id: str, body: TurnIn):
    """Transcript-driven path (eval, text demo, or a fallback if live audio misbehaves)."""
    s = registry.get_or_create(session_id, mode="text")
    turn = await s.add_turn(body.speaker, body.text, body.t)
    return {"turn": turn, "turns": len(s.turns)}


@app.post("/api/sessions/{session_id}/analyze")
async def analyze_now(session_id: str):
    s = registry.get(session_id)
    if not s:
        raise HTTPException(404, "unknown session")
    r = await s.run_analysis()
    return r.model_dump() if r else None


@app.post("/api/sessions/{session_id}/end")
async def end_session(session_id: str):
    s = registry.get(session_id)
    if not s:
        raise HTTPException(404, "unknown session")
    stop_replay(session_id)
    await s.end()
    return {"ok": True}


class ReplayIn(BaseModel):
    script_id: str
    voice: bool = True
    pace: float = 1.0
    stop_at_marker: str | None = "payment_demand"


@app.post("/api/sessions/{session_id}/replay")
async def replay(session_id: str, body: ReplayIn):
    s = registry.get_or_create(session_id, mode="replay")
    script = get_script(body.script_id)
    if not script:
        raise HTTPException(404, "unknown script")
    start_replay(s, script, voice=body.voice, pace=body.pace, stop_at_marker=body.stop_at_marker)
    return {"ok": True, "script": script["id"], "lines": len(script["lines"])}


@app.post("/api/sessions/{session_id}/replay/stop")
async def replay_stop(session_id: str):
    return {"stopped": stop_replay(session_id)}


class SayIn(BaseModel):
    text: str
    speaker: str = "caller"
    voice: bool = True


@app.post("/api/sessions/{session_id}/say")
async def say(session_id: str, body: SayIn):
    """Inject one line as the caller (voiced with the caller TTS voice to the victim device) or the user."""
    s = registry.get_or_create(session_id)
    await s.add_turn(body.speaker, body.text)
    if body.speaker == "caller" and body.voice and settings.llm_enabled():
        try:
            pcm = await asyncio.wait_for(tts_pcm16(body.text, voice=settings.tts_voice_caller), timeout=15)
            if pcm:
                await s.inject_caller_audio(pcm, text=body.text)
        except Exception as e:  # pragma: no cover
            log.warning("say tts failed: %s", e)
    return {"ok": True, "turns": len(s.turns)}


@app.get("/api/scripts")
async def scripts():
    return [{k: s.get(k) for k in ("id", "title", "scam_type", "language", "duration_sec", "expected_outcome", "payment_attempt")} for s in load_scripts()]


@app.get("/api/scripts/{script_id}")
async def script(script_id: str):
    sc = get_script(script_id)
    if not sc:
        raise HTTPException(404, "unknown script")
    return sc


# ----------------------------------------------------------------------------- payments
class PaymentIn(BaseModel):
    session_id: str
    vpa: str
    payee_name: str = ""
    amount_inr: float
    use_agent: bool = True


@app.post("/api/payments")
async def initiate_payment(body: PaymentIn):
    s = registry.get_or_create(body.session_id)
    result = await payment_mod.evaluate_payment(s, body.vpa, body.payee_name, body.amount_inr, use_agent=body.use_agent)
    return result


@app.post("/api/sessions/{session_id}/prewarm")
async def prewarm_session(session_id: str, amount_inr: float):
    """Pre-generate Rakshak's voice for an amount (called when the pay screen opens) so the barge-in is instant."""
    s = registry.get_or_create(session_id)
    asyncio.create_task(payment_mod.prewarm_for(s, amount_inr))
    return {"ok": True}


class OverrideIn(BaseModel):
    reason: str = "customer confirmed they know the payee"


@app.post("/api/cases/{case_id}/override")
async def override(case_id: str, body: OverrideIn):
    case = store().get_case(case_id)
    if not case:
        raise HTTPException(404, "unknown case")
    return await payment_mod.override_case(case_id, body.reason, registry.get(case["session_id"]))


@app.post("/api/cases/{case_id}/cancel")
async def cancel(case_id: str):
    case = store().get_case(case_id)
    if not case:
        raise HTTPException(404, "unknown case")
    return await payment_mod.cancel_case(case_id, registry.get(case["session_id"]))


@app.get("/api/cases")
async def cases():
    return [payment_mod.public_case(c) for c in store().list_cases()]


@app.get("/api/cases/{case_id}")
async def case(case_id: str):
    c = store().get_case(case_id)
    if not c:
        raise HTTPException(404, "unknown case")
    return payment_mod.public_case(c)


@app.get("/api/alerts")
async def alerts(user_id: str | None = None):
    return store().list_alerts(user_id)


# ----------------------------------------------------------------------------- profiles & payees
@app.get("/api/profiles/{user_id}")
async def get_profile(user_id: str):
    return store().get_profile(user_id)


@app.put("/api/profiles/{user_id}")
async def put_profile(user_id: str, patch: dict):
    return store().put_profile(user_id, patch)


@app.get("/api/payees")
async def payees():
    return all_payees()


@app.get("/api/payees/{vpa}")
async def payee(vpa: str):
    return lookup_payee(vpa)


@app.get("/api/tts")
async def tts(text: str, voice: str | None = None):
    pcm = await tts_pcm16(text, voice=voice)
    return {"audio_b64": base64.b64encode(pcm).decode(), "rate": 16000, "bytes": len(pcm)}


@app.get("/api/eval/latest")
async def eval_latest():
    p = Path(settings.runtime_dir) / "eval_results.json"
    if not p.exists():
        return JSONResponse({"error": "run scripts/eval.py first"}, status_code=404)
    return FileResponse(str(p))


# ----------------------------------------------------------------------------- websockets
@app.websocket("/ws/events/{session_id}")
async def ws_events(ws: WebSocket, session_id: str):
    await ws.accept()
    if session_id == "all":
        registry.global_sockets.add(ws)
        await ws.send_json({"type": "hello", "sessions": [s.snapshot() | {"turns": len(s.turns)} for s in registry.sessions.values()]})
    else:
        s = registry.get_or_create(session_id)
        s.ui_sockets.add(ws)
        await ws.send_json({"type": "hello", "snapshot": s.snapshot()})
    try:
        while True:
            await ws.receive_text()  # keepalive / ignored
    except WebSocketDisconnect:
        pass
    finally:
        registry.global_sockets.discard(ws)
        for s in registry.sessions.values():
            s.ui_sockets.discard(ws)


@app.websocket("/ws/call/{session_id}/{role}")
async def ws_call(ws: WebSocket, session_id: str, role: str):
    """Binary frames: 16 kHz mono PCM16 from this role's microphone. JSON frames: control.
    Server -> client: binary = the other party's audio; JSON = rakshak_audio / caller_audio."""
    if role not in ("user", "caller"):
        await ws.close(code=4000)
        return
    await ws.accept()
    s = registry.get_or_create(session_id)
    s.audio_sockets[role] = ws
    await s.ensure_started(source="app")
    await s.broadcast({"type": "party_joined", "role": role})
    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if msg.get("bytes"):
                await s.feed_audio(role, msg["bytes"], relay=True)
            elif msg.get("text"):
                import json as _json
                data = _json.loads(msg["text"])
                if data.get("type") == "text_turn":
                    await s.add_turn(role, data["text"])
                elif data.get("type") == "end_call":
                    stop_replay(session_id)
                    await s.end()
                    break
    except WebSocketDisconnect:
        pass
    finally:
        if s.audio_sockets.get(role) is ws:
            s.audio_sockets.pop(role, None)
        await s.broadcast({"type": "party_left", "role": role})


@app.websocket("/ws/guardian/{case_id}")
async def ws_guardian(ws: WebSocket, case_id: str):
    await ws.accept()
    try:
        await run_guardian_voice(ws, case_id)
    except WebSocketDisconnect:
        pass
    except Exception as e:  # pragma: no cover
        log.warning("guardian voice ended: %s", str(e)[:160])
        try:
            await ws.send_json({"type": "error", "error": str(e)[:160]})
        except Exception:
            pass
