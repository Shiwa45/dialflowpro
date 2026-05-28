"""
Middleware helpers for tenant resolution.
"""
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django_tenants.middleware.main import TenantMainMiddleware as BaseTenantMainMiddleware

from .models import Tenant, Domain


class TenantHeaderMiddleware(MiddlewareMixin):
    """
    Allow API clients to select a tenant by schema name via
    the ``X-Tenant`` request header.

    django-tenants normally resolves tenants from the request host.
    During local React development the browser host is ``localhost``,
    which maps to the *public* tenant.  The frontend sends
    ``X-Tenant: <schema_name>`` after login so that subsequent API
    requests hit the correct tenant schema.

    Instead of faking the Host header (which may not resolve to a
    Domain row), we directly set the tenant on ``request`` and switch
    the DB connection to that schema.
    """

    def process_request(self, request):
        tenant_schema = request.headers.get('X-Tenant')
        if not tenant_schema:
            return None

        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            return None

        # Wire up the tenant exactly the way django-tenants expects.
        request.tenant = tenant
        connection.set_tenant(tenant)
        return None


class UserTenantMiddleware(MiddlewareMixin):
    """
    Fallback: if no ``X-Tenant`` header was provided but the user is
    authenticated and belongs to a tenant, switch to that tenant's
    schema automatically.

    Must run *after* AuthenticationMiddleware in the MIDDLEWARE list.
    """

    def process_request(self, request):
        # Skip if a tenant was already resolved (by header or host).
        if getattr(request, 'tenant', None) and request.tenant.schema_name != 'public':
            return None

        user = getattr(request, 'user', None)
        if user and user.is_authenticated and getattr(user, 'tenant_id', None):
            try:
                tenant = Tenant.objects.get(pk=user.tenant_id)
                request.tenant = tenant
                connection.set_tenant(tenant)
            except Tenant.DoesNotExist:
                pass

        return None


class ConditionalTenantMainMiddleware(BaseTenantMainMiddleware):
    """
    Wrapper around django-tenants' TenantMainMiddleware that skips
    host-based tenant resolution when a tenant has already been set
    by TenantHeaderMiddleware (via the X-Tenant header).
    """

    def process_request(self, request):
        # If TenantHeaderMiddleware already resolved a non-public tenant,
        # skip the host-based resolution entirely.
        if getattr(request, 'tenant', None) and request.tenant.schema_name != 'public':
            return None
        return super().process_request(request)
