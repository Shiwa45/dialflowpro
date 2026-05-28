"""
Views for Contact and Phonebook management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Phonebook, Contact
from .serializers import (
    PhonebookSerializer, ContactSerializer,
    ContactListSerializer, ContactImportSerializer
)
import csv
import io
import phonenumbers


class PhonebookViewSet(viewsets.ModelViewSet):
    """ViewSet for Phonebook CRUD"""
    queryset = Phonebook.objects.all()
    serializer_class = PhonebookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        """Filter by tenant"""
        user = self.request.user
        if user.is_superadmin:
            return Phonebook.objects.all()
        return Phonebook.objects.filter(user__tenant=user.tenant)
    
    def perform_create(self, serializer):
        """Set user automatically"""
        serializer.save(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Contact CRUD + CSV import"""
    queryset = Contact.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['phonebook', 'status']
    search_fields = ['contact', 'first_name', 'last_name', 'email']
    
    def get_queryset(self):
        """Filter by tenant"""
        user = self.request.user
        if user.is_superadmin:
            return Contact.objects.all()
        return Contact.objects.filter(phonebook__user__tenant=user.tenant)
    
    def get_serializer_class(self):
        """Use lightweight serializer for list"""
        if self.action == 'list':
            return ContactListSerializer
        return ContactSerializer
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """
        Import contacts from CSV.
        POST /api/contacts/contacts/import_csv/
        
        CSV format:
        contact,first_name,last_name,email,status
        +14155551234,John,Doe,john@example.com,1
        """
        serializer = ContactImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        csv_file = serializer.validated_data['csv_file']
        phonebook = serializer.validated_data['phonebook']
        skip_duplicates = serializer.validated_data['skip_duplicates']
        
        # Parse CSV
        decoded_file = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_file))
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                contact_number = row.get('contact', '').strip()
                
                if not contact_number:
                    continue
                
                # Parse and normalize phone number
                try:
                    parsed = phonenumbers.parse(contact_number, None)
                    if not phonenumbers.is_valid_number(parsed):
                        errors.append(f"Row {row_num}: Invalid phone number {contact_number}")
                        error_count += 1
                        continue
                    contact_number = phonenumbers.format_number(
                        parsed,
                        phonenumbers.PhoneNumberFormat.E164
                    )
                except phonenumbers.NumberParseException:
                    errors.append(f"Row {row_num}: Could not parse phone number {contact_number}")
                    error_count += 1
                    continue
                
                # Check for duplicate
                if skip_duplicates:
                    if Contact.objects.filter(
                        phonebook=phonebook,
                        contact=contact_number
                    ).exists():
                        skipped_count += 1
                        continue
                
                # Create contact
                Contact.objects.create(
                    phonebook=phonebook,
                    contact=contact_number,
                    first_name=row.get('first_name', '').strip(),
                    last_name=row.get('last_name', '').strip(),
                    email=row.get('email', '').strip(),
                    status=int(row.get('status', 1)),
                )
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1
        
        return Response({
            'created': created_count,
            'skipped': skipped_count,
            'errors': error_count,
            'error_details': errors[:20]  # Return first 20 errors only
        })
