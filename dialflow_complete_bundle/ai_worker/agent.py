"""
DialFlow AI voice agent.

One AgentSession per inbound call. Pipeline (all Sarvam for Indic quality):
    Sarvam STT (saaras:v3, telephony 8kHz, VAD/barge-in)
      -> RAG (retrieve product knowledge from Django)
      -> LLM (Sarvam or Gemini per agent config) with tools
      -> Sarvam TTS (bulbul:v3, mulaw for telephony)

Tools the model can call:
    transfer_to_human(reason)   -> SIP REFER / FreeSWITCH bridge to a human queue
    schedule_callback(when,note)-> writes an AICallback in Django

On shutdown the full transcript + outcome is persisted via the worker REST
surface, which also meters the tenant's AI minutes.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone as dt_timezone

from livekit.agents import Agent, function_tool, RunContext
from livekit.plugins import sarvam

from .config import BackendClient, settings
from .llm_adapter import build_llm

logger = logging.getLogger("ai-worker.agent")


def _telephony_tts(cfg: dict, api_key: str):
    """Bulbul v3 configured for narrowband telephony (mulaw / 8kHz)."""
    return sarvam.TTS(
        target_language_code=(cfg.get("language") or "hi-IN")
        if cfg.get("language") != "unknown" else "hi-IN",
        model=cfg.get("tts_model", "bulbul:v3"),
        speaker=cfg.get("tts_speaker", "anand"),
        pace=float(cfg.get("tts_pace", 1.0)),
        temperature=float(cfg.get("tts_temperature", 0.6)),
        speech_sample_rate=8000,
        output_audio_codec="mulaw",
        api_key=api_key,
        send_completion_event=True,
    )


def _telephony_stt(cfg: dict, api_key: str):
    """Saaras v3 for telephony with barge-in signals (per Sarvam best practice)."""
    lang = cfg.get("language", "hi-IN")
    if cfg.get("auto_detect_language"):
        lang = "unknown"
    return sarvam.STT(
        language=lang,
        model=cfg.get("stt_model", "saaras:v3"),
        mode=cfg.get("stt_mode", "transcribe"),
        api_key=api_key,
        # narrowband telephony
        sample_rate=8000,
        # snappy turn-taking + barge-in
        # (the plugin emits speech start/end; AgentSession uses turn_detection="stt")
        flush_signal=True,
    )


class DialFlowAIAgent(Agent):
    def __init__(self, *, cfg: dict, tenant_schema: str, caller: str,
                 call_uuid: str, room_name: str, backend: BackendClient):
        super().__init__(instructions=cfg.get("system_prompt", ""))
        self.cfg = cfg
        self.tenant_schema = tenant_schema
        self.caller = caller
        self.call_uuid = call_uuid
        self.room_name = room_name
        self.backend = backend
        self.started = time.time()
        self.transcript: list[dict] = []
        self.outcome = "resolved"
        self.transfer_reason = ""

    async def on_enter(self):
        greeting = self.cfg.get("greeting") or "Namaste!"
        await self.session.say(greeting, allow_interruptions=True)
        self._log("ai", greeting)

    # ---- RAG: inject product knowledge before each LLM turn ---- #
    async def on_user_turn_completed(self, turn_ctx, new_message):
        text = getattr(new_message, "text_content", None) or str(new_message)
        self._log("caller", text)
        try:
            snippets = self.backend.retrieve(
                agent_id=self.cfg["id"], tenant_schema=self.tenant_schema,
                query=text, top_k=4,
            )
            if snippets:
                turn_ctx.add_message(
                    role="system",
                    content="Relevant business knowledge:\n" + "\n".join(snippets),
                )
        except Exception as exc:
            logger.warning("retrieve failed: %s", exc)

    # ---- Tools ---- #
    @function_tool()
    async def transfer_to_human(self, ctx: RunContext, reason: str):
        """Transfer the call to a human agent when the caller asks for a human
        or the AI cannot help. `reason` is a short explanation."""
        if not self.cfg.get("allow_human_transfer"):
            return "Human transfer is not enabled for this line."
        self.outcome = "transferred"
        self.transfer_reason = reason[:200]
        # The actual SIP REFER / FreeSWITCH bridge is performed by the
        # transfer handler (see transfer.py); here we signal intent and speak.
        from .transfer import perform_transfer
        ok = await perform_transfer(
            room_name=self.room_name,
            queue_id=self.cfg.get("transfer_queue_id"),
        )
        if ok:
            await self.session.say("Main aapko ek agent se connect kar raha hoon. "
                                   "Kripya hold karein.")
            return "Transferring to a human agent now."
        # No human available -> offer callback if allowed
        if self.cfg.get("allow_callback"):
            self.outcome = "callback"
            await self.session.say("Abhi koi agent uplabdh nahi hai. "
                                   "Kya main aapke liye callback schedule karoon?")
            return "No human available; offered a callback."
        await self.session.say("Abhi koi agent uplabdh nahi hai. "
                               "Kripya baad mein call karein.")
        return "No human available and callback disabled."

    @function_tool()
    async def schedule_callback(self, ctx: RunContext, when: str, notes: str = ""):
        """Schedule a callback for the caller. `when` is the requested time
        (ISO 8601 if known, else a natural description)."""
        if not self.cfg.get("allow_callback"):
            return "Callbacks are not enabled."
        requested_for = when
        # Best-effort: if not ISO, leave server to default to now.
        try:
            datetime.fromisoformat(when)
        except Exception:
            requested_for = None
        try:
            self.backend.schedule_callback(
                tenant_schema=self.tenant_schema,
                payload={
                    "agent_id": self.cfg["id"],
                    "call_uuid": self.call_uuid,
                    "caller_number": self.caller,
                    "requested_for": requested_for,
                    "notes": notes[:500],
                },
            )
            self.outcome = "callback"
            await self.session.say("Theek hai, maine aapka callback schedule kar diya hai. Dhanyavaad!")
            return "Callback scheduled."
        except Exception as exc:
            logger.error("callback failed: %s", exc)
            return "Could not schedule the callback right now."

    # ---- helpers ---- #
    def _log(self, role: str, text: str, language: str = "", confidence=None):
        self.transcript.append({
            "role": role, "text": text, "language": language,
            "confidence": confidence,
            "started_at": datetime.now(dt_timezone.utc).isoformat(),
        })

    def persist(self):
        duration = int(time.time() - self.started)
        try:
            self.backend.save_result(
                tenant_schema=self.tenant_schema,
                payload={
                    "agent_id": self.cfg["id"],
                    "call_uuid": self.call_uuid,
                    "livekit_room": self.room_name,
                    "caller_number": self.caller,
                    "started_at": datetime.fromtimestamp(self.started, dt_timezone.utc).isoformat(),
                    "ended_at": datetime.now(dt_timezone.utc).isoformat(),
                    "duration_seconds": duration,
                    "outcome": self.outcome,
                    "detected_language": self.cfg.get("language", ""),
                    "transfer_reason": self.transfer_reason,
                    "turns": self.transcript,
                },
            )
            logger.info("persisted call %s (%ss, %s)", self.call_uuid, duration, self.outcome)
        except Exception as exc:
            logger.error("persist failed: %s", exc)


def build_session(cfg: dict):
    """Assemble the AgentSession with Sarvam best-practice turn-taking."""
    from livekit.agents import AgentSession
    return AgentSession(
        stt=_telephony_stt(cfg, settings.sarvam_api_key),
        llm=build_llm(cfg, sarvam_api_key=settings.sarvam_api_key,
                      gemini_api_key=settings.gemini_api_key),
        tts=_telephony_tts(cfg, settings.sarvam_api_key),
        turn_detection="stt",           # Sarvam plugin handles turns
        min_endpointing_delay=0.07,     # ~70ms Sarvam STT latency
    )
