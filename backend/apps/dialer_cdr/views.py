"""Views for Callrequest and VoIPCall"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Callrequest, VoIPCall
from .serializers import CallrequestSerializer, VoIPCallSerializer


class CallrequestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Callrequest (read-only)"""
    serializer_class = CallrequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'campaign', 'completed']
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return Callrequest.objects.filter(
            user__tenant=user.tenant
        ).select_related('campaign', 'aleg_gateway', 'user')


class VoIPCallViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for VoIPCall CDR (read-only)"""
    serializer_class = VoIPCallSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['disposition', 'starting_date']
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return VoIPCall.objects.filter(
            user__tenant=user.tenant
        ).select_related('user', 'callrequest')
