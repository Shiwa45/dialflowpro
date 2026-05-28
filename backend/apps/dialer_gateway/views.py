"""Views for Gateway management"""
import os
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import Gateway
from .serializers import GatewaySerializer

logger = logging.getLogger(__name__)


def _sync_gateway(gateway: Gateway) -> dict:
    """
    Write FreeSWITCH XML config for gateway and reload sofia via ESL.

    Returns a dict with:
      xml_written  bool   — whether the XML file was written OK
      esl_reloaded bool   — whether sofia was reloaded via ESL
      success      bool   — True if xml_written (ESL failure is a warning, not a hard error)
      message      str
      xml_path     str
      manual_cmd   str    — the FreeSWITCH CLI command to run manually if ESL failed
    """
    if not gateway.sip_host:
        return {
            'success': False, 'xml_written': False, 'esl_reloaded': False,
            'message': 'SIP host is not set on this gateway.',
        }

    xml     = gateway.generate_fs_xml()
    profile = getattr(settings, 'FS_SOFIA_PROFILE', 'external')

    # Build the config path using posixpath so it stays / on any OS
    import posixpath
    raw_dir  = getattr(settings, 'FS_GATEWAY_CONFIG_DIR', '/etc/freeswitch/sip_profiles/external')
    # os.path.join on Windows corrupts a POSIX path prefix; use the raw dir + separator
    xml_path = raw_dir.rstrip('/\\') + os.sep + f'{gateway.name}.xml'

    manual_cmd = f'sofia profile {profile} rescan'

    # ── 1. Write XML file ──
    try:
        os.makedirs(raw_dir, exist_ok=True)
        with open(xml_path, 'w', newline='\n') as fh:
            fh.write(xml)
        logger.info(f'Gateway XML written to {xml_path}')
    except (IOError, OSError) as exc:
        return {
            'success': False, 'xml_written': False, 'esl_reloaded': False,
            'xml_path': xml_path,
            'message': f'Cannot write XML to {xml_path}: {exc}',
            'manual_cmd': manual_cmd,
        }

    # ── 2. Reload sofia via ESL ──
    try:
        from apps.dialer_cdr.esl import get_esl_connection
        conn = get_esl_connection('fs1')
        if conn:
            conn.send(f'api sofia profile {profile} rescan')
            return {
                'success': True, 'xml_written': True, 'esl_reloaded': True,
                'xml_path': xml_path,
                'message': f'Gateway "{gateway.name}" synced and sofia {profile} rescanned.',
                'manual_cmd': manual_cmd,
            }
    except Exception as exc:
        logger.warning(f'ESL reload failed for gateway {gateway.name}: {exc}')

    # XML written but ESL unavailable — still a partial success
    return {
        'success': True, 'xml_written': True, 'esl_reloaded': False,
        'xml_path': xml_path,
        'message': (
            f'XML written to {xml_path}. '
            f'ESL not reachable — run this in the FreeSWITCH CLI: {manual_cmd}'
        ),
        'manual_cmd': manual_cmd,
    }


def _delete_gateway_xml(gateway: Gateway):
    config_dir = getattr(settings, 'FS_GATEWAY_CONFIG_DIR', '/etc/freeswitch/sip_profiles/external')
    xml_path = os.path.join(config_dir, f'{gateway.name}.xml')
    try:
        if os.path.exists(xml_path):
            os.remove(xml_path)
    except OSError as exc:
        logger.warning(f'Could not remove gateway XML {xml_path}: {exc}')


class GatewayViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Gateway CRUD + FreeSWITCH sync.
    Gateway is a tenant-level resource (no user FK).
    """
    serializer_class = GatewaySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Gateway.objects.all()

    def perform_destroy(self, instance):
        _delete_gateway_xml(instance)
        instance.delete()

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Sync this gateway to FreeSWITCH:
          1. Write /etc/freeswitch/sip_profiles/external/<name>.xml
          2. Run: sofia profile external rescan
        POST /api/dialer-gateway/gateways/{id}/sync/
        """
        gateway = self.get_object()
        result = _sync_gateway(gateway)
        http_status = status.HTTP_200_OK if result['success'] else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(result, status=http_status)

    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """
        Sync all active gateways that have a sip_host configured.
        POST /api/dialer-gateway/gateways/sync_all/
        """
        gateways = Gateway.objects.filter(status=1).exclude(sip_host='')
        results = []
        for gw in gateways:
            res = _sync_gateway(gw)
            results.append({'id': gw.id, 'name': gw.name, **res})

        # Final sofia rescan (already done per gateway but one more for safety)
        return Response({'synced': len(results), 'results': results})

    @action(detail=True, methods=['get'])
    def xml_preview(self, request, pk=None):
        """
        Return the FreeSWITCH XML that would be written for this gateway.
        GET /api/dialer-gateway/gateways/{id}/xml_preview/
        """
        gateway = self.get_object()
        if not gateway.sip_host:
            return Response({'error': 'SIP host not set'}, status=400)
        return Response({'xml': gateway.generate_fs_xml(), 'name': gateway.name})
