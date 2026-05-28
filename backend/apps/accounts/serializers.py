"""
Serializers for User authentication and management.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, UserProfile, UserRole


class UserTenantSerializer(serializers.Serializer):
    """Small tenant payload returned with authenticated users."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    schema_name = serializers.CharField(read_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'dialersetting', 'email_notifications', 'sms_notifications',
            'timezone', 'language', 'created_date', 'updated_date'
        ]
        read_only_fields = ['created_date', 'updated_date']


class UserSerializer(serializers.ModelSerializer):
    """Main User serializer"""
    profile = UserProfileSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    tenant = UserTenantSerializer(read_only=True)
    agent_contact   = serializers.SerializerMethodField()
    agent_extension = serializers.SerializerMethodField()

    def get_agent_contact(self, obj):
        try:
            return obj.agent_profile.contact
        except Exception:
            return None

    def get_agent_extension(self, obj):
        try:
            return obj.agent_profile.sip_extension
        except Exception:
            return None

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'tenant', 'phone', 'company',
            'address', 'city', 'state', 'country', 'zip_code',
            'is_active', 'date_joined', 'profile',
            'agent_contact', 'agent_extension',
        ]
        read_only_fields = ['id', 'date_joined', 'tenant']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user creation (admin-side)"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    # SIP extension fields — only relevant when role=AGENT
    extension    = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')
    sip_password = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'role',
            'extension', 'sip_password',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        extension    = validated_data.pop('extension',    '')
        sip_password = validated_data.pop('sip_password', '')

        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None) if request else None

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role', UserRole.MANAGER),
            tenant=tenant
        )

        UserProfile.objects.create(user=user)

        # Auto-create Agent profile for agent-role users
        if user.role == UserRole.AGENT:
            from apps.callcenter.models import Agent
            contact = f'user/{extension}' if extension else ''
            agent = Agent.objects.create(
                user=user,
                name=user.get_full_name() or user.username,
                contact=contact,
                sip_extension=extension,
                sip_password=sip_password,
            )
            if extension and sip_password:
                from apps.callcenter.freeswitch import sync_agent_extension

                sync_agent_extension(agent)

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login"""
    username = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """Authenticate user"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                'Must include "username" and "password".',
                code='authorization'
            )
        
        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Check passwords match"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs
    
    def validate_old_password(self, value):
        """Check old password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Check passwords match"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs
