"""
LLM adapter — turns an agent's config into a LiveKit LLM instance.

Configurable per agent (the requirement): Sarvam or Gemini. Sarvam exposes an
OpenAI-compatible /chat/completions endpoint, so we use the LiveKit openai
plugin pointed at Sarvam's base_url. Gemini uses the google plugin.

Keeping this in one function means the rest of the worker is provider-agnostic;
both paths expose the same tool-calling interface to the AgentSession.
"""
from __future__ import annotations

import logging

# IMPORTANT: LiveKit plugins self-register on import and MUST be imported on
# the main thread (module load time). Importing them lazily inside build_llm
# raises "Plugins must be registered on the main thread" at call time.
from livekit.plugins import google, openai  # noqa: E402

logger = logging.getLogger("ai-worker.llm")

SARVAM_BASE_URL = "https://api.sarvam.ai/v1"


def build_llm(cfg: dict, *, sarvam_api_key: str, gemini_api_key: str):
    """
    cfg is the dict returned by /api/ai/worker/config/.
    Returns a LiveKit LLM plugin instance.
    """
    provider = cfg.get("llm_provider", "sarvam")
    model = cfg.get("llm_model", "sarvam-30b")
    temperature = float(cfg.get("temperature", 0.6))

    if provider == "gemini":
        logger.info("LLM: Gemini %s", model)
        return google.LLM(
            model=model,
            api_key=gemini_api_key,
            temperature=temperature,
        )

    # Sarvam via OpenAI-compatible endpoint.
    logger.info("LLM: Sarvam %s (OpenAI-compatible)", model)
    extra = {}
    if cfg.get("enable_thinking"):
        # Sarvam-M hybrid thinking maps to OpenAI-style reasoning_effort.
        extra["reasoning_effort"] = "medium"
    return openai.LLM(
        model=model,
        api_key=sarvam_api_key,
        base_url=SARVAM_BASE_URL,
        temperature=temperature,
        **extra,
    )
