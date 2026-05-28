"""Django admin for Contact and Phonebook"""
from django.contrib import admin
from .models import Phonebook, Contact


@admin.register(Phonebook)
class PhonebookAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'phonebook_contacts', 'created_date']
    list_filter = ['created_date', 'user']
    search_fields = ['name', 'description']
    readonly_fields = ['created_date', 'updated_date']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['contact', 'full_name', 'email', 'phonebook', 'status', 'created_date']
    list_filter = ['status', 'phonebook', 'created_date']
    search_fields = ['contact', 'first_name', 'last_name', 'email']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['phonebook']
