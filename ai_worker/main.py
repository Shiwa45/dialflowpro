"""
Worker entrypoint.

Run with:
    python -m ai_worker.main dev      # local dev
    python -m ai_worker.main start    # production

Dispatch model (per LiveKit docs): explicit agent dispatch for inbound SIP.
The SIP dispatch rule (see scripts/livekit_sip_setup.py) creates one room per
call, sets these attributes on the SIP participant, and dispatches this agent:

    sip.trunkPhoneNumber / sip.phoneNumber  -> caller's number
    agent_id (job metadata or attribute)    -> which AIAgent to run
    tenant_schema                            -> which tenant schema

The agent_id->config mapping is resolved here by calling Django. If the agent's
subscription quota is exhausted, we decline (LiveKit can route the caller to a
human fallback rule).
"""
from __future__ import annotations

import json
import logging

from livekit.agents import JobContext, WorkerOptions, cli

from .config import BackendClient, settings
from .agent import DialFlowAIAgent, build_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-worker.main")


def _extract_call_meta(ctx: JobContext, participant=None) -> dict:
    """
    Pull caller number, agent_id and tenant from job metadata and/or the SIP
    participant attributes. Job metadata (set by the dispatch rule) wins.
    """
    meta = {}
    if ctx.job and ctx.job.metadata:
        try:
            meta = json.loads(ctx.job.metadata)
        except Exception:
            meta = {}

    caller = meta.get("caller", "")
    agent_id = str(meta.get("agent_id", "") or "")
    tenant = meta.get("tenant_schema", "")

    # Fallback to SIP participant attributes if metadata was sparse.
    participants = list(ctx.room.remote_participants.values())
    if participant is not None and participant not in participants:
        participants.insert(0, participant)
    for p in participants:
        attrs = getattr(p, "attributes", {}) or {}
        caller = caller or attrs.get("sip.phoneNumber") or attrs.get("sip.trunkPhoneNumber", "")
        agent_id = agent_id or attrs.get("agent_id", "")
        tenant = tenant or attrs.get("tenant_schema", "")

    return {"caller": caller, "agent_id": agent_id, "tenant_schema": tenant}


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    backend = BackendClient(settings)

    # CRITICAL: at dispatch time the SIP participant has usually NOT joined the
    # room yet — its attributes (agent_id / tenant_schema, mapped from the
    # X-* SIP headers) only exist once it joins. Reading them immediately is a
    # race that aborts the agent and the call is never answered.
    participant = await ctx.wait_for_participant()

    info = _extract_call_meta(ctx, participant)
    logger.info("call meta: %s room=%s", info, ctx.room.name)

    if not info["agent_id"] or not info["tenant_schema"]:
        logger.error("missing agent_id/tenant_schema; cannot run AI agent")
        return

    try:
        cfg = backend.get_agent_config(
            agent_id=info["agent_id"], tenant_schema=info["tenant_schema"]
        )
    except Exception as exc:
        logger.error("failed to fetch agent config: %s", exc)
        return

    if not cfg.get("quota_ok", True):
        logger.warning("AI quota exhausted for tenant %s; declining",
                       info["tenant_schema"])
        # Leaving the room lets a LiveKit fallback rule route to a human.
        return

    agent = DialFlowAIAgent(
        cfg=cfg,
        tenant_schema=info["tenant_schema"],
        caller=info["caller"],
        call_uuid=ctx.room.name,
        room_name=ctx.room.name,
        backend=backend,
    )

    # Persist transcript + outcome no matter how the call ends.
    # (shutdown callbacks are awaited, so wrap the sync persist)
    async def _persist():
        agent.persist()
    ctx.add_shutdown_callback(_persist)

    session = build_session(cfg)

    # Enforce max call duration.
    max_secs = int(cfg.get("max_call_duration_seconds", 600))

    await session.start(agent=agent, room=ctx.room)

    # Hard cap on duration.
    import asyncio

    async def _guard():
        await asyncio.sleep(max_secs)
        logger.info("max call duration reached; ending %s", ctx.room.name)
        await ctx.room.disconnect()

    asyncio.create_task(_guard())


def run():
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name=settings.agent_name,
    ))


if __name__ == "__main__":
    run()
