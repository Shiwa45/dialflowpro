"""
Supervisor live-monitoring over FreeSWITCH ESL.

Uses mod_dptools `eavesdrop` for listen / whisper / barge and a channel
`intercept` for full takeover. The supervisor's own extension is bridged into
the target leg, so the supervisor must be registered on a softphone too.

Modes
-----
listen    Supervisor hears both legs, is muted to them.            (default eavesdrop)
whisper   Supervisor hears both legs, speaks only to the AGENT.    (eavesdrop + dtmf '2')
barge     Supervisor joins as a 3-way conference (all hear all).   (eavesdrop + dtmf '3')
takeover  Supervisor replaces the agent on the customer leg.       (intercept)

All commands are issued via the existing inbound ESL connection from
apps.dialer_cdr.esl.get_esl_connection.
"""
from __future__ import annotations

import logging
from typing import Optional

from apps.dialer_cdr.esl import get_esl_connection

logger = logging.getLogger(__name__)


def _api(command: str, node: str = "fs1") -> tuple[bool, str]:
    conn = get_esl_connection(node)
    if not conn:
        return False, "No ESL connection"
    try:
        resp = conn.send(f"api {command}")
        text = str(getattr(resp, "data", resp) or "")
        ok = "-ERR" not in text and "error" not in text.lower()
        return ok, text.strip()
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error("ESL api failed (%s): %s", command, exc)
        return False, str(exc)


def start_monitor(
    *,
    agent_uuid: str,
    supervisor_ext: str,
    mode: str = "listen",
    node: str = "fs1",
) -> tuple[bool, str]:
    """
    Originate a call to the supervisor's extension and, once answered,
    eavesdrop on `agent_uuid`.

    `agent_uuid` is the FreeSWITCH UUID of the AGENT's channel (the leg we want
    to monitor). We originate the supervisor leg with an execute-on-answer that
    runs eavesdrop, so no second round-trip is needed.

    Returns (ok, job_uuid_or_error).
    """
    dtmf = {"listen": "", "whisper": "w2", "barge": "w3"}.get(mode, "")
    # eavesdrop flags: read both, but only let supervisor talk per mode
    eaves_vars = "eavesdrop_enable_dtmf=true"
    if mode == "listen":
        eaves_vars += ",eavesdrop_bridge_aleg=false,eavesdrop_bridge_bleg=false"

    onanswer = f"'eavesdrop:{agent_uuid}'"
    cmd = (
        f"originate "
        f"{{origination_caller_id_name='Supervisor',{eaves_vars}}}"
        f"user/{supervisor_ext} "
        f"&{onanswer}"
    )
    ok, resp = _api(cmd, node)
    if ok and dtmf:
        # Switch eavesdrop mode after a short connect; FS reads queued dtmf.
        for d in dtmf.replace("w", ""):
            _api(f"uuid_send_dtmf {agent_uuid} {d}", node)
    logger.info("start_monitor mode=%s agent_uuid=%s -> ok=%s", mode, agent_uuid, ok)
    return ok, resp


def stop_monitor(*, supervisor_uuid: str, node: str = "fs1") -> tuple[bool, str]:
    """Hang up the supervisor's monitoring leg."""
    return _api(f"uuid_kill {supervisor_uuid}", node)


def takeover_call(
    *,
    agent_uuid: str,
    supervisor_ext: str,
    node: str = "fs1",
) -> tuple[bool, str]:
    """
    Full takeover: originate the supervisor leg and `intercept` the agent's
    channel. intercept steals the *other* leg (the customer) and bridges it to
    the supervisor, dropping the agent. The agent's leg then hangs up.

    Returns (ok, response).
    """
    onanswer = f"'intercept:{agent_uuid}'"
    cmd = (
        f"originate "
        f"{{origination_caller_id_name='Supervisor-Takeover'}}"
        f"user/{supervisor_ext} "
        f"&{onanswer}"
    )
    ok, resp = _api(cmd, node)
    logger.info("takeover_call agent_uuid=%s by ext=%s -> ok=%s",
                agent_uuid, supervisor_ext, ok)
    return ok, resp
