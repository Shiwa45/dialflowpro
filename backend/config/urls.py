"""
DialFlow Pro URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Authentication (JWT)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # API Apps
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/dialer-settings/', include('apps.dialer_settings.urls')),

    # Phase 2 - Campaign Core
    path('api/dialer-contact/', include('apps.dialer_contact.urls')),
    path('api/dialer-gateway/', include('apps.dialer_gateway.urls')),
    path('api/dialer-campaign/', include('apps.dialer_campaign.urls')),
    path('api/dialer-cdr/', include('apps.dialer_cdr.urls')),

    # Phase 3 - IVR & Survey
    path('api/survey/', include('apps.survey.urls')),
    path('api/audiofield/', include('apps.audiofield.urls')),

    # Phase 4 - Call Center
    path('api/callcenter/', include('apps.callcenter.urls')),

    # Phase 5 - DNC & SMS
    path('api/dnc/', include('apps.dnc.urls')),
    path('api/sms/', include('apps.mod_sms.urls')),

    # AI Voice Agents
    path('api/ai/', include('apps.ai_agent.urls')),

    # Health check
    path('health/', include('apps.common.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "DialFlow Pro Administration"
admin.site.site_title = "DialFlow Pro Admin"
admin.site.index_title = "Welcome to DialFlow Pro Administration"
