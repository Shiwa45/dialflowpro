"""
Views for Tenant management.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Tenant
from .serializers import TenantSerializer, TenantCreateSerializer


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tenant CRUD.
    Only superadmins can manage tenants.
    """
    queryset = Tenant.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Superadmins see all, others see only their tenant"""
        user = self.request.user
        if user.is_superadmin:
            return Tenant.objects.all()
        elif user.tenant:
            return Tenant.objects.filter(id=user.tenant.id)
        return Tenant.objects.none()
    
    def get_serializer_class(self):
        """Use creation serializer for create action"""
        if self.action == 'create':
            return TenantCreateSerializer
        return TenantSerializer
