"""Views for AudioFile management"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from .models import AudioFile
from .serializers import AudioFileSerializer, TTSSerializer
import os


class AudioFileViewSet(viewsets.ModelViewSet):
    """ViewSet for AudioFile CRUD and TTS"""
    serializer_class = AudioFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return AudioFile.objects.filter(user__tenant=user.tenant)
    
    def perform_create(self, serializer):
        """Set user and process audio"""
        audio_file = serializer.save(user=self.request.user)
        self._process_audio_metadata(audio_file)
    
    def _process_audio_metadata(self, audio_file):
        """Extract audio metadata using pydub"""
        try:
            # TODO: Install pydub and extract metadata
            # from pydub import AudioSegment
            # audio = AudioSegment.from_file(audio_file.audio_file.path)
            # audio_file.duration = len(audio) // 1000  # ms to seconds
            # audio_file.sample_rate = audio.frame_rate
            # audio_file.channels = audio.channels
            # audio_file.format = audio_file.audio_file.name.split('.')[-1]
            
            # For now, just set file size
            audio_file.file_size = audio_file.audio_file.size
            
            # Get format from filename
            if audio_file.audio_file.name:
                audio_file.format = audio_file.audio_file.name.split('.')[-1].lower()
            
            audio_file.save(update_fields=['file_size', 'format'])
        except Exception as e:
            # Log error but don't fail upload
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing audio metadata: {e}")
    
    @action(detail=False, methods=['post'])
    def generate_tts(self, request):
        """
        Generate audio from text using TTS.
        POST /api/audiofield/audio/generate_tts/
        
        Body:
        {
          "name": "Welcome message",
          "text": "Hello, welcome to our service",
          "language": "en-US"
        }
        """
        serializer = TTSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # TODO: Implement TTS
        # For now, return not implemented
        return Response(
            {
                'error': 'TTS not yet implemented',
                'message': 'Install Coqui TTS or Google TTS to enable this feature'
            },
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
        
        # Example implementation with Google TTS:
        # from google.cloud import texttospeech
        # client = texttospeech.TextToSpeechClient()
        # synthesis_input = texttospeech.SynthesisInput(text=serializer.validated_data['text'])
        # voice = texttospeech.VoiceSelectionParams(
        #     language_code=serializer.validated_data['language'],
        #     ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        # )
        # audio_config = texttospeech.AudioConfig(
        #     audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        #     sample_rate_hertz=8000
        # )
        # response = client.synthesize_speech(
        #     input=synthesis_input, voice=voice, audio_config=audio_config
        # )
        # 
        # # Create AudioFile
        # audio_file = AudioFile(
        #     name=serializer.validated_data['name'],
        #     user=request.user,
        #     is_tts=True,
        #     tts_text=serializer.validated_data['text'],
        #     tts_language=serializer.validated_data['language'],
        #     sample_rate=8000,
        #     channels=1,
        #     format='wav'
        # )
        # audio_file.audio_file.save(
        #     f"{serializer.validated_data['name']}.wav",
        #     ContentFile(response.audio_content)
        # )
        # audio_file.save()
        # 
        # return Response(AudioFileSerializer(audio_file).data)
