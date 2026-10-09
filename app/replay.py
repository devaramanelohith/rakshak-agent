"""Scripted replay: drives a demo script through a session as if a caller were speaking.
Lines are injected as caller turns (and, when the victim app is connected, voiced with the caller TTS
voice so the judge hears the scammer). The user's lines are injected as text so the rubric sees both sides."""
from __future__ import annotations

import asyncio
import json
import logging
from functools import lru_cache

from .config import settings
from .intervention import tts_pcm16

log = logging.getLogger("rakshak.replay")


@lru_cache(maxsize=1)
def load_scripts() -> list[dict]:
    p = settings.data_dir / "scripts" / "demo_scripts.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def get_script(script_id: str) -> dict | None:
    return next((s for s in load_scripts() if s["id"] == script_id), None)


_running: dict[str, asyncio.Task] = {}


def stop_replay(session_id: str) -> bool:
    task = _running.pop(session_id, None)
    if task and not task.done():
        task.cancel()
        return True
    return False


async def _speak_line(session, line: dict, voice: bool) -> None:
    text = line["text"]
    if voice and settings.llm_enabled():
        try:
            pcm = await asyncio.wait_for(tts_pcm16(text, voice=settings.tts_voice_caller), timeout=15)
            if pcm:
                await session.inject_caller_audio(pcm, text=text)
                await asyncio.sleep(len(pcm) / 32000 + 0.3)  # wait for playback
        except Exception as e:  # pragma: no cover
            log.warning("caller tts failed: %s", e)


async def _run(session, script: dict, voice: bool, pace: float, stop_at_marker: str | None) -> None:
    await session.ensure_started(source="replay")
    await session.broadcast({"type": "replay_started", "script_id": script["id"], "title": script.get("title")})
    try:
        for line in script["lines"]:
            if line["speaker"] == "caller":
                await session.add_turn("caller", line["text"], analyse=False)
                await _speak_line(session, line, voice)
                session.schedule_analysis()
            else:
                await asyncio.sleep(0.6 * pace)
                await session.add_turn("user", line["text"])
            if line.get("marker"):
                await session.broadcast({"type": "replay_marker", "marker": line["marker"], "n": line["n"]})
            if stop_at_marker and line.get("marker") == stop_at_marker:
                await session.broadcast({"type": "replay_paused", "marker": stop_at_marker, "payment_attempt": script.get("payment_attempt")})
                return
            await asyncio.sleep(max(0.4, 1.2 * pace))
        await session.run_analysis()
        await session.broadcast({"type": "replay_finished", "script_id": script["id"], "payment_attempt": script.get("payment_attempt")})
    except asyncio.CancelledError:
        await session.broadcast({"type": "replay_stopped"})
        raise
    finally:
        _running.pop(session.id, None)


def start_replay(session, script: dict, voice: bool = True, pace: float = 1.0, stop_at_marker: str | None = "payment_demand") -> None:
    stop_replay(session.id)
    pay = script.get("payment_attempt")
    if pay and settings.llm_enabled():
        from .payment import prewarm_for  # late import to avoid a cycle

        asyncio.create_task(prewarm_for(session, float(pay["amount_inr"])))
    _running[session.id] = asyncio.create_task(_run(session, script, voice, pace, stop_at_marker))
