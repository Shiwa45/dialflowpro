"""
Views for user authentication and management.
"""
from rest_framework import viewsets, status as drf_status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from .models import User, UserProfile
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    PasswordChangeSerializer, UserProfileSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user CRUD operations.
    Only managers and superadmins can manage users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users by tenant"""
        user = self.request.user
        if user.is_superadmin:
            return User.objects.all()
        elif user.tenant:
            return User.objects.filter(tenant=user.tenant)
        return User.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a new user.
        POST /api/accounts/users/register/
        """
        serializer = UserCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=drf_status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login endpoint.
        POST /api/accounts/users/login/
        """
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Logout endpoint.
        POST /api/accounts/users/logout/
        """
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        
        logout(request)
        return Response({'detail': 'Successfully logged out.'})
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user profile.
        GET /api/accounts/users/me/
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Update current user profile.
        PUT/PATCH /api/accounts/users/update_profile/
        """
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change password for current user.
        POST /api/accounts/users/change_password/
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'detail': 'Password changed successfully.'})

    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        """
        Admin resets another user's password.
        POST /api/accounts/users/{id}/set_password/
        Body: { "password": "newpass123" }
        """
        target = self.get_object()
        password = request.data.get('password', '').strip()
        if not password:
            return Response({'password': 'Password is required.'}, status=drf_status.HTTP_400_BAD_REQUEST)
        if len(password) < 8:
            return Response({'password': 'Password must be at least 8 characters.'}, status=drf_status.HTTP_400_BAD_REQUEST)
        target.set_password(password)
        target.save()
        return Response({'detail': f'Password for {target.username} updated.'})

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle a user's active status.
        POST /api/accounts/users/{id}/toggle_active/
        """
        target = self.get_object()
        target.is_active = not target.is_active
        target.save(update_fields=['is_active'])
        return Response({'is_active': target.is_active, 'username': target.username})

    @action(detail=True, methods=['patch'])
    def update_extension(self, request, pk=None):
        """
        Update an agent's SIP extension number and/or password.
        PATCH /api/accounts/users/{id}/update_extension/
        Body: { "extension": "1001", "sip_password": "secret" }
        """
        from apps.callcenter.models import Agent
        target = self.get_object()
        extension = request.data.get('extension', '').strip()
        sip_pw    = request.data.get('sip_password', '').strip()

        try:
            agent = target.agent_profile
        except Exception:
            agent = Agent(user=target, name=target.get_full_name() or target.username)

        agent.sip_extension = extension
        if sip_pw:
            agent.sip_password = sip_pw
        agent.contact       = f'user/{extension}' if extension else ''
        agent.save()
        sync_result = None
        if extension and agent.sip_password:
            from apps.callcenter.freeswitch import sync_agent_extension

            sync_result = sync_agent_extension(agent)
        return Response({
            'extension': extension,
            'sip_password': '***' if agent.sip_password else '',
            'sync': sync_result.as_dict() if sync_result else None,
        })

    @action(detail=True, methods=['post'])
    def sync_extension(self, request, pk=None):
        """
        Write FreeSWITCH user directory XML for this agent's extension
        and run reloadxml via ESL.
        POST /api/accounts/users/{id}/sync_extension/
        """
        from apps.callcenter.freeswitch import sync_agent_extension

        target = self.get_object()
        try:
            agent = target.agent_profile
        except Exception:
            return Response({'success': False, 'message': 'No agent profile found. Save the extension first.'}, status=400)

        result = sync_agent_extension(agent)
        return Response(result.as_dict(), status=result.status_code)

    @action(detail=False, methods=['post'])
    def sync_all_extensions(self, request):
        """
        Write FreeSWITCH user directory XML for all visible agents with SIP
        credentials, then run reloadxml for each sync attempt.
        POST /api/accounts/users/sync_all_extensions/
        """
        from apps.callcenter.models import Agent
        from apps.callcenter.freeswitch import sync_agent_extension

        agents = Agent.objects.filter(
            user__in=self.get_queryset(),
        ).select_related('user').order_by('sip_extension')

        results = []
        synced = 0
        failed = 0
        skipped = 0

        for agent in agents:
            missing = []
            if not agent.sip_extension:
                missing.append('extension')
            if not agent.sip_password:
                missing.append('SIP password')
            if missing:
                skipped += 1
                results.append({
                    'user_id': agent.user_id,
                    'username': agent.user.username,
                    'extension': agent.sip_extension,
                    'success': False,
                    'skipped': True,
                    'xml_written': False,
                    'reloaded': False,
                    'message': f"Skipped: missing {' and '.join(missing)}.",
                    'xml_path': '',
                })
                continue

            result = sync_agent_extension(agent)
            if result.success:
                synced += 1
            else:
                failed += 1
            results.append({
                'user_id': agent.user_id,
                'username': agent.user.username,
                'extension': agent.sip_extension,
                **result.as_dict(),
            })

        success = failed == 0
        if not results:
            message = 'No agent extensions with SIP passwords found to sync.'
        elif failed:
            message = f'Synced {synced} extension(s), {failed} failed, {skipped} skipped.'
        else:
            message = f'Synced {synced} extension(s), {skipped} skipped.'

        return Response({
            'success': success,
            'synced': synced,
            'failed': failed,
            'skipped': skipped,
            'message': message,
            'results': results,
        }, status=drf_status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfile management"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter profiles by tenant"""
        user = self.request.user
        if user.is_superadmin:
            return UserProfile.objects.all()
        elif user.tenant:
            return UserProfile.objects.filter(user__tenant=user.tenant)
        return UserProfile.objects.none()
