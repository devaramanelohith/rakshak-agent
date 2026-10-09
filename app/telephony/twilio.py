"""Twilio Media Streams bridge: lets a judge call a real phone number. Twilio dials the 'scammer' phone,
and streams both legs (8 kHz mu-law) to /ws/twilio/{session_id}; we decode, resample to 16 kHz and feed the
same transcribers as the in-app call. This is the telco-side deployment shape (FICO Scam Signal pattern)."""
from __future__ import annotations

import base64
import json
import logging

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from ..audio import mulaw_to_pcm16, resample_pcm16
from ..config import settings

log = logging.getLogger("rakshak.twilio")
router = APIRouter()


def _public_ws_base(request: Request) -> str:
    base = settings.public_base_url or str(request.base_url).rstrip("/")
    return base.replace("https://", "wss://").replace("http://", "ws://")


@router.post("/twilio/voice")
async def twilio_voice(request: Request):
    """TwiML webhook. Configure your Twilio number's Voice URL to POST here.
    Query/form param `session` links the call to an app session (default: 'phone')."""
    form = await request.form()
    session_id = request.query_params.get("session") or form.get("session") or "phone"
    ws = f"{_public_ws_base(request)}/ws/twilio/{session_id}"
    dial = settings.twilio_dial_number
    say = "Rakshak guardian mode is on for this call."
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Start><Stream url="{ws}" track="both_tracks"/></Start>
  <Say>{say}</Say>
  {f'<Dial>{dial}</Dial>' if dial else '<Pause length="600"/>'}
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.websocket("/ws/twilio/{session_id}")
async def twilio_media(ws: WebSocket, session_id: str):
    from ..session import registry  # late import to avoid cycles

    await ws.accept()
    session = registry.get_or_create(session_id, user_id="demo-user", mode="audio")
    await session.ensure_started(source="twilio")
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            ev = msg.get("event")
            if ev == "media":
                media = msg["media"]
                track = media.get("track", "inbound")  # inbound = the person who called (victim), outbound = dialed party
                role = "user" if track == "inbound" else "caller"
                pcm8 = mulaw_to_pcm16(base64.b64decode(media["payload"]))
                await session.feed_audio(role, resample_pcm16(pcm8, 8000, 16000), relay=False)
            elif ev == "start":
                log.info("twilio stream start %s", msg.get("start", {}).get("callSid"))
                await session.broadcast({"type": "call_started", "source": "twilio"})
            elif ev == "stop":
                break
    except WebSocketDisconnect:
        pass
    finally:
        await session.broadcast({"type": "call_ended", "source": "twilio"})
