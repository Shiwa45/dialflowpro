"""
Call Center models.
Queue management, agent availability, tier routing.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from xml.sax.saxutils import escape
from apps.common.models import TimeStampedModel
from .constants import (
    AgentStatus, AgentState, QueueStrategy,
    TierLevel, TierPosition
)


class Queue(TimeStampedModel):
    """
    Call queue for routing incoming calls to agents.
    Supports 8 routing strategies.
    """
    name = models.CharField(
        max_length=128,
        verbose_name=_('queue name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description')
    )
    
    # Strategy
    strategy = models.IntegerField(
        choices=QueueStrategy.choices,
        default=QueueStrategy.LONGEST_IDLE_AGENT,
        verbose_name=_('routing strategy')
    )
    
    # Music on hold
    moh_sound = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('music on hold'),
        help_text=_('Audio file path for hold music')
    )
    
    # Timeouts
    time_base_score = models.IntegerField(
        default=0,
        verbose_name=_('time base score'),
        help_text=_('Seconds before increasing priority')
    )
    
    tier_rules_apply = models.BooleanField(
        default=False,
        verbose_name=_('apply tier rules'),
        help_text=_('Route calls based on tier levels')
    )
    
    tier_rule_wait_second = models.IntegerField(
        default=0,
        verbose_name=_('tier wait seconds'),
        help_text=_('Seconds to wait before trying next tier')
    )
    
    tier_rule_wait_multiply_level = models.BooleanField(
        default=False,
        verbose_name=_('multiply tier wait'),
        help_text=_('Multiply wait time by tier level')
    )
    
    tier_rule_no_agent_no_wait = models.BooleanField(
        default=False,
        verbose_name=_('no wait if no agents'),
        help_text=_('Skip to next tier immediately if no agents')
    )
    
    # Max wait time
    max_wait_time = models.IntegerField(
        default=0,
        verbose_name=_('max wait time'),
        help_text=_('Maximum seconds caller will wait (0 = unlimited)')
    )
    
    # Max wait time with no agent
    max_wait_time_with_no_agent = models.IntegerField(
        default=0,
        verbose_name=_('max wait without agent'),
        help_text=_('Max wait if no agents available')
    )
    
    # Discard abandoned after seconds
    discard_abandoned_after = models.IntegerField(
        default=60,
        verbose_name=_('discard abandoned after'),
        help_text=_('Seconds before removing abandoned calls')
    )
    
    # Ring timeout
    ring_progressively_delay = models.IntegerField(
        default=10,
        verbose_name=_('ring delay'),
        help_text=_('Seconds between ring attempts')
    )
    
    # Owner
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='queues',
        verbose_name=_('user')
    )
    
    class Meta:
        db_table = 'callcenter_queue'
        verbose_name = _('queue')
        verbose_name_plural = _('queues')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Agent(TimeStampedModel):
    """
    Call center agent.
    Tracks availability, status, and call statistics.
    """
    name = models.CharField(
        max_length=128,
        verbose_name=_('agent name')
    )
    
    # User reference (agent must be a user)
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='agent_profile',
        verbose_name=_('user')
    )
    
    # Status
    status = models.IntegerField(
        choices=AgentStatus.choices,
        default=AgentStatus.LOGGED_OUT,
        verbose_name=_('status')
    )
    
    # State (during call)
    state = models.CharField(
        max_length=50,
        choices=AgentState.choices,
        default=AgentState.WAITING,
        verbose_name=_('state')
    )
    
    # Contact info
    contact = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('contact'),
        help_text=_('SIP URI or phone number for agent (e.g. user/1001)')
    )

    # SIP extension credentials — stored to generate FreeSWITCH directory XML
    sip_extension = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('SIP extension'),
        help_text=_('Extension number the agent registers with (e.g. 1001)')
    )

    sip_password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_('SIP password'),
        help_text=_('Password the agent uses to register their SIP phone')
    )
    
    # Statistics
    no_answer_delay_time = models.IntegerField(
        default=0,
        verbose_name=_('no answer delay'),
        help_text=_('Seconds to wait for answer')
    )
    
    max_no_answer = models.IntegerField(
        default=3,
        verbose_name=_('max no answer'),
        help_text=_('Max missed calls before logout')
    )
    
    wrap_up_time = models.IntegerField(
        default=0,
        verbose_name=_('wrap up time'),
        help_text=_('Seconds after call before available')
    )
    
    reject_delay_time = models.IntegerField(
        default=0,
        verbose_name=_('reject delay'),
        help_text=_('Seconds delay after rejection')
    )
    
    busy_delay_time = models.IntegerField(
        default=0,
        verbose_name=_('busy delay'),
        help_text=_('Seconds delay when busy')
    )
    
    # Call tracking
    last_bridge_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last call start')
    )
    
    last_bridge_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last call end')
    )
    
    talk_time = models.IntegerField(
        default=0,
        verbose_name=_('total talk time'),
        help_text=_('Total seconds on calls')
    )
    
    calls_answered = models.IntegerField(
        default=0,
        verbose_name=_('calls answered')
    )
    
    # Last status change
    last_status_change = models.DateTimeField(
        auto_now=True,
        verbose_name=_('last status change')
    )

    # ── Presence tracking (real availability) ──
    # An agent is only truly available to receive calls when their Agent
    # Desktop WebSocket is connected AND their SIP phone is registered.
    ws_connected = models.BooleanField(
        default=False,
        verbose_name=_('websocket connected'),
        help_text=_('True while the agent desktop WebSocket is connected')
    )

    last_heartbeat = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last heartbeat'),
        help_text=_('Last WebSocket heartbeat — used to detect dropped connections')
    )

    class Meta:
        db_table = 'callcenter_agent'
        verbose_name = _('agent')
        verbose_name_plural = _('agents')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def generate_fs_directory_xml(self) -> str:
        """Generate FreeSWITCH user directory XML for this agent's SIP extension."""
        ext  = escape(self.sip_extension or '')
        pw   = escape(self.sip_password or '', {'"': '&quot;'})
        full = escape(self.user.get_full_name() or self.name or ext, {'"': '&quot;'})
        return '\n'.join([
            '<include>',
            f'  <user id="{ext}">',
            '    <params>',
            f'      <param name="password"    value="{pw}"/>',
            f'      <param name="vm-password" value="{ext}"/>',
            '    </params>',
            '    <variables>',
            '      <variable name="toll_allow"                    value="domestic,international,local"/>',
            f'      <variable name="accountcode"                   value="{ext}"/>',
            '      <variable name="user_context"                  value="default"/>',
            f'      <variable name="effective_caller_id_name"      value="{full}"/>',
            f'      <variable name="effective_caller_id_number"    value="{ext}"/>',
            f'      <variable name="outbound_caller_id_name"       value="{full}"/>',
            f'      <variable name="outbound_caller_id_number"     value="{ext}"/>',
            '    </variables>',
            '  </user>',
            '</include>',
        ])

    def set_available(self):
        """Set agent status to available"""
        self.status = AgentStatus.AVAILABLE
        self.state = AgentState.WAITING
        self.save(update_fields=['status', 'state', 'last_status_change'])
    
    def set_on_break(self):
        """Set agent on break"""
        self.status = AgentStatus.ON_BREAK
        self.save(update_fields=['status', 'last_status_change'])
    
    def set_logged_out(self):
        """Log out agent"""
        self.status = AgentStatus.LOGGED_OUT
        self.save(update_fields=['status', 'last_status_change'])


class Tier(TimeStampedModel):
    """
    Tier - assigns agents to queues with priority.
    Level (1-5) and position (1-10) determine routing order.
    """
    queue = models.ForeignKey(
        Queue,
        on_delete=models.CASCADE,
        related_name='tiers',
        verbose_name=_('queue')
    )
    
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='tiers',
        verbose_name=_('agent')
    )
    
    # Tier level (1 = highest priority)
    level = models.IntegerField(
        choices=TierLevel.choices,
        default=TierLevel.LEVEL_1,
        verbose_name=_('tier level')
    )
    
    # Position within tier
    position = models.IntegerField(
        choices=TierPosition.choices,
        default=TierPosition.POSITION_1,
        verbose_name=_('position')
    )
    
    class Meta:
        db_table = 'callcenter_tier'
        verbose_name = _('tier')
        verbose_name_plural = _('tiers')
        unique_together = [['queue', 'agent']]
        ordering = ['queue', 'level', 'position']
    
    def __str__(self):
        return f"{self.queue.name} - {self.agent.name} (L{self.level}/P{self.position})"


class QueueMember(TimeStampedModel):
    """
    Active queue member - tracks current calls in queue.
    Created when call enters queue, deleted when answered/abandoned.
    """
    queue = models.ForeignKey(
        Queue,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('queue')
    )
    
    # Call info
    callrequest = models.ForeignKey(
        'dialer_cdr.Callrequest',
        on_delete=models.CASCADE,
        related_name='queue_memberships',
        verbose_name=_('call request')
    )
    
    session_uuid = models.CharField(
        max_length=255,
        verbose_name=_('session UUID'),
        help_text=_('FreeSWITCH session UUID')
    )
    
    # Caller info
    caller_number = models.CharField(
        max_length=80,
        verbose_name=_('caller number')
    )
    
    caller_name = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_('caller name')
    )
    
    # Queue entry time
    joined_epoch = models.BigIntegerField(
        verbose_name=_('joined time'),
        help_text=_('Unix timestamp when joined queue')
    )
    
    # Current status
    serving_agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='serving_calls',
        verbose_name=_('serving agent')
    )
    
    serving_system = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('serving system'),
        help_text=_('FreeSWITCH node handling call')
    )
    
    state = models.CharField(
        max_length=50,
        default='Waiting',
        verbose_name=_('state')
    )
    
    # Abandoned flag
    abandoned_epoch = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('abandoned time')
    )
    
    class Meta:
        db_table = 'callcenter_queue_member'
        verbose_name = _('queue member')
        verbose_name_plural = _('queue members')
        ordering = ['joined_epoch']
    
    def __str__(self):
        return f"{self.caller_number} in {self.queue.name}"
