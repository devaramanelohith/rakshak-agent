"""Post-hold voice conversation with Rakshak (Gemini 3.8 Live, audio in/out, in-session function calling).
The customer can ask 'why did you stop this?' and say 'keep the hold' / 'I know this person, release it'
/ 'call my daughter'. Tools act on the case; the override is still a deliberate confirmation."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket
from google.genai import types

from .config import settings
from .llm import live_client
from .store import store

log = logging.getLogger("rakshak.guardian_voice")

TOOLS = [types.Tool(function_declarations=[
    types.FunctionDeclaration(name="keep_hold", description="Keep the payment on hold (the customer agrees it is suspicious).",
                              parameters={"type": "object", "properties": {"note": {"type": "string"}}}),
    types.FunctionDeclaration(name="request_release", description="The customer insists the payment is legitimate and wants to release the hold. Returns what the app will ask them to confirm.",
                              parameters={"type": "object", "properties": {"customer_reason": {"type": "string"}}, "required": ["customer_reason"]}),
    types.FunctionDeclaration(name="call_trusted_contact", description="Ask the app to call the customer's trusted contact now.",
                              parameters={"type": "object", "properties": {}}),
])]


def _system(case: dict) -> str:
    prof, pay, rub, payee, dec = case["profile"], case["payment"], case["rubric"], case["payee"], case["decision"]
    lang = {"hi": "Hindi", "en": "English", "en-sg": "English (Singapore)", "kn": "Kannada", "ta": "Tamil", "hinglish": "Hinglish"}.get(prof.get("language", "en"), "English")
    return f"""You are Rakshak, the calm, warm safety voice of the customer's bank. Speak {lang}, short sentences, no jargon.
The customer {prof.get('name')} (age band {prof.get('age_band')}) just tried to pay {pay['amount_inr']:.0f} to {pay['vpa']} ({pay.get('payee_name')}).
You paused it because: call risk {rub.get('risk_score')} ({rub.get('scam_type')}; signals: {', '.join(k for k, v in rub.get('signals', {}).items() if v) or 'none'});
payee risk band {payee.get('risk_band')} ({'; '.join(payee.get('reasons', [])[:2])}). Decision reasons: {'; '.join(dec.get('reasons', [])[:3])}.
Trusted contact: {prof.get('trusted_contact_name') or 'none'}. Hold minutes: {dec.get('hold_minutes')}.
Answer questions about why. If they insist on paying, call request_release once and tell them the app will ask them to confirm; never argue more than once.
If they are frightened, reassure: no real officer takes money by phone; hanging up is safe. Keep answers under 20 seconds."""


async def run_guardian_voice(ws: WebSocket, case_id: str) -> None:
    case = store().get_case(case_id)
    if not case:
        await ws.send_json({"type": "error", "error": "unknown case"})
        return
    if not settings.live_enabled():
        await ws.send_json({"type": "error", "error": "Live API not configured (needs GEMINI_API_KEY or RAKSHAK_LIVE_VIA_VERTEX)"})
        return
    cfg = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=_system(case),
        tools=TOOLS,
        output_audio_transcription=types.AudioTranscriptionConfig(),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=settings.tts_voice_guardian))),
    )
    async with live_client().aio.live.connect(model=settings.model_live, config=cfg) as live:
        await ws.send_json({"type": "guardian_ready"})
        await live.send_client_content(turns=types.Content(role="user", parts=[types.Part(text="(The customer opened the Rakshak conversation. Greet them in one sentence and ask what they want to know.)")]), turn_complete=True)

        async def from_browser():
            while True:
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    return
                if msg.get("bytes"):
                    await live.send_realtime_input(audio=types.Blob(data=msg["bytes"], mime_type="audio/pcm;rate=16000"))
                elif msg.get("text"):
                    data = json.loads(msg["text"])
                    if data.get("type") == "text":
                        await live.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=data["text"])]), turn_complete=True)
                    elif data.get("type") == "end":
                        return

        async def to_browser():
            # receive() yields one complete model turn and returns; keep reading turns until the client ends.
            while True:
                async for m in live.receive():
                    await _handle(m)

        async def _handle(m):
            if True:
                sc = m.server_content
                if sc:
                    if sc.model_turn:
                        for p in sc.model_turn.parts:
                            if p.inline_data:
                                await ws.send_bytes(p.inline_data.data)  # 24 kHz PCM16 from the Live model
                    if sc.output_transcription and sc.output_transcription.text:
                        await ws.send_json({"type": "guardian_text", "text": sc.output_transcription.text})
                    if sc.input_transcription and sc.input_transcription.text:
                        await ws.send_json({"type": "user_text", "text": sc.input_transcription.text})
                    if sc.interrupted:
                        await ws.send_json({"type": "interrupted"})
                if m.tool_call:
                    responses = []
                    for fc in m.tool_call.function_calls:
                        result = {"ok": True}
                        if fc.name == "request_release":
                            result = {"ok": True, "next": "app_shows_confirmation_dialog"}
                        await ws.send_json({"type": "tool", "name": fc.name, "args": dict(fc.args or {})})
                        responses.append(types.FunctionResponse(id=fc.id, name=fc.name, response=result))
                    await live.send_tool_response(function_responses=responses)

        t1 = asyncio.create_task(from_browser())
        t2 = asyncio.create_task(to_browser())
        done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
