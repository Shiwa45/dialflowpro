"""
Broadcast agent changes in real time.

Hooking post_save on Agent means the existing REST actions (`set_available`,
`set_on_break`, `set_logged_out`) and ANY other code path that saves an Agent
automatically pushes a WebSocket update — no need to touch the views.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Agent

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Agent)
def agent_saved(sender, instance: Agent, **kwargs):
    # Import here to avoid app-loading order issues.
    from .realtime import broadcast_agent_status, broadcast_dashboard_snapshot
    try:
        broadcast_agent_status(instance)
        broadcast_dashboard_snapshot()
    except Exception as exc:  # pragma: no cover
        logger.error("agent_saved broadcast failed: %s", exc)
