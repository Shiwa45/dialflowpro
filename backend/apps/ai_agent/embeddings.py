"""
Pluggable embedding providers for the AI knowledge base.

Selected by settings.AI_EMBEDDING_PROVIDER (env AI_EMBEDDING_PROVIDER):
    "sarvam"  -> Sarvam embeddings API
    "gemini"  -> Google Gemini embeddings
    "local"   -> sentence-transformers (no external API; CPU friendly)
    "none"    -> embeddings disabled (retriever falls back to lexical match)

This module is imported by tasks.embed_text so the rest of the codebase never
needs to know which provider is active. All providers return list[float].
Swapping providers is an env change + reindex, no code change.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def _provider() -> str:
    return (getattr(settings, "AI_EMBEDDING_PROVIDER", "none") or "none").lower()


def embedding_dimensions() -> Optional[int]:
    """Best-effort dimension hint (used only for diagnostics)."""
    return {
        "local": 384,        # all-MiniLM-L6-v2
        "gemini": 768,       # text-embedding-004
        "sarvam": 1024,      # provider-defined
    }.get(_provider())


# --------------------------------------------------------------------------- #
#  Local (sentence-transformers)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _local_model():
    from sentence_transformers import SentenceTransformer
    name = getattr(settings, "AI_LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    logger.info("Loading local embedding model %s", name)
    return SentenceTransformer(name)


def _embed_local(text: str) -> List[float]:
    model = _local_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


# --------------------------------------------------------------------------- #
#  Sarvam
# --------------------------------------------------------------------------- #
def _embed_sarvam(text: str) -> List[float]:
    import requests
    key = getattr(settings, "SARVAM_API_KEY", "")
    if not key:
        raise RuntimeError("SARVAM_API_KEY not set")
    resp = requests.post(
        "https://api.sarvam.ai/embeddings",
        headers={"api-subscription-key": key, "Content-Type": "application/json"},
        json={"inputs": [text]},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    # Sarvam returns embeddings under "embeddings" (list) — defensive parse.
    embs = data.get("embeddings") or data.get("data")
    if not embs:
        raise RuntimeError(f"Unexpected Sarvam embeddings response: {data}")
    first = embs[0]
    return first["embedding"] if isinstance(first, dict) else first


# --------------------------------------------------------------------------- #
#  Gemini
# --------------------------------------------------------------------------- #
def _embed_gemini(text: str) -> List[float]:
    import requests
    key = getattr(settings, "GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    model = getattr(settings, "AI_GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:embedContent?key={key}"
    )
    resp = requests.post(
        url,
        json={"model": f"models/{model}",
              "content": {"parts": [{"text": text}]}},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]["values"]


# --------------------------------------------------------------------------- #
#  Public entry
# --------------------------------------------------------------------------- #
def embed(text: str) -> List[float]:
    """Return an embedding for `text`, or raise if provider is 'none'/unset."""
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")
    p = _provider()
    if p == "local":
        return _embed_local(text)
    if p == "sarvam":
        return _embed_sarvam(text)
    if p == "gemini":
        return _embed_gemini(text)
    raise NotImplementedError("AI_EMBEDDING_PROVIDER is 'none' (lexical retrieval).")
