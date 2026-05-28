"""
AudioFile model for storing and managing audio files.
Supports TTS and audio conversion.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedModel


class AudioFile(TimeStampedModel):
    """
    Audio file for use in surveys and campaigns.
    Stores uploaded audio or TTS-generated audio.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_('name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description')
    )
    
    # Audio file
    audio_file = models.FileField(
        upload_to='audio/%Y/%m/%d/',
        verbose_name=_('audio file'),
        help_text=_('Audio file (WAV, MP3, etc.)')
    )
    
    # User owner
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='audio_files',
        verbose_name=_('user')
    )
    
    # Metadata
    duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('duration'),
        help_text=_('Duration in seconds')
    )
    
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name=_('file size'),
        help_text=_('Size in bytes')
    )
    
    # Audio format info
    format = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('format'),
        help_text=_('Audio format (wav, mp3, etc.)')
    )
    
    sample_rate = models.PositiveIntegerField(
        default=8000,
        verbose_name=_('sample rate'),
        help_text=_('Sample rate in Hz (8000 for telephony)')
    )
    
    channels = models.PositiveIntegerField(
        default=1,
        verbose_name=_('channels'),
        help_text=_('Number of audio channels (1=mono, 2=stereo)')
    )
    
    # TTS fields
    is_tts = models.BooleanField(
        default=False,
        verbose_name=_('TTS generated'),
        help_text=_('Was this file generated via TTS?')
    )
    
    tts_text = models.TextField(
        blank=True,
        verbose_name=_('TTS text'),
        help_text=_('Text used to generate TTS audio')
    )
    
    tts_language = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('TTS language'),
        help_text=_('Language code for TTS (en-US, es-ES, etc.)')
    )
    
    class Meta:
        db_table = 'audiofile'
        verbose_name = _('audio file')
        verbose_name_plural = _('audio files')
        ordering = ['-created_date']
    
    def __str__(self):
        return self.name
