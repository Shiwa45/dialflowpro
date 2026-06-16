"""
One-time LiveKit setup: inbound SIP trunk + dispatch rule that routes AI calls
to the DialFlow AI agent.

Run once against your LiveKit deployment (cloud or self-hosted — same script,
env decides the target):

    python scripts/livekit_sip_setup.py

It creates:
  * an inbound SIP trunk (accepts calls bridged from FreeSWITCH),
  * an individual dispatch rule: one room per call, prefixed `ai-call-`,
    dispatching the `dialflow-ai` agent, and passing agent_id + tenant_schema
    as job metadata.

How agent_id / tenant_schema get set: your FreeSWITCH dialplan adds SIP headers
(X-Agent-Id, X-Tenant-Schema) when bridging to LiveKit; the dispatch rule maps
them into participant attributes / job metadata. See dialplan_ai_bridge.xml.
"""
import asyncio
import os

from dotenv import load_dotenv
from livekit import api

load_dotenv()

AGENT_NAME = os.getenv("AI_AGENT_DISPATCH_NAME", "dialflow-ai")


async def main():
    lk = api.LiveKitAPI(
        url=os.environ["LIVEKIT_URL"],
        api_key=os.environ["LIVEKIT_API_KEY"],
        api_secret=os.environ["LIVEKIT_API_SECRET"],
    )

    # 1) Inbound trunk — accepts calls from your FreeSWITCH gateway.
    #    headers_to_attributes maps the X-* SIP headers the FreeSWITCH dialplan
    #    sets (see dialflow.lua route_to_ai / dialplan_ai_bridge.xml) onto the
    #    SIP participant attributes the worker reads (main.py _extract_call_meta).
    trunk = await lk.sip.create_sip_inbound_trunk(
        api.CreateSIPInboundTrunkRequest(
            trunk=api.SIPInboundTrunkInfo(
                name="dialflow-fs-inbound",
                # Lock down to your FreeSWITCH IP in production:
                allowed_addresses=[os.getenv("FS_PUBLIC_IP", "0.0.0.0/0")],
                headers_to_attributes={
                    "X-Agent-Id": "agent_id",
                    "X-Tenant-Schema": "tenant_schema",
                    "X-Caller-Number": "sip.phoneNumber",
                },
            )
        )
    )
    print("Created inbound trunk:", trunk.sip_trunk_id)

    # 2) Dispatch rule — one room per call, dispatch the AI agent.
    rule = await lk.sip.create_sip_dispatch_rule(
        api.CreateSIPDispatchRuleRequest(
            name="dialflow-ai-dispatch",
            trunk_ids=[trunk.sip_trunk_id],
            rule=api.SIPDispatchRule(
                dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                    room_prefix="ai-call-",
                )
            ),
            room_config=api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(
                    agent_name=AGENT_NAME,
                    # metadata is overridable per-call via SIP headers mapping;
                    # this is the default shape the worker expects.
                    metadata='{"agent_id":"","tenant_schema":""}',
                )]
            ),
        )
    )
    print("Created dispatch rule:", rule.sip_dispatch_rule_id)
    await lk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
