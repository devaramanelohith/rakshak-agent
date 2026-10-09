"""Thin wrapper around google-genai: one client, JSON helper with retries."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from google import genai
from google.genai import errors, types

from .config import settings

log = logging.getLogger("rakshak.llm")
_client: genai.Client | None = None
_live_client: genai.Client | None = None


def live_client() -> genai.Client:
    """Client for the Live API (transcribe-live, 3.8-live). The Live models are published under these ids on the
    Gemini API, so by default they use the AI Studio key even when text/TTS traffic goes through Vertex.
    Set RAKSHAK_LIVE_VIA_VERTEX=1 to route Live through Vertex as well (requires the Vertex Live model ids)."""
    global _live_client
    if _live_client is None:
        if settings.gemini_api_key and not settings.live_via_vertex:
            # vertexai=False is explicit: the SDK would otherwise honour GOOGLE_GENAI_USE_VERTEXAI from the env
            _live_client = genai.Client(api_key=settings.gemini_api_key, vertexai=False)
        else:
            _live_client = client()
    return _live_client


def client() -> genai.Client:
    global _client
    if _client is None:
        if settings.use_vertex:
            kwargs: dict[str, Any] = {}
            token = os.getenv("RAKSHAK_ACCESS_TOKEN")  # local dev without ADC: gcloud auth print-access-token
            if token:
                from google.oauth2.credentials import Credentials

                kwargs["credentials"] = Credentials(token=token)
            _client = genai.Client(vertexai=True, project=settings.project, location=settings.location, **kwargs)
        else:
            _client = genai.Client(api_key=settings.gemini_api_key, vertexai=False)
    return _client


async def generate_json(
    model: str,
    contents: Any,
    schema: dict,
    *,
    system: str | None = None,
    thinking: str = "low",
    retries: int = 2,
    timeout_s: float = 30.0,
) -> dict:
    """Call Gemini with a JSON schema and return the parsed object. Retries on 429/5xx."""
    cfg = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=schema,
        thinking_config=types.ThinkingConfig(thinking_level=thinking),
        system_instruction=system,
    )
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = await asyncio.wait_for(
                client().aio.models.generate_content(model=model, contents=contents, config=cfg),
                timeout=timeout_s,
            )
            return json.loads(resp.text)
        except (errors.APIError, asyncio.TimeoutError, json.JSONDecodeError) as e:  # pragma: no cover - network
            last = e
            code = getattr(e, "code", None)
            log.warning("generate_json %s attempt %d failed: %s", model, attempt, str(e)[:160])
            if isinstance(e, errors.APIError) and code not in (429, 500, 502, 503, 504):
                break
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Gemini call failed after retries: {last}")


async def generate_text(model: str, contents: Any, *, system: str | None = None, thinking: str = "low") -> str:
    cfg = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=thinking), system_instruction=system
    )
    resp = await client().aio.models.generate_content(model=model, contents=contents, config=cfg)
    return resp.text or ""
