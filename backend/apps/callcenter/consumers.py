"""
WebSocket consumers for real-time call center updates.
Fully bidirectional — agents receive live events AND send commands back.
"""
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import logging
import json

from django_tenants.utils import schema_context

def tenant_db_sync(func):
    def wrapper(self, *args, **kwargs):
        schema = getattr(self, 'tenant_name', 'public') or 'public'
        with schema_context(schema):
            return func(self, *args, **kwargs)
    return database_sync_to_async(wrapper)


logger = logging.getLogger(__name__)


class AgentStatusConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for agent status updates (broadcast to admin dashboards).

    Usage:
        ws://host/ws/callcenter/agents/

    Outbound events:
        agent_status  – agent changed status/state
        agent_list    – full agent list (sent on connect)
    """

    async def connect(self):
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)
        self.tenant_name = params.get('tenant')

        self.group_name = 'agent_status'
        await self.accept()
        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        except Exception as exc:
            logger.error(f"Channel layer unavailable: {exc}")
            await self.close(code=4500)
            return
        agents = await self._get_all_agents()
        await self.send_json({'type': 'agent_list', 'agents': agents})
        logger.info(f"Agent status WS connected: {self.channel_name}")

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def agent_status_update(self, event):
        await self.send_json({
            'type': 'agent_status',
            'agent_id': event['agent_id'],
            'agent_name': event['agent_name'],
            'status': event['status'],
            'status_display': event['status_display'],
            'state': event['state'],
            'calls_answered': event.get('calls_answered', 0),
            'talk_time': event.get('talk_time', 0),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        })

    @tenant_db_sync
    def _get_all_agents(self):
        from .models import Agent
        agents = Agent.objects.select_related('user').all()
        return [
            {
                'id': a.id,
                'name': a.name,
                'status': a.status,
                'status_display': a.get_status_display(),
                'state': a.state,
                'calls_answered': a.calls_answered,
                'talk_time': a.talk_time,
                'sip_extension': a.sip_extension,
            }
            for a in agents
        ]


class AgentDesktopConsumer(AsyncJsonWebsocketConsumer):
    """
    Bidirectional WebSocket for the Agent Desktop panel.
    Each agent gets their own channel for receiving calls and sending commands.

    Usage:
        ws://host/ws/callcenter/agent-desktop/

    Inbound commands (agent → server):
        { "action": "login" }
        { "action": "logout" }
        { "action": "set_status", "status": "available" | "on_break" }
        { "action": "answer_call", "call_id": "uuid" }
        { "action": "hangup_call", "call_id": "uuid" }
        { "action": "hold_call", "call_id": "uuid" }
        { "action": "resume_call", "call_id": "uuid" }
        { "action": "transfer_call", "call_id": "uuid", "target": "1002" }
        { "action": "send_dtmf", "call_id": "uuid", "digits": "123" }
        { "action": "set_disposition", "call_id": "uuid", "disposition": "sale" }
        { "action": "select_queue", "queue_id": 1 }
        { "action": "heartbeat" }

    Outbound events (server → agent):
        incoming_call   – new call routed to this agent
        call_answered   – call connected
        call_ended      – call hung up / completed
        call_held       – call placed on hold
        call_resumed    – call resumed from hold
        transfer_result – result of transfer attempt
        agent_state     – full agent state snapshot
        queue_stats     – queue metrics update
        campaign_lead   – predictive dialer lead info
        error           – error response
        pong            – heartbeat reply
    """

    async def connect(self):
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)
        self.tenant_name = params.get('tenant')

        # Authenticate agent from query params or scope user
        self.agent_id = None
        self.agent_group = None

        await self.accept()

        try:
            agent_data = await self._identify_agent()
        except Exception as exc:
            logger.exception(f"Error identifying agent: {exc}")
            await self.send_json({'type': 'error', 'message': 'Server error during authentication'})
            await self.close(code=4500)
            return

        if not agent_data:
            await self.send_json({
                'type': 'error',
                'message': 'Agent profile not found. Contact admin.',
            })
            await self.close(code=4001)
            return

        self.agent_id = agent_data['id']
        self.agent_group = f'agent_desktop_{self.agent_id}'

        # Join channel groups — requires Redis; close gracefully if unavailable
        try:
            await self.channel_layer.group_add(self.agent_group, self.channel_name)
            await self.channel_layer.group_add('agent_status', self.channel_name)
            await self.channel_layer.group_add('agent_calls', self.channel_name)
        except Exception as exc:
            logger.error(f"Channel layer unavailable (is Redis running?): {exc}")
            await self.send_json({'type': 'error', 'message': 'Server error: channel layer unavailable'})
            await self.close(code=4500)
            return

        # Mark presence — WebSocket is now connected
        try:
            await self._set_presence(True)
        except Exception as exc:
            logger.warning(f"Could not set presence for agent {self.agent_id}: {exc}")

        try:
            state = await self._get_agent_state()
            await self.send_json({'type': 'agent_state', **state})
        except Exception as exc:
            logger.exception(f"Error fetching initial agent state: {exc}")

        logger.info(f"Agent desktop WS connected: agent_id={self.agent_id}")

    async def disconnect(self, close_code):
        # Clear presence — WebSocket dropped, agent can no longer take calls
        if self.agent_id:
            try:
                await self._set_presence(False)
            except Exception:
                pass
        if self.agent_group:
            try:
                await self.channel_layer.group_discard(self.agent_group, self.channel_name)
                await self.channel_layer.group_discard('agent_status', self.channel_name)
                await self.channel_layer.group_discard('agent_calls', self.channel_name)
            except Exception:
                pass  # Redis may be gone during shutdown — best effort
        logger.info(f"Agent desktop WS disconnected: agent_id={self.agent_id}")

    async def receive_json(self, content):
        """Handle commands from the agent UI."""
        action = content.get('action', '')
        handler = getattr(self, f'_handle_{action}', None)

        if handler:
            try:
                await handler(content)
            except Exception as exc:
                logger.exception(f"Error handling action '{action}': {exc}")
                await self.send_json({
                    'type': 'error',
                    'action': action,
                    'message': str(exc),
                })
        else:
            await self.send_json({
                'type': 'error',
                'message': f'Unknown action: {action}',
            })

    # ── Inbound command handlers ──────────────────────────────

    async def _handle_heartbeat(self, content):
        # Refresh presence timestamp so the dialer knows this agent is alive
        try:
            await self._touch_heartbeat()
        except Exception:
            pass
        await self.send_json({'type': 'pong', 'ts': timezone.now().isoformat()})

    async def _handle_login(self, content):
        result = await self._set_agent_status('available')
        await self.send_json({'type': 'agent_state', **result})
        await self._broadcast_agent_update(result)

    async def _handle_logout(self, content):
        result = await self._set_agent_status('logged_out')
        await self.send_json({'type': 'agent_state', **result})
        await self._broadcast_agent_update(result)

    async def _handle_set_status(self, content):
        new_status = content.get('status', 'available')
        result = await self._set_agent_status(new_status)
        await self.send_json({'type': 'agent_state', **result})
        await self._broadcast_agent_update(result)

    async def _handle_answer_call(self, content):
        call_id = content.get('call_id')
        result = await self._answer_call(call_id)
        await self.send_json({'type': 'call_answered', **result})
        await self._broadcast_agent_update(await self._get_agent_state())

    async def _handle_hangup_call(self, content):
        call_id = content.get('call_id')
        disposition = content.get('disposition', '')
        result = await self._hangup_call(call_id, disposition)
        await self.send_json({'type': 'call_ended', **result})
        await self._broadcast_agent_update(await self._get_agent_state())

    async def _handle_hold_call(self, content):
        call_id = content.get('call_id')
        result = await self._hold_call(call_id)
        await self.send_json({'type': 'call_held', **result})

    async def _handle_resume_call(self, content):
        call_id = content.get('call_id')
        result = await self._resume_call(call_id)
        await self.send_json({'type': 'call_resumed', **result})

    async def _handle_transfer_call(self, content):
        call_id = content.get('call_id')
        target = content.get('target', '')
        result = await self._transfer_call(call_id, target)
        await self.send_json({'type': 'transfer_result', **result})

    async def _handle_send_dtmf(self, content):
        call_id = content.get('call_id')
        digits = content.get('digits', '')
        await self._send_dtmf(call_id, digits)
        await self.send_json({'type': 'dtmf_sent', 'call_id': call_id, 'digits': digits})

    async def _handle_set_disposition(self, content):
        call_id = content.get('call_id')
        disposition = content.get('disposition', '')
        notes = content.get('notes', '')
        await self._save_disposition(call_id, disposition, notes)
        await self.send_json({
            'type': 'disposition_saved',
            'call_id': call_id,
            'disposition': disposition,
        })

    async def _handle_select_queue(self, content):
        queue_id = content.get('queue_id')
        stats = await self._get_queue_stats(queue_id)
        await self.send_json({'type': 'queue_stats', **stats})

    async def _handle_make_call(self, content):
        """Click-to-dial: originate an outbound call from the agent's SIP extension."""
        destination = content.get('destination', '').strip()
        if not destination:
            await self.send_json({'type': 'error', 'message': 'No destination number provided'})
            return

        agent_ext = await self._get_agent_extension()
        if not agent_ext:
            await self.send_json({'type': 'error', 'message': 'Agent SIP extension not configured'})
            return

        try:
            from apps.dialer_cdr.esl import get_esl_connection
            from django.conf import settings
            import json

            fs_nodes = settings.FREESWITCH_NODES if isinstance(settings.FREESWITCH_NODES, dict) \
                else json.loads(settings.FREESWITCH_NODES)
            fs_host = list(fs_nodes.values())[0]['host']
            profile = getattr(settings, 'FS_SOFIA_PROFILE', 'internal')

            conn = get_esl_connection('fs1')
            if not conn:
                await self.send_json({'type': 'error', 'message': 'FreeSWITCH unavailable'})
                return

            # Call the agent's extension first; when answered, bridge to destination
            originate_cmd = (
                f'api originate '
                f'{{origination_caller_id_number={agent_ext},origination_caller_id_name=Dialflow}}'
                f'sofia/{profile}/{agent_ext}%{fs_host} '
                f'&bridge(sofia/{profile}/{destination}%{fs_host})'
            )
            conn.send(originate_cmd)
            await self.send_json({'type': 'outbound_initiated', 'destination': destination})
        except Exception as exc:
            logger.exception(f"make_call ESL error: {exc}")
            await self.send_json({'type': 'error', 'message': f'Call failed: {exc}'})

    # ── Outbound event handlers (from channel layer group_send) ──

    async def incoming_call(self, event):
        """New call routed to this agent by the dialer engine."""
        await self.send_json({
            'type': 'incoming_call',
            'call_id': event['call_id'],
            'caller_number': event['caller_number'],
            'caller_name': event.get('caller_name', ''),
            'queue_name': event.get('queue_name', ''),
            'campaign_name': event.get('campaign_name', ''),
            'lead': event.get('lead', {}),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        })

    async def call_answered(self, event):
        await self.send_json({'type': 'call_answered', **event})

    async def call_ended(self, event):
        await self.send_json({
            'type': 'call_ended',
            'call_id': event.get('call_id'),
            'duration': event.get('duration', 0),
            'hangup_cause': event.get('hangup_cause', ''),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        })

    async def campaign_lead(self, event):
        """Lead/contact info pushed when predictive dialer connects a call."""
        await self.send_json({
            'type': 'campaign_lead',
            'call_id': event.get('call_id'),
            'lead': event.get('lead', {}),
            'campaign': event.get('campaign', {}),
            'script': event.get('script', ''),
        })

    async def agent_status_update(self, event):
        """Broadcast from other agents (for awareness, not self-update)."""
        if event.get('agent_id') != self.agent_id:
            await self.send_json({
                'type': 'peer_status',
                'agent_id': event['agent_id'],
                'agent_name': event['agent_name'],
                'status': event['status'],
                'status_display': event['status_display'],
            })

    async def queue_stats_update(self, event):
        await self.send_json({'type': 'queue_stats', **event})

    # ── Database helpers ──────────────────────────────────────

    @tenant_db_sync
    def _identify_agent(self):
        """Identify agent from WS query param or scope user."""
        from .models import Agent

        # Try query param ?agent_id=N
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)

        agent_id = params.get('agent_id')
        if agent_id:
            try:
                agent = Agent.objects.get(id=int(agent_id))
                return {'id': agent.id, 'name': agent.name}
            except Agent.DoesNotExist:
                pass

        # Try scope user
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            try:
                agent = Agent.objects.get(user=user)
                return {'id': agent.id, 'name': agent.name}
            except Agent.DoesNotExist:
                pass

        # Fallback: try token from query params
        token = params.get('token')
        if token:
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                from django.contrib.auth import get_user_model
                User = get_user_model()
                validated = AccessToken(token)
                user = User.objects.get(id=validated['user_id'])
                agent = Agent.objects.get(user=user)
                return {'id': agent.id, 'name': agent.name}
            except Exception:
                pass

        return None

    @tenant_db_sync
    def _get_agent_extension(self):
        from .models import Agent
        try:
            agent = Agent.objects.get(id=self.agent_id)
            return agent.sip_extension or None
        except Agent.DoesNotExist:
            return None

    @tenant_db_sync
    def _set_presence(self, connected: bool):
        """Update WebSocket presence for this agent.

        On disconnect we DON'T clear last_heartbeat — a duplicate/overlapping
        socket closing must not wipe a live agent's presence. Availability is
        driven by heartbeat freshness, which decays naturally if truly gone.
        """
        from .models import Agent
        fields = {'ws_connected': connected}
        if connected:
            fields['last_heartbeat'] = timezone.now()
        Agent.objects.filter(id=self.agent_id).update(**fields)

    @tenant_db_sync
    def _touch_heartbeat(self):
        """Refresh the heartbeat timestamp (called on each WS heartbeat)."""
        from .models import Agent
        Agent.objects.filter(id=self.agent_id).update(
            ws_connected=True,
            last_heartbeat=timezone.now(),
        )

    @tenant_db_sync
    def _get_agent_state(self):
        from .models import Agent, Tier
        try:
            agent = Agent.objects.select_related('user').get(id=self.agent_id)
        except Agent.DoesNotExist:
            return {'error': 'Agent not found'}

        # Get agent queues
        tiers = Tier.objects.filter(agent=agent).select_related('queue')
        queues = [
            {
                'id': t.queue.id,
                'name': t.queue.name,
                'level': t.level,
                'position': t.position,
            }
            for t in tiers
        ]

        return {
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'status': agent.status,
                'status_display': agent.get_status_display(),
                'state': agent.state,
                'sip_extension': agent.sip_extension,
                'calls_answered': agent.calls_answered,
                'talk_time': agent.talk_time,
                'wrap_up_time': agent.wrap_up_time,
                'last_bridge_start': agent.last_bridge_start.isoformat() if agent.last_bridge_start else None,
                'last_bridge_end': agent.last_bridge_end.isoformat() if agent.last_bridge_end else None,
            },
            'queues': queues,
        }

    @tenant_db_sync
    def _set_agent_status(self, new_status):
        from .models import Agent
        from .constants import AgentStatus, AgentState
        agent = Agent.objects.get(id=self.agent_id)

        status_map = {
            'available': AgentStatus.AVAILABLE,
            'on_break': AgentStatus.ON_BREAK,
            'logged_out': AgentStatus.LOGGED_OUT,
        }
        agent.status = status_map.get(new_status, AgentStatus.LOGGED_OUT)
        if new_status == 'available':
            agent.state = AgentState.WAITING
        elif new_status == 'logged_out':
            agent.state = AgentState.WAITING
        agent.last_status_change = timezone.now()
        agent.save(update_fields=['status', 'state', 'last_status_change'])

        return {
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'status': agent.status,
                'status_display': agent.get_status_display(),
                'state': agent.state,
                'calls_answered': agent.calls_answered,
                'talk_time': agent.talk_time,
            }
        }

    @tenant_db_sync
    def _answer_call(self, call_id):
        from .models import Agent, QueueMember
        from .constants import AgentState
        agent = Agent.objects.get(id=self.agent_id)
        agent.state = AgentState.IN_CALL
        agent.last_bridge_start = timezone.now()
        agent.save(update_fields=['state', 'last_bridge_start'])

        # Try to send answer to FreeSWITCH via ESL
        try:
            from apps.dialer_cdr.esl import get_esl_connection
            conn = get_esl_connection('fs1')
            if conn and call_id:
                conn.send(f'api uuid_answer {call_id}')
        except Exception as exc:
            logger.warning(f"ESL answer failed: {exc}")

        return {
            'call_id': call_id,
            'status': 'answered',
            'agent_state': agent.state,
        }

    @tenant_db_sync
    def _hangup_call(self, call_id, disposition=''):
        from .models import Agent
        from .constants import AgentState
        agent = Agent.objects.get(id=self.agent_id)

        # Calculate talk time
        if agent.last_bridge_start:
            duration = (timezone.now() - agent.last_bridge_start).total_seconds()
            agent.talk_time += int(duration)
            agent.calls_answered += 1

        agent.state = AgentState.WAITING
        agent.last_bridge_end = timezone.now()
        agent.save(update_fields=['state', 'last_bridge_end', 'talk_time', 'calls_answered'])

        # Send hangup to FreeSWITCH
        try:
            from apps.dialer_cdr.esl import get_esl_connection
            conn = get_esl_connection('fs1')
            if conn and call_id:
                conn.send(f'api uuid_kill {call_id} NORMAL_CLEARING')
        except Exception as exc:
            logger.warning(f"ESL hangup failed: {exc}")

        return {
            'call_id': call_id,
            'status': 'ended',
            'disposition': disposition,
            'agent_state': agent.state,
        }

    @tenant_db_sync
    def _hold_call(self, call_id):
        try:
            from apps.dialer_cdr.esl import get_esl_connection
            conn = get_esl_connection('fs1')
            if conn and call_id:
                conn.send(f'api uuid_hold toggle {call_id}')
        except Exception as exc:
            logger.warning(f"ESL hold failed: {exc}")
        return {'call_id': call_id, 'status': 'held'}

    @tenant_db_sync
    def _resume_call(self, call_id):
        try:
            from apps.dialer_cdr.esl import get_esl_connection
            conn = get_esl_connection('fs1')
            if conn and call_id:
                conn.send(f'api uuid_hold off {call_id}')
        except Exception as exc:
            logger.warning(f"ESL resume failed: {exc}")
        return {'call_id': call_id, 'status': 'resumed'}

    @tenant_db_sync
    def _transfer_call(self, call_id, target):
        try:
            from apps.dialer_cdr.esl import get_esl_connection
            conn = get_esl_connection('fs1')
            if conn and call_id and target:
                conn.send(f'api uuid_transfer {call_id} {target} XML default')
                return {'call_id': call_id, 'target': target, 'status': 'transferred'}
        except Exception as exc:
            logger.warning(f"ESL transfer failed: {exc}")
        return {'call_id': call_id, 'target': target, 'status': 'failed'}

    @tenant_db_sync
    def _send_dtmf(self, call_id, digits):
        try:
            from apps.dialer_cdr.esl import get_esl_connection
            conn = get_esl_connection('fs1')
            if conn and call_id and digits:
                conn.send(f'api uuid_send_dtmf {call_id} {digits}')
        except Exception as exc:
            logger.warning(f"ESL DTMF failed: {exc}")

    @tenant_db_sync
    def _save_disposition(self, call_id, disposition, notes=''):
        """Save call disposition/notes to CDR."""
        from apps.dialer_cdr.models import VoIPCall
        try:
            call = VoIPCall.objects.get(callid=call_id)
            call.disposition = disposition
            call.save(update_fields=['disposition'])
        except VoIPCall.DoesNotExist:
            logger.warning(f"VoIPCall not found for disposition: {call_id}")

    @tenant_db_sync
    def _get_queue_stats(self, queue_id):
        from .models import Queue, QueueMember, Tier
        from .constants import AgentStatus
        try:
            queue = Queue.objects.get(id=queue_id)
        except Queue.DoesNotExist:
            return {'error': 'Queue not found'}

        waiting = QueueMember.objects.filter(
            queue=queue, abandoned_epoch__isnull=True, serving_agent__isnull=True
        ).count()
        active_agents = Tier.objects.filter(
            queue=queue, agent__status=AgentStatus.AVAILABLE
        ).count()

        return {
            'queue_id': queue.id,
            'queue_name': queue.name,
            'waiting_calls': waiting,
            'active_agents': active_agents,
        }

    async def _broadcast_agent_update(self, state):
        """Broadcast agent status change to all listeners."""
        agent_data = state.get('agent', {})
        await self.channel_layer.group_send('agent_status', {
            'type': 'agent_status_update',
            'agent_id': agent_data.get('id'),
            'agent_name': agent_data.get('name', ''),
            'status': agent_data.get('status'),
            'status_display': agent_data.get('status_display', ''),
            'state': agent_data.get('state', ''),
            'calls_answered': agent_data.get('calls_answered', 0),
            'talk_time': agent_data.get('talk_time', 0),
            'timestamp': timezone.now().isoformat(),
        })


class QueueStatusConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for queue status updates.

    Usage:
        ws://host/ws/callcenter/queues/{queue_id}/
    """

    async def connect(self):
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)
        self.tenant_name = params.get('tenant')

        self.queue_id = self.scope['url_route']['kwargs']['queue_id']
        self.group_name = f'queue_{self.queue_id}'
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Send initial queue state
        stats = await self._get_queue_stats(self.queue_id)
        await self.send_json({'type': 'queue_update', **stats})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def queue_update(self, event):
        await self.send_json({
            'type': 'queue_update',
            'queue_id': event['queue_id'],
            'queue_name': event['queue_name'],
            'waiting_calls': event['waiting_calls'],
            'active_agents': event['active_agents'],
            'members': event.get('members', []),
        })

    @tenant_db_sync
    def _get_queue_stats(self):
        from .models import Queue, QueueMember, Tier
        from .constants import AgentStatus
        try:
            queue = Queue.objects.get(id=self.queue_id)
        except Queue.DoesNotExist:
            return {'queue_id': self.queue_id, 'error': 'Not found'}

        waiting = QueueMember.objects.filter(
            queue=queue, abandoned_epoch__isnull=True, serving_agent__isnull=True
        ).count()
        active_agents = Tier.objects.filter(
            queue=queue, agent__status=AgentStatus.AVAILABLE
        ).count()

        return {
            'queue_id': queue.id,
            'queue_name': queue.name,
            'waiting_calls': waiting,
            'active_agents': active_agents,
        }


class LiveDashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for live dashboard updates.
    Aggregates all call center metrics.

    Usage:
        ws://host/ws/callcenter/dashboard/
    """

    async def connect(self):
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)
        self.tenant_name = params.get('tenant')

        self.group_name = 'dashboard'
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Send initial dashboard data
        data = await self._get_dashboard_data()
        await self.send_json({'type': 'dashboard_update', **data})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def dashboard_update(self, event):
        await self.send_json({
            'type': 'dashboard_update',
            'total_agents': event['total_agents'],
            'available_agents': event['available_agents'],
            'total_queues': event['total_queues'],
            'total_waiting_calls': event['total_waiting_calls'],
            'total_active_calls': event['total_active_calls'],
            'timestamp': event.get('timestamp'),
        })

    # Also forward agent status updates to dashboard
    async def agent_status_update(self, event):
        data = await self._get_dashboard_data()
        await self.send_json({'type': 'dashboard_update', **data})

    @tenant_db_sync
    def _get_dashboard_data(self):
        from .models import Agent, Queue, QueueMember
        from .constants import AgentStatus

        total_agents = Agent.objects.count()
        available_agents = Agent.objects.filter(status=AgentStatus.AVAILABLE).count()
        on_call = Agent.objects.filter(state='In a queue call').count()
        total_queues = Queue.objects.count()
        waiting_calls = QueueMember.objects.filter(
            abandoned_epoch__isnull=True, serving_agent__isnull=True
        ).count()

        return {
            'total_agents': total_agents,
            'available_agents': available_agents,
            'on_call_agents': on_call,
            'total_queues': total_queues,
            'total_waiting_calls': waiting_calls,
            'total_active_calls': on_call,
            'timestamp': timezone.now().isoformat(),
        }
