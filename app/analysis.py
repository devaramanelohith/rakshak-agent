"""Call understanding: live transcription (Gemini Live API) and the coercion rubric (Gemini JSON).

Two transcription paths:
  * LiveTranscriber  - streams 16 kHz PCM to `gemini-3.5-transcribe-live`; one session per speaker so the
                       transcript is labelled without diarization guesswork.
  * analyze_audio_window - batch fallback: a WAV window to `gemini-3.8-flash` returns transcript + rubric.
A keyword stub (RAKSHAK_FAKE_LLM=1) keeps tests and offline demos deterministic.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Awaitable, Callable

from google.genai import types
from pydantic import BaseModel, Field

from .config import settings
from .llm import generate_json, live_client

log = logging.getLogger("rakshak.analysis")

SIGNALS = [
    "authority_impersonation",
    "secrecy",
    "urgency",
    "remote_app_install",
    "safe_account",
    "investment_pressure",
    "otp_or_credential_request",
    "threat_of_arrest_or_harm",
]
SCAM_TYPES = [
    "none", "digital_arrest", "investment", "job_task", "kyc_otp", "lottery",
    "family_emergency", "loan_app", "sg_official_impersonation", "other",
]
STAGES = ["rapport", "authority_claim", "threat", "isolation", "payment_demand", "post_payment", "benign"]


class Rubric(BaseModel):
    language: str = "unknown"
    scam_type: str = "none"
    stage: str = "benign"
    signals: dict[str, bool] = Field(default_factory=lambda: {k: False for k in SIGNALS})
    risk_score: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    reasons_user_language: list[str] = Field(default_factory=list)
    summary: str = ""
    analysed_turns: int = 0
    latency_ms: int = 0
    source: str = "gemini"

    @property
    def signal_count(self) -> int:
        return sum(1 for v in self.signals.values() if v)


RUBRIC_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "description": "BCP-47-ish code of the user's language: hi, en, en-sg, kn, ta, hinglish"},
        "scam_type": {"type": "string", "enum": SCAM_TYPES},
        "stage": {"type": "string", "enum": STAGES},
        "signals": {
            "type": "object",
            "properties": {k: {"type": "boolean"} for k in SIGNALS},
            "required": SIGNALS,
        },
        "risk_score": {"type": "number", "description": "0 = clearly benign, 1 = certain scam"},
        "reasons": {"type": "array", "items": {"type": "string"}, "description": "<= 4 short reasons in English"},
        "reasons_user_language": {"type": "array", "items": {"type": "string"}, "description": "the same reasons, in the user's language and script"},
        "summary": {"type": "string", "description": "one sentence: what the caller wants"},
    },
    "required": ["language", "scam_type", "stage", "signals", "risk_score", "reasons", "reasons_user_language", "summary"],
}

RUBRIC_SYSTEM = """You are Rakshak, a bank's real-time scam analyst listening (with the customer's consent) to a phone call.
You see the transcript so far, labelled 'caller:' (the other party) and 'user:' (the bank's customer).
Score the call against these signals, true only when the CALLER does it:
- authority_impersonation: claims to be police/CBI/ED/customs/TRAI/RBI/MAS/bank official/courier authority.
- threat_of_arrest_or_harm: arrest warrant, account freeze, legal case, harm to family.
- secrecy: tells the user not to tell anyone / not to hang up / 'confidential', 'national security'.
- urgency: must act now, minutes, 'before the warrant is issued', 'offer closes'.
- remote_app_install: asks to install AnyDesk/TeamViewer/screen share/APK or to stay on video call.
- safe_account: asks to move money to a 'safe'/'RBI'/'verification'/'escrow' account, promises refund after 'verification', or asks for a 'tax'/'fee' to release winnings.
- investment_pressure: guaranteed returns, VIP tips, 'deposit more to withdraw'.
- otp_or_credential_request: asks for OTP, PIN, card number, password, UPI PIN.
Benign calls may still be urgent or about money (a daughter needing fees, a landlord, a real bank RM who never asks for OTP). Do NOT mark those as scams: urgency alone is weak evidence; authority + secrecy + safe_account is decisive.
risk_score guidance: 0.0-0.2 ordinary call; 0.3-0.5 one weak signal; 0.6-0.8 two strong signals; 0.85-1.0 the digital-arrest / safe-account pattern or OTP request.
reasons_user_language must be in the user's own language and script (Hindi in Devanagari, Kannada, Tamil, or English), short, and suitable to show on a phone screen.
If the transcript is empty or only greetings, return stage 'rapport', scam_type 'none', risk_score <= 0.1."""


def format_turns(turns: list[dict], limit_chars: int = 6000) -> str:
    lines = [f"{t['speaker']}: {t['text']}" for t in turns if t.get("text")]
    text = "\n".join(lines)
    return text[-limit_chars:]


# --- keyword stub (offline / tests) ------------------------------------------------------------
_KW = {
    "authority_impersonation": r"cbi|police|ed\b|enforcement|customs|trai|rbi|narcotics|inspector|officer|mas\b|ministry|पुलिस|सीबीआई|इंस्पेक्टर|अधिकारी|आरबीआई|कस्टम",
    "threat_of_arrest_or_harm": r"arrest|warrant|jail|freeze|legal case|fir\b|गिरफ्तार|वारंट|जेल|फ्रीज|केस",
    "secrecy": r"don't tell|do not tell|tell no one|confidential|secret|national security|किसी को मत बता|गुप्त|राष्ट्रीय सुरक्षा",
    "urgency": r"immediately|right now|within|minutes|urgent|abhi|turant|अभी|तुरंत|जल्दी",
    "remote_app_install": r"anydesk|teamviewer|screen share|install|apk|video call|skype|एनीडेस्क|इंस्टॉल",
    "safe_account": r"safe account|rbi account|verification account|escrow|refund|tax.*withdraw|सेफ अकाउंट|सुरक्षित खाते|वापस मिल",
    "investment_pressure": r"guaranteed|returns|profit|vip|tips|trading|invest|crypto|गारंटी|मुनाफा|निवेश",
    "otp_or_credential_request": r"\botp\b|\bpin\b|password|cvv|card number|ओटीपी|पिन|पासवर्ड",
}


def stub_rubric(turns: list[dict]) -> Rubric:
    caller_text = " ".join(t["text"].lower() for t in turns if t.get("speaker") == "caller")
    signals = {k: bool(re.search(p, caller_text)) for k, p in _KW.items()}
    strong = sum(signals[k] for k in ("authority_impersonation", "safe_account", "otp_or_credential_request", "threat_of_arrest_or_harm", "secrecy", "remote_app_install", "investment_pressure"))
    weak = int(signals["urgency"])
    risk = min(1.0, 0.3 * strong + 0.1 * weak)
    if signals["safe_account"] or signals["otp_or_credential_request"]:
        risk = max(risk, 0.85)
    scam = "none"
    if signals["authority_impersonation"] and (signals["safe_account"] or signals["threat_of_arrest_or_harm"]):
        scam = "digital_arrest"
    elif signals["investment_pressure"]:
        scam = "investment"
    elif signals["otp_or_credential_request"]:
        scam = "kyc_otp"
    stage = "payment_demand" if signals["safe_account"] else ("threat" if signals["threat_of_arrest_or_harm"] else ("benign" if risk < 0.3 else "authority_claim"))
    reasons = [k.replace("_", " ") for k, v in signals.items() if v][:4]
    return Rubric(language="unknown", scam_type=scam, stage=stage, signals=signals, risk_score=round(risk, 2),
                  reasons=reasons, reasons_user_language=reasons, summary="stub analysis", analysed_turns=len(turns), source="stub")


# --- Gemini rubric ------------------------------------------------------------------------------
async def analyze_transcript(turns: list[dict], profile: dict | None = None) -> Rubric:
    t0 = time.time()
    if not settings.llm_enabled():
        r = stub_rubric(turns)
        r.latency_ms = int((time.time() - t0) * 1000)
        return r
    profile = profile or {}
    user_ctx = f"Customer profile: age band {profile.get('age_band', 'unknown')}, preferred language {profile.get('language', 'unknown')}."
    prompt = f"{user_ctx}\n\nTranscript so far:\n{format_turns(turns) or '(no speech yet)'}"
    data = await generate_json(settings.model_rubric, prompt, RUBRIC_SCHEMA, system=RUBRIC_SYSTEM, thinking=settings.rubric_thinking, timeout_s=25)
    data["signals"] = {k: bool(data.get("signals", {}).get(k, False)) for k in SIGNALS}
    data["risk_score"] = max(0.0, min(1.0, float(data.get("risk_score", 0))))
    r = Rubric(**{k: v for k, v in data.items() if k in Rubric.model_fields})
    r.analysed_turns = len(turns)
    r.latency_ms = int((time.time() - t0) * 1000)
    return r


AUDIO_WINDOW_SCHEMA = {
    "type": "object",
    "properties": {
        "utterances": {"type": "array", "items": {"type": "object", "properties": {
            "speaker": {"type": "string", "enum": ["caller", "user"]}, "text": {"type": "string"}}, "required": ["speaker", "text"]}},
    },
    "required": ["utterances"],
}


async def transcribe_audio_window(wav: bytes, prior_transcript: str, speaker_hint: str | None = None) -> list[dict]:
    """Batch fallback: transcribe a short WAV window (both parties mixed) into labelled utterances."""
    if not settings.llm_enabled():
        return []
    hint = f"All speech in this window is the '{speaker_hint}'." if speaker_hint else "Label each utterance 'caller' (the other party) or 'user' (the bank customer)."
    prompt = (
        "Transcribe this phone-call audio verbatim in the spoken script. " + hint +
        " Use the earlier transcript only for context, do not repeat it.\nEarlier transcript:\n" + (prior_transcript[-1500:] or "(none)")
    )
    data = await generate_json(settings.model_audio_batch,
                               [types.Part.from_bytes(data=wav, mime_type="audio/wav"), prompt],
                               AUDIO_WINDOW_SCHEMA, thinking="low", timeout_s=40)
    return [u for u in data.get("utterances", []) if u.get("text")]


# --- Live transcription ---------------------------------------------------------------------
class LiveTranscriber:
    """One Gemini Live transcription session per speaker. feed() takes 16 kHz mono PCM16."""

    def __init__(self, role: str, on_text: Callable[[str, str], Awaitable[None]], language_hint: str | None = None):
        self.role = role
        self.on_text = on_text
        self.language_hint = language_hint
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self._stopped = False
        self.connected = False
        self.errors = 0

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name=f"transcriber-{self.role}")

    async def feed(self, pcm16k: bytes) -> None:
        if not self._stopped:
            await self._queue.put(pcm16k)

    async def stop(self) -> None:
        self._stopped = True
        await self._queue.put(None)
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except Exception:
                self._task.cancel()

    async def _run(self) -> None:
        backoff = 1.0
        while not self._stopped:
            try:
                await self._session()
                backoff = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as e:  # pragma: no cover - network
                self.errors += 1
                self.connected = False
                log.warning("transcriber[%s] error: %s", self.role, str(e)[:200])
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 10)

    async def _session(self) -> None:
        cfg = types.LiveConnectConfig(response_modalities=["TEXT"])
        if self.language_hint:
            cfg.input_audio_transcription = types.AudioTranscriptionConfig(language_hints=[self.language_hint])
        async with live_client().aio.live.connect(model=settings.model_transcribe_live, config=cfg) as session:
            self.connected = True
            log.info("transcriber[%s] connected", self.role)

            async def sender():
                while True:
                    chunk = await self._queue.get()
                    if chunk is None:
                        await session.send_realtime_input(audio_stream_end=True)
                        return
                    await session.send_realtime_input(audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000"))

            send_task = asyncio.create_task(sender())
            try:
                # receive() returns after each complete turn; keep the session open across utterances.
                while not (self._stopped and send_task.done()):
                    async for msg in session.receive():
                        sc = msg.server_content
                        if sc and sc.input_transcription and sc.input_transcription.text:
                            text = sc.input_transcription.text.strip()
                            if text:
                                await self.on_text(self.role, text)
                        if self._stopped and send_task.done():
                            break
            finally:
                if not send_task.done():
                    send_task.cancel()
