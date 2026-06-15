"""
Worker configuration + Django API client.

The worker is stack-agnostic about WHERE LiveKit runs: it reads LIVEKIT_URL /
keys from the environment, so the same binary points at LiveKit Cloud today and
your self-hosted server later — no code change (hybrid mode).

It pulls per-call agent configuration from the Django backend over the
worker REST surface (shared-secret auth), so all business config stays in one
place (the admin UI) and the worker stays a thin runtime.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # LiveKit (hybrid: cloud or self-hosted, decided purely by these values)
    livekit_url: str = os.getenv("LIVEKIT_URL", "")
    livekit_api_key: str = os.getenv("LIVEKIT_API_KEY", "")
    livekit_api_secret: str = os.getenv("LIVEKIT_API_SECRET", "")

    # Django backend
    backend_url: str = os.getenv("DIALFLOW_BACKEND_URL", "http://localhost:8000")
    worker_token: str = os.getenv("AI_WORKER_TOKEN", "")

    # Providers (the worker passes keys to the plugins / LLM adapter)
    sarvam_api_key: str = os.getenv("SARVAM_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Agent name this worker registers under (matches the SIP dispatch rule)
    agent_name: str = os.getenv("AI_AGENT_DISPATCH_NAME", "dialflow-ai")


settings = Settings()


class BackendClient:
    """Thin client over the Django worker REST surface."""

    def __init__(self, s: Settings = settings):
        self.s = s
        self._client = httpx.Client(
            base_url=s.backend_url.rstrip("/"),
            headers={"X-AI-Worker-Token": s.worker_token},
            timeout=15.0,
        )

    def get_agent_config(self, *, agent_id: str, tenant_schema: str) -> dict:
        r = self._client.get(
            "/api/ai/worker/config/",
            params={"agent_id": agent_id},
            headers={"X-Tenant": tenant_schema},
        )
        r.raise_for_status()
        return r.json()

    def retrieve(self, *, agent_id: int, tenant_schema: str, query: str, top_k: int = 4) -> list[str]:
        r = self._client.post(
            "/api/ai/worker/retrieve/",
            json={"agent_id": agent_id, "query": query, "top_k": top_k,
                  "tenant_schema": tenant_schema},
            headers={"X-Tenant": tenant_schema},
        )
        r.raise_for_status()
        return r.json().get("snippets", [])

    def save_result(self, *, tenant_schema: str, payload: dict) -> dict:
        payload["tenant_schema"] = tenant_schema
        r = self._client.post(
            "/api/ai/worker/result/", json=payload,
            headers={"X-Tenant": tenant_schema},
        )
        r.raise_for_status()
        return r.json()

    def schedule_callback(self, *, tenant_schema: str, payload: dict) -> dict:
        payload["tenant_schema"] = tenant_schema
        r = self._client.post(
            "/api/ai/worker/callback/", json=payload,
            headers={"X-Tenant": tenant_schema},
        )
        r.raise_for_status()
        return r.json()
