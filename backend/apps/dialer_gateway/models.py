"""
Gateway model - SIP trunk configuration.
Preserves all original fields from dialer_gateway.Gateway.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedModel
from .constants import GatewayStatus


class Gateway(TimeStampedModel):
    """
    SIP Gateway/Trunk configuration for outbound calling.
    Defines FreeSWITCH sofia gateway strings and dial parameters.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('name'),
        help_text=_('Gateway name')
    )
    
    status = models.IntegerField(
        choices=GatewayStatus.choices,
        default=GatewayStatus.ACTIVE,
        verbose_name=_('gateway status')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description'),
        help_text=_('Gateway provider notes')
    )
    
    # Number manipulation
    addprefix = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_('add prefix')
    )
    
    removeprefix = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_('remove prefix')
    )
    
    # FreeSWITCH dial strings
    gateways = models.CharField(
        max_length=500,
        verbose_name=_('gateways'),
        help_text=_('Gateway string to dial (e.g., "sofia/gateway/myprovider/")')
    )
    
    gateway_codecs = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('gateway codecs'),
        help_text=_('Codec string (e.g., "PCMA,PCMU")')
    )
    
    gateway_timeouts = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('gateway timeouts'),
        help_text=_('Timeout in seconds (e.g., "10")')
    )
    
    gateway_retries = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('gateway retries'),
        help_text=_('Retry count per gateway (e.g., "2,1")')
    )
    
    originate_dial_string = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('originate dial string'),
        help_text=_('Channel variables for originate')
    )
    
    addparameter = models.CharField(
        max_length=360,
        blank=True,
        verbose_name=_('additional parameters')
    )
    
    # Stats and limits
    secondused = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('seconds used')
    )
    
    count_call = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('call count')
    )
    
    count_in_use = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('calls in use')
    )
    
    maximum_call = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('maximum calls'),
        help_text=_('Maximum concurrent calls')
    )
    
    # SIP connection details (used for XML auto-generation + FS sync)
    sip_host = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('SIP host'),
        help_text=_('IP or hostname of the SIP/GSM gateway (e.g. 192.168.1.113)')
    )

    sip_port = models.PositiveIntegerField(
        default=5060,
        verbose_name=_('SIP port')
    )

    register = models.BooleanField(
        default=False,
        verbose_name=_('register'),
        help_text=_('Whether FreeSWITCH should register with this gateway')
    )

    sip_username = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('SIP username'),
        help_text=_('Username for SIP registration (leave blank for GSM/direct gateways)')
    )

    sip_password = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('SIP password')
    )

    caller_id_in_from = models.BooleanField(
        default=True,
        verbose_name=_('caller ID in From header'),
        help_text=_('Pass caller ID via SIP From header (recommended for GSM gateways)')
    )

    # Failover
    failover = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='failover_gateways',
        verbose_name=_('failover gateway')
    )

    class Meta:
        db_table = 'dialer_gateway'
        verbose_name = _('gateway')
        verbose_name_plural = _('gateways')
        ordering = ['name']
    
    def __str__(self):
        return self.name

    def generate_fs_xml(self) -> str:
        """Return a FreeSWITCH XML gateway stanza for this gateway."""
        host = self.sip_host or '127.0.0.1'
        port = self.sip_port or 5060
        proxy = f'{host}:{port}' if port != 5060 else host

        lines = [
            '<include>',
            f'  <gateway name="{self.name}">',
            f'    <param name="proxy"    value="{proxy}"/>',
            f'    <param name="realm"    value="{host}"/>',
            f'    <param name="register" value="{"true" if self.register else "false"}"/>',
        ]

        if self.register and self.sip_username:
            lines += [
                f'    <param name="username" value="{self.sip_username}"/>',
                f'    <param name="password" value="{self.sip_password}"/>',
            ]

        if self.caller_id_in_from:
            lines.append('    <param name="caller-id-in-from" value="true"/>')

        if self.gateway_codecs:
            lines.append(f'    <param name="codec-prefs" value="{self.gateway_codecs}"/>')

        if self.gateway_timeouts:
            lines.append(f'    <param name="timeout-seconds" value="{self.gateway_timeouts}"/>')

        lines += ['  </gateway>', '</include>']
        return '\n'.join(lines)

    @property
    def fs_dial_string_prefix(self) -> str:
        """Convenience: the sofia dial string prefix for this gateway."""
        return self.gateways or f'sofia/gateway/{self.name}/'
