"""
Constants for call center app.
Agent states, queue strategies, tier levels.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class AgentStatus(models.IntegerChoices):
    """Agent availability status"""
    LOGGED_OUT = 0, _('Logged Out')
    AVAILABLE = 1, _('Available')
    ON_BREAK = 2, _('On Break')
    ON_DEMAND = 3, _('On Demand')


class AgentState(models.TextChoices):
    """Agent call state (during active call)"""
    WAITING = 'Waiting', _('Waiting')
    RECEIVING = 'Receiving', _('Receiving')
    IN_A_QUEUE_CALL = 'In a queue call', _('In a Queue Call')
    IDLE = 'Idle', _('Idle')


class QueueStrategy(models.IntegerChoices):
    """
    Call routing strategies - 8 types from Newfies-Dialer.
    Determines how calls are distributed to agents.
    """
    RING_ALL = 1, _('Ring All')
    LONGEST_IDLE_AGENT = 2, _('Longest Idle Agent')
    ROUND_ROBIN = 3, _('Round Robin')
    TOP_DOWN = 4, _('Top Down')
    AGENT_WITH_LEAST_TALK_TIME = 5, _('Agent with Least Talk Time')
    AGENT_WITH_FEWEST_CALLS = 6, _('Agent with Fewest Calls')
    SEQUENTIALLY_BY_AGENT_ORDER = 7, _('Sequentially by Agent Order')
    RANDOM = 8, _('Random')


class TierLevel(models.IntegerChoices):
    """
    Tier priority levels.
    Lower number = higher priority (1 is highest).
    """
    LEVEL_1 = 1, _('Level 1 (Highest)')
    LEVEL_2 = 2, _('Level 2')
    LEVEL_3 = 3, _('Level 3')
    LEVEL_4 = 4, _('Level 4')
    LEVEL_5 = 5, _('Level 5 (Lowest)')


class TierPosition(models.IntegerChoices):
    """
    Agent position within tier.
    Used for ordering agents in same tier level.
    """
    POSITION_1 = 1, _('Position 1')
    POSITION_2 = 2, _('Position 2')
    POSITION_3 = 3, _('Position 3')
    POSITION_4 = 4, _('Position 4')
    POSITION_5 = 5, _('Position 5')
    POSITION_6 = 6, _('Position 6')
    POSITION_7 = 7, _('Position 7')
    POSITION_8 = 8, _('Position 8')
    POSITION_9 = 9, _('Position 9')
    POSITION_10 = 10, _('Position 10')
