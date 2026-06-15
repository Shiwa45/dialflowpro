"""
Test your AI agent in the browser (no phone/SIP needed).

It creates an explicit agent dispatch into a room and prints a join token +
the Playground URL. Run the worker first (`python -m ai_worker.main dev`),
then run this, then open the Playground and paste the token.

Usage (from the dialflow root, worker venv active):
    python -m ai_worker.scripts.playground_dispatch <agent_id> [tenant_schema]

    agent_id        the AIAgent id from the admin UI (AI Agents page)
    tenant_schema   defaults to "test_tenant"
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from livekit import api

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

AGENT_NAME = os.getenv("AI_AGENT_DISPATCH_NAME", "dialflow-ai")
ROOM = "ai-playground-test"


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m ai_worker.scripts.playground_dispatch <agent_id> [tenant_schema]")
        return
    agent_id = sys.argv[1]
    tenant = sys.argv[2] if len(sys.argv) > 2 else "test_tenant"

    lk = api.LiveKitAPI()
    metadata = json.dumps({"agent_id": agent_id, "tenant_schema": tenant})
    dispatch = await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=AGENT_NAME, room=ROOM, metadata=metadata,
        )
    )
    await lk.aclose()
    print("Dispatch created:", dispatch.id, "room:", ROOM, "metadata:", metadata)

    token = (
        api.AccessToken()
        .with_identity("playground-tester")
        .with_name("Tester")
        .with_grants(api.VideoGrants(room_join=True, room=ROOM))
        .to_jwt()
    )

    print("\n=== Open the Playground and connect with these ===")
    print("Playground:  https://agents-playground.livekit.io")
    print("LiveKit URL:", os.getenv("LIVEKIT_URL"))
    print("Token:\n" + token)


if __name__ == "__main__":
    asyncio.run(main())
