"""
Views for DialerSetting management.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import DialerSetting
from .serializers import DialerSettingSerializer, DialerSettingDetailSerializer


class DialerSettingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DialerSetting CRUD.
    Managers can view/edit their tenant's settings.
    Superadmins can manage all settings.
    """
    queryset = DialerSetting.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by tenant"""
        user = self.request.user
        if user.is_superadmin:
            return DialerSetting.objects.all()
        elif user.tenant:
            return DialerSetting.objects.filter(tenant=user.tenant)
        return DialerSetting.objects.none()
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve"""
        if self.action == 'retrieve':
            return DialerSettingDetailSerializer
        return DialerSettingSerializer
