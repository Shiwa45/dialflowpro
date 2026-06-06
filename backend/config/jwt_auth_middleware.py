"""
JWT authentication middleware for Django Channels WebSocket connections.
Reads ?token=<jwt> from the query string and populates scope['user'].
"""
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket' and 'user' not in scope:
            query_string = scope.get('query_string', b'').decode()
            params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)
            token_str = params.get('token')
            scope['user'] = await _user_from_token(token_str) if token_str else AnonymousUser()
        return await self.inner(scope, receive, send)


@database_sync_to_async
def _user_from_token(token_str):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from django.contrib.auth import get_user_model

    try:
        token = AccessToken(token_str)
        User = get_user_model()
        return User.objects.get(id=token['user_id'])
    except (InvalidToken, TokenError, Exception):
        return AnonymousUser()
