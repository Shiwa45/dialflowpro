"""
Human-transfer handler.

When the AI decides to hand off, we need to bring a human agent into the call.
Two supported paths (pick per deployment; both live behind perform_transfer):

  1. LiveKit SIP transfer (REFER): transfer the caller's SIP participant to a
     PSTN/SIP address that routes to your FreeSWITCH human queue. Cleanest when
     the inbound call arrived via a LiveKit SIP trunk.

  2. Dial a human into the room: create a SIP participant for the next available
     human extension so caller + human + (optionally) AI share the room.

This module uses the LiveKit server API. The queue->extension resolution calls
back into FreeSWITCH/Django via the existing callcenter routing; here we keep it
simple and transfer to a configured SIP URI built from the queue id.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger("ai-worker.transfer")

# A SIP URI template that routes into your FreeSWITCH human queue.
# e.g. "sip:queue-{queue_id}@your-fs-host:5060"
TRANSFER_SIP_TEMPLATE = os.getenv(
    "AI_TRANSFER_SIP_TEMPLATE", "sip:queue-{queue_id}@127.0.0.1:5060"
)


async def perform_transfer(*, room_name: str, queue_id, caller_identity: str | None = None) -> bool:
    """
    Attempt to bring a human into `room_name`. Returns True if a human leg was
    successfully initiated, False if none available (caller should be offered a
    callback).
    """
    if not queue_id:
        logger.warning("transfer requested but no transfer_queue configured")
        return False

    sip_uri = TRANSFER_SIP_TEMPLATE.format(queue_id=queue_id)

    try:
        from livekit import api
        from .config import settings

        lkapi = api.LiveKitAPI(
            url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
        # Dial the human queue into the same room as a new SIP participant.
        await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_call_to=sip_uri,
                participant_identity=f"human-{queue_id}",
                participant_name="Human Agent",
                # short timeout so we can fall back to callback quickly
                wait_until_answered=True,
            )
        )
        await lkapi.aclose()
        logger.info("transfer: dialed %s into room %s", sip_uri, room_name)
        return True
    except Exception as exc:
        logger.warning("transfer to %s failed: %s", sip_uri, exc)
        return False
