"""
ASGI config for DialFlow Pro.
Supports both HTTP and WebSocket protocols via Django Channels.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Initialize Django ASGI application early to populate apps registry
django_asgi_app = get_asgi_application()

# Import websocket routing after Django is initialized
from config.routing import websocket_urlpatterns
from config.jwt_auth_middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
