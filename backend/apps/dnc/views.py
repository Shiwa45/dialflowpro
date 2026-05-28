"""Views for DNC management"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from .models import DNC, DNCContact
from .serializers import DNCSerializer, DNCContactSerializer, DNCImportSerializer


class DNCViewSet(viewsets.ModelViewSet):
    """ViewSet for DNC CRUD"""
    serializer_class = DNCSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant, add counts"""
        user = self.request.user
        return DNC.objects.filter(
            user__tenant=user.tenant
        ).annotate(contact_count=Count('contacts'))
    
    def perform_create(self, serializer):
        """Set user from request"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def import_from_phonebook(self, request, pk=None):
        """
        Import contacts from phonebook into DNC list.
        POST /api/dnc/dnc/{id}/import_from_phonebook/
        Body: {"phonebook": 1}
        """
        dnc = self.get_object()
        serializer = DNCImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phonebook_id = serializer.validated_data['phonebook']
        
        # Import contacts from phonebook
        from apps.dialer_contact.models import Contact
        contacts = Contact.objects.filter(
            phonebook_id=phonebook_id,
            phonebook__user__tenant=request.user.tenant
        )
        
        created_count = 0
        for contact in contacts:
            _, created = DNCContact.objects.get_or_create(
                dnc=dnc,
                phone_number=contact.contact
            )
            if created:
                created_count += 1
        
        return Response({
            'status': 'imported',
            'total_contacts': contacts.count(),
            'new_contacts': created_count
        })
    
    @action(detail=True, methods=['post'])
    def add_number(self, request, pk=None):
        """
        Add single number to DNC list.
        POST /api/dnc/dnc/{id}/add_number/
        Body: {"phone_number": "+15551234567"}
        """
        dnc = self.get_object()
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response(
                {'error': 'phone_number required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contact, created = DNCContact.objects.get_or_create(
            dnc=dnc,
            phone_number=phone_number
        )
        
        return Response({
            'status': 'added' if created else 'already_exists',
            'phone_number': str(contact.phone_number)
        })
    
    @action(detail=True, methods=['post'])
    def remove_number(self, request, pk=None):
        """
        Remove number from DNC list.
        POST /api/dnc/dnc/{id}/remove_number/
        Body: {"phone_number": "+15551234567"}
        """
        dnc = self.get_object()
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response(
                {'error': 'phone_number required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = DNCContact.objects.filter(
            dnc=dnc,
            phone_number=phone_number
        ).delete()[0]
        
        return Response({
            'status': 'removed' if deleted_count > 0 else 'not_found',
            'phone_number': phone_number
        })


class DNCContactViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DNCContact (read-only)"""
    serializer_class = DNCContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant via DNC"""
        user = self.request.user
        return DNCContact.objects.filter(
            dnc__user__tenant=user.tenant
        ).select_related('dnc')
