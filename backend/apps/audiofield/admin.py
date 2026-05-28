"""Django admin for AudioFile"""
from django.contrib import admin
from .models import AudioFile


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'format', 'duration', 'file_size', 'is_tts', 'created_date']
    list_filter = ['is_tts', 'format', 'created_date']
    search_fields = ['name', 'user__username', 'tts_text']
    readonly_fields = ['duration', 'file_size', 'format', 'sample_rate', 'channels', 'created_date', 'updated_date']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'audio_file', 'user')
        }),
        ('Metadata', {
            'fields': ('duration', 'file_size', 'format', 'sample_rate', 'channels')
        }),
        ('TTS', {
            'fields': ('is_tts', 'tts_text', 'tts_language'),
            'classes': ('collapse',)
        }),
    )
