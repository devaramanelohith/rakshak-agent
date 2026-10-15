"""CallSession: the live state of one guarded call.

Audio from each party (victim app mic, scammer console mic, Twilio leg, or server-side replay) is fed in as
16 kHz PCM16; it is relayed to the other party (a tiny VoIP) and streamed to that party's LiveTranscriber.
Every new utterance schedules a debounced rubric analysis; risk updates are broadcast to all UI sockets.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import time
import uuid
from typing import Any

from fastapi import WebSocket

from .analysis import LiveTranscriber, Rubric, analyze_transcript
from .config import settings
from .intervention import tts_pcm16, whisper_text
from .store import store

log = logging.getLogger("rakshak.session")


class CallSession:
    def __init__(self, session_id: str, user_id: str, mode: str = "audio", caller_display: str = "+91 98765 00301 (unknown)"):
        self.id = session_id
        self.user_id = user_id
        self.mode = mode  # audio | text | replay | eval
        self.caller_display = caller_display
        self.created_at = time.time()
        self.started_at: float | None = None
        self.state = "idle"  # idle | active | ended
        self.turns: list[dict] = []
        self.rubric: Rubric | None = None
        self.rubric_history: list[dict] = []
        self.events: list[dict] = []
        self.case_ids: list[str] = []
        self.ui_sockets: set[WebSocket] = set()
        self.audio_sockets: dict[str, WebSocket] = {}
        self.transcribers: dict[str, LiveTranscriber] = {}
        self.whispered = False
        self.source = "app"
        self.live_call = False
        self._analysis_task: asyncio.Task | None = None
        self._last_analysis = 0.0
        self._analysed_turns = 0
        self._pending_text: dict[str, str] = {}

    # ------------------------------------------------------------------ lifecycle
    @property
    def profile(self) -> dict:
        return store().get_profile(self.user_id)

    def elapsed(self) -> float:
        return round(time.time() - (self.started_at or self.created_at), 1)

    async def ensure_started(self, source: str = "app") -> None:
        if self.state == "idle":
            self.state = "active"
            self.started_at = time.time()
            self.source = source
            await self.broadcast({"type": "call_started", "source": source, "caller_display": self.caller_display})

    async def end(self) -> None:
        self.state = "ended"
        for t in list(self.transcribers.values()):
            await t.stop()
        self.transcribers.clear()
        await self.broadcast({"type": "call_ended"})

    # ------------------------------------------------------------------ transcript
    async def add_turn(self, speaker: str, text: str, t: float | None = None, analyse: bool = True) -> dict:
        await self.ensure_started(self.source)
        turn = {"t": round(t if t is not None else self.elapsed(), 1), "speaker": speaker, "text": text.strip()}
        self.turns.append(turn)
        await self.broadcast({"type": "transcript", "turn": turn})
        if analyse:
            self.schedule_analysis()
        return turn

    def schedule_analysis(self) -> None:
        if self._analysis_task and not self._analysis_task.done():
            self._analysis_task.cancel()
        self._analysis_task = asyncio.create_task(self._debounced_analysis())

    async def _debounced_analysis(self) -> None:
        try:
            await asyncio.sleep(settings.analysis_debounce_s)
            since = time.time() - self._last_analysis
            if since < settings.analysis_min_interval_s:
                await asyncio.sleep(settings.analysis_min_interval_s - since)
            await self.run_analysis()
        except asyncio.CancelledError:
            pass

    async def run_analysis(self) -> Rubric | None:
        if len(self.turns) == self._analysed_turns:
            return self.rubric
        self._last_analysis = time.time()
        try:
            rubric = await analyze_transcript(self.turns, self.profile)
        except Exception as e:  # pragma: no cover - network
            log.warning("analysis failed: %s", str(e)[:160])
            await self.broadcast({"type": "analysis_error", "error": str(e)[:160]})
            return self.rubric
        self._analysed_turns = len(self.turns)
        self.rubric = rubric
        self.rubric_history.append({"t": self.elapsed(), "risk": rubric.risk_score, "stage": rubric.stage, "signals": rubric.signal_count})
        if rubric.risk_score >= float(self.profile.get("hold_threshold") or settings.hold_threshold):
            # Remember the call on the customer's profile so a payment made after hanging up (or from another
            # screen/app) within the carry-over window is still judged with this call's context.
            store().put_profile(self.user_id, {"last_high_risk_call": {
                "session_id": self.id, "ts": time.time(), "risk_score": rubric.risk_score, "scam_type": rubric.scam_type,
                "signals": rubric.signals, "reasons": rubric.reasons[:3], "reasons_user_language": rubric.reasons_user_language[:3], "language": rubric.language}})
        await self.broadcast({"type": "risk_update", "t": self.elapsed(), "rubric": rubric.model_dump()})
        if rubric.risk_score >= settings.whisper_threshold and not self.whispered and self.profile.get("guardian_enabled", True):
            await self.whisper()
        return rubric

    async def whisper(self) -> None:
        """Private in-call warning to the victim's device only (the caller does not hear it)."""
        self.whispered = True
        lang, text = whisper_text(self.profile)
        audio_b64 = None
        try:
            pcm = await asyncio.wait_for(tts_pcm16(text), timeout=10)
            audio_b64 = base64.b64encode(pcm).decode() if pcm else None
        except Exception as e:  # pragma: no cover
            log.warning("whisper tts failed: %s", e)
        await self.send_private_audio("user", audio_b64, text, kind="whisper")
        await self.broadcast({"type": "whisper", "t": self.elapsed(), "text": text, "lang": lang})

    # ------------------------------------------------------------------ audio
    async def feed_audio(self, role: str, pcm16k: bytes, relay: bool = True) -> None:
        await self.ensure_started(self.source)
        tr = self.transcribers.get(role)
        if tr is None and settings.live_enabled():
            tr = LiveTranscriber(role, self._on_live_text, language_hint=None)
            self.transcribers[role] = tr
            await tr.start()
        if tr is not None:
            await tr.feed(pcm16k)
        if relay:
            other = "caller" if role == "user" else "user"
            ws = self.audio_sockets.get(other)
            if ws is not None:
                try:
                    await ws.send_bytes(pcm16k)
                except Exception:
                    self.audio_sockets.pop(other, None)

    async def _on_live_text(self, role: str, text: str) -> None:
        # The live transcriber emits per-utterance chunks; merge fragments arriving within 0.8s.
        await self.add_turn(role, text)

    async def send_private_audio(self, role: str, audio_b64: str | None, text: str, kind: str = "rakshak") -> None:
        ws = self.audio_sockets.get(role)
        if ws is None:
            return
        try:
            await ws.send_json({"type": "rakshak_audio", "kind": kind, "text": text, "audio_b64": audio_b64, "rate": 16000})
        except Exception:
            self.audio_sockets.pop(role, None)

    async def inject_caller_audio(self, pcm16k: bytes, text: str | None = None) -> None:
        """Server-side scripted caller line: play to the victim and transcribe as the caller."""
        ws = self.audio_sockets.get("user")
        if ws is not None:
            try:
                await ws.send_json({"type": "caller_audio", "audio_b64": base64.b64encode(pcm16k).decode(), "rate": 16000, "text": text})
            except Exception:
                self.audio_sockets.pop("user", None)

    # ------------------------------------------------------------------ ui
    async def broadcast(self, event: dict[str, Any]) -> None:
        event.setdefault("session_id", self.id)
        event.setdefault("ts", time.time())
        self.events.append({k: v for k, v in event.items() if k != "audio_b64"})
        self.events = self.events[-500:]
        dead = []
        for ws in list(self.ui_sockets):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.ui_sockets.discard(ws)
        await registry.broadcast_global(event)

    def snapshot(self) -> dict:
        return {
            "session_id": self.id,
            "user_id": self.user_id,
            "mode": self.mode,
            "state": self.state,
            "source": self.source,
            "caller_display": self.caller_display,
            "elapsed": self.elapsed(),
            "turns": self.turns,
            "rubric": self.rubric.model_dump() if self.rubric else None,
            "rubric_history": self.rubric_history,
            "case_ids": self.case_ids,
            "whispered": self.whispered,
            "transcribers": {r: {"connected": t.connected, "errors": t.errors} for r, t in self.transcribers.items()},
            "profile": self.profile,
        }


class SessionRegistry:
    def __init__(self) -> None:
        self.sessions: dict[str, CallSession] = {}
        self.global_sockets: set[WebSocket] = set()

    def get_or_create(self, session_id: str | None, user_id: str = "demo-user", mode: str = "audio", caller_display: str | None = None) -> CallSession:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        sid = session_id or uuid.uuid4().hex[:8]
        s = CallSession(sid, user_id=user_id, mode=mode, caller_display=caller_display or "+91 98765 00301 (unknown)")
        self.sessions[sid] = s
        return s

    def get(self, session_id: str) -> CallSession | None:
        return self.sessions.get(session_id)

    async def broadcast_global(self, event: dict) -> None:
        dead = []
        for ws in list(self.global_sockets):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.global_sockets.discard(ws)


registry = SessionRegistry()
