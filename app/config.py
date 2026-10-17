"""Runtime settings for Rakshak. Everything is driven by environment variables so the
same container runs locally (AI Studio key) and on Cloud Run (Agent Platform / Vertex)."""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


class Settings(BaseModel):
    # --- Gemini access -------------------------------------------------------
    gemini_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    use_vertex: bool = Field(default_factory=lambda: _env_bool("GOOGLE_GENAI_USE_VERTEXAI"))
    project: str | None = Field(default_factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT"))
    location: str = Field(default_factory=lambda: os.getenv("GOOGLE_CLOUD_LOCATION", "global"))  # model location; Cloud Run region is separate
    live_via_vertex: bool = Field(default_factory=lambda: _env_bool("RAKSHAK_LIVE_VIA_VERTEX"))
    fake_llm: bool = Field(default_factory=lambda: _env_bool("RAKSHAK_FAKE_LLM"))

    # --- Models (verified against the Gemini API on 2026-10-10) ---------------
    model_rubric: str = Field(default_factory=lambda: os.getenv("RAKSHAK_MODEL_RUBRIC", "gemini-3.5-flash"))
    model_agent: str = Field(default_factory=lambda: os.getenv("RAKSHAK_MODEL_AGENT", "gemini-3.8-flash"))
    model_agent_fallback: str = Field(default_factory=lambda: os.getenv("RAKSHAK_MODEL_AGENT_FALLBACK", "gemini-3.5-flash"))
    model_narrative: str = Field(default_factory=lambda: os.getenv("RAKSHAK_MODEL_NARRATIVE", "gemini-3.8-flash"))
    model_transcribe_live: str = Field(
        default_factory=lambda: os.getenv("RAKSHAK_MODEL_TRANSCRIBE_LIVE", "gemini-3.5-transcribe-live")
    )
    model_audio_batch: str = Field(default_factory=lambda: os.getenv("RAKSHAK_MODEL_AUDIO_BATCH", "gemini-3.8-flash"))
    model_tts: str = Field(default_factory=lambda: os.getenv("RAKSHAK_MODEL_TTS", "gemini-3.8-flash-tts"))
    model_live: str = Field(default_factory=lambda: os.getenv("RAKSHAK_MODEL_LIVE", "gemini-3.8-live"))
    tts_voice_guardian: str = Field(default_factory=lambda: os.getenv("RAKSHAK_TTS_VOICE", "Kore"))
    tts_voice_caller: str = Field(default_factory=lambda: os.getenv("RAKSHAK_TTS_VOICE_CALLER", "Charon"))

    # --- Behaviour ------------------------------------------------------------
    analysis_debounce_s: float = 1.2
    analysis_min_interval_s: float = 3.0
    warn_threshold: float = 0.45
    hold_threshold: float = 0.70
    whisper_threshold: float = 0.85
    hold_minutes: int = Field(default_factory=lambda: int(os.getenv("RAKSHAK_HOLD_MINUTES", "30")))
    carryover_minutes: int = Field(default_factory=lambda: int(os.getenv("RAKSHAK_CARRYOVER_MINUTES", "60")))
    agent_timeout_s: float = Field(default_factory=lambda: float(os.getenv("RAKSHAK_AGENT_TIMEOUT_S", "35")))
    agent_sync_wait_s: float = Field(default_factory=lambda: float(os.getenv("RAKSHAK_AGENT_SYNC_WAIT_S", "6")))
    rubric_thinking: str = Field(default_factory=lambda: os.getenv("RAKSHAK_RUBRIC_THINKING", "minimal"))
    agent_thinking: str = Field(default_factory=lambda: os.getenv("RAKSHAK_AGENT_THINKING", "low"))
    retain_audio: bool = Field(default_factory=lambda: _env_bool("RAKSHAK_RETAIN_AUDIO"))

    # --- Google Cloud data services (all optional; local fallbacks exist) -----
    bigquery_payee_table: str | None = Field(default_factory=lambda: os.getenv("BIGQUERY_PAYEE_TABLE"))
    use_firestore: bool = Field(default_factory=lambda: _env_bool("USE_FIRESTORE"))
    firestore_collection_prefix: str = Field(default_factory=lambda: os.getenv("FIRESTORE_PREFIX", "rakshak"))
    pubsub_topic: str | None = Field(default_factory=lambda: os.getenv("PUBSUB_ALERT_TOPIC"))
    ledger_enabled: bool = Field(default_factory=lambda: _env_bool("RAKSHAK_LEDGER", True))
    bigquery_ledger_table: str | None = Field(default_factory=lambda: os.getenv("BIGQUERY_LEDGER_TABLE"))
    pubsub_ledger_topic: str | None = Field(default_factory=lambda: os.getenv("PUBSUB_LEDGER_TOPIC"))

    # --- Telephony bridge (optional) -----------------------------------------
    twilio_account_sid: str | None = Field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID"))
    twilio_auth_token: str | None = Field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN"))
    twilio_from_number: str | None = Field(default_factory=lambda: os.getenv("TWILIO_FROM_NUMBER"))
    twilio_dial_number: str | None = Field(default_factory=lambda: os.getenv("TWILIO_DIAL_NUMBER"))
    public_base_url: str | None = Field(default_factory=lambda: os.getenv("PUBLIC_BASE_URL"))

    # --- Paths ----------------------------------------------------------------
    data_dir: Path = ROOT / "data"
    runtime_dir: Path = ROOT / "data" / "runtime"
    tts_cache_dir: Path = ROOT / "data" / "tts_cache"
    web_dir: Path = ROOT / "web"

    def llm_enabled(self) -> bool:
        return not self.fake_llm and (self.use_vertex or bool(self.gemini_api_key))

    def live_enabled(self) -> bool:
        return self.llm_enabled() and (bool(self.gemini_api_key) or self.live_via_vertex)


settings = Settings()


def configure_env() -> None:
    """Make the google-genai client and ADK pick up the same credentials."""
    if settings.gemini_api_key and not settings.use_vertex:
        os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
        os.environ.pop("GEMINI_API_KEY", None)  # genai warns when both are set
    if settings.use_vertex:
        # ADK + genai must not fall back to the API key when Vertex is selected
        os.environ.pop("GOOGLE_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
        if settings.project:
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", settings.project)
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", settings.location)
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    settings.tts_cache_dir.mkdir(parents=True, exist_ok=True)
