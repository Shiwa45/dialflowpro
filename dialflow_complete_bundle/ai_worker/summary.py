"""
Optional post-call summary + sentiment.

Called by the worker at shutdown (one extra LLM call) to fill AICallSession's
`summary` and `sentiment_score`. It's optional on purpose: it adds a little
latency/cost per call, so the worker only invokes it when
settings.AI_POST_CALL_SUMMARY is true. The review page renders these when
present and degrades gracefully when not.

This runs inside the worker process (not Django), reusing the same LLM the agent
used. It is provided here as a drop-in module the worker imports so the logic
lives next to the agent code.
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger("ai-worker.summary")

ENABLED = os.getenv("AI_POST_CALL_SUMMARY", "false").lower() in ("1", "true", "yes")

_PROMPT = (
    "You are reviewing a customer support phone call transcript. "
    "Return ONLY compact JSON: "
    '{"summary": "<=2 sentence summary", "sentiment": <float -1..1>}. '
    "Sentiment reflects the caller's overall mood (1 happy, -1 upset)."
)


async def summarize(transcript: list[dict], llm_cfg: dict,
                    *, sarvam_api_key: str, gemini_api_key: str) -> dict:
    """
    Returns {"summary": str, "sentiment": float} or {} on failure / disabled.
    `transcript` is the list of {role, text} turns; `llm_cfg` is the agent config
    dict (so we reuse its provider/model).
    """
    if not ENABLED or not transcript:
        return {}

    convo = "\n".join(
        f"{t.get('role', '?')}: {t.get('text', '')}" for t in transcript
        if t.get("role") in ("caller", "ai")
    )[:6000]

    try:
        provider = llm_cfg.get("llm_provider", "sarvam")
        model = llm_cfg.get("llm_model", "sarvam-30b")
        if provider == "gemini":
            text = await _gemini_complete(model, gemini_api_key, convo)
        else:
            text = await _sarvam_complete(model, sarvam_api_key, convo)
        data = _parse_json(text)
        return {
            "summary": str(data.get("summary", ""))[:1000],
            "sentiment": _clamp(data.get("sentiment")),
        }
    except Exception as exc:
        logger.warning("summary failed: %s", exc)
        return {}


def _clamp(v):
    try:
        f = float(v)
        return max(-1.0, min(1.0, f))
    except Exception:
        return None


def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    return {}


async def _sarvam_complete(model: str, key: str, convo: str) -> str:
    import httpx
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            "https://api.sarvam.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _PROMPT},
                    {"role": "user", "content": convo},
                ],
                "temperature": 0.2,
                "max_tokens": 200,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _gemini_complete(model: str, key: str, convo: str) -> str:
    import httpx
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(url, json={
            "contents": [{"parts": [{"text": _PROMPT + "\n\n" + convo}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200},
        })
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
