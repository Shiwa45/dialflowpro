"""Serializers for AudioFile"""
from rest_framework import serializers
from .models import AudioFile


class AudioFileSerializer(serializers.ModelSerializer):
    """Serializer for AudioFile with upload"""
    audio_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioFile
        fields = [
            'id', 'name', 'description', 'audio_file', 'audio_url',
            'user', 'duration', 'file_size', 'format',
            'sample_rate', 'channels', 'is_tts', 'tts_text',
            'tts_language', 'created_date', 'updated_date'
        ]
        read_only_fields = [
            'id', 'user', 'duration', 'file_size', 'format',
            'sample_rate', 'channels', 'created_date', 'updated_date'
        ]
    
    def get_audio_url(self, obj):
        """Return full URL for audio file"""
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None


class TTSSerializer(serializers.Serializer):
    """Serializer for TTS generation"""
    name = serializers.CharField(max_length=255)
    text = serializers.CharField()
    language = serializers.CharField(default='en-US', max_length=10)
