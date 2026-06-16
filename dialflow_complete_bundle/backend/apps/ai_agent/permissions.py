"""
Permissions for the AI Agent app.

`HasActiveAISubscription` is the gate: only tenants whose AISubscription is
active may create or run AI agents. Read access (listing existing agents, call
history) is allowed so an admin whose plan lapsed can still see their data.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import AISubscription


def get_subscription(request):
    tenant = getattr(request.user, "tenant", None)
    if not tenant:
        return None
    return AISubscription.objects.filter(tenant=tenant).first()


class HasActiveAISubscription(BasePermission):
    message = "Your tenant does not have an active AI agent subscription."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Reads allowed for anyone in the tenant; writes need an active sub.
        if request.method in SAFE_METHODS:
            return True
        sub = get_subscription(request)
        return bool(sub and sub.is_active)


class IsTenantAdminForAI(BasePermission):
    """Only managers / superadmins may configure AI agents (not plain agents)."""
    message = "Only managers can configure AI agents."

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        # role 1 superadmin, 2 manager (matches accounts.UserRole)
        return getattr(u, "role", None) in (1, 2)
