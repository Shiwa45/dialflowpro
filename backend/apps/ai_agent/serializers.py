"""Serializers for the AI Agent app."""
from rest_framework import serializers

from .models import (
    AISubscription, AIAgent, AIKnowledgeItem, AICallSession,
    AITranscriptTurn, AICallback,
)
from .constants import (
    LLMProvider, TTSModel, BULBUL_V3_SPEAKERS, BULBUL_V2_SPEAKERS,
)


class AISubscriptionSerializer(serializers.ModelSerializer):
    minutes_remaining = serializers.IntegerField(read_only=True)
    quota_exhausted = serializers.BooleanField(read_only=True)

    class Meta:
        model = AISubscription
        fields = [
            "id", "is_active", "plan_name", "max_agents",
            "monthly_minute_quota", "minutes_used_this_period",
            "minutes_remaining", "quota_exhausted",
            "period_start", "period_end",
        ]
        read_only_fields = fields  # tenant admin reads; provisioning is server-side


class AIKnowledgeItemSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(
        source="get_source_type_display", read_only=True
    )

    class Meta:
        model = AIKnowledgeItem
        fields = [
            "id", "agent", "source_type", "source_type_display", "title",
            "content", "product_name", "product_price", "product_attributes",
            "is_active", "created_date", "updated_date",
        ]
        read_only_fields = ["id", "created_date", "updated_date"]


class AIAgentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    active_llm_model = serializers.CharField(read_only=True)
    knowledge_count = serializers.SerializerMethodField()

    class Meta:
        model = AIAgent
        fields = [
            "id", "name", "description", "status", "status_display",
            "call_direction",
            "persona_name", "greeting", "system_prompt", "temperature",
            "max_response_tokens",
            "llm_provider", "sarvam_llm_model", "gemini_model",
            "enable_thinking", "active_llm_model",
            "primary_language", "auto_detect_language",
            "stt_model", "stt_mode", "tts_model", "tts_speaker",
            "tts_pace", "tts_temperature",
            "allow_human_transfer", "transfer_queue", "allow_callback",
            "confidence_transfer_threshold", "max_call_duration_seconds",
            "kb_last_indexed", "kb_chunk_count", "knowledge_count",
            "created_date", "updated_date",
        ]
        read_only_fields = [
            "id", "kb_last_indexed", "kb_chunk_count",
            "created_date", "updated_date",
        ]

    def get_knowledge_count(self, obj):
        return obj.knowledge_items.filter(is_active=True).count()

    def validate(self, attrs):
        # Speaker must be valid for the chosen TTS model.
        tts_model = attrs.get("tts_model") or getattr(self.instance, "tts_model", TTSModel.BULBUL_V3)
        speaker = attrs.get("tts_speaker") or getattr(self.instance, "tts_speaker", "")
        if speaker:
            valid = BULBUL_V3_SPEAKERS if tts_model == TTSModel.BULBUL_V3 else BULBUL_V2_SPEAKERS
            if speaker.lower() not in valid:
                raise serializers.ValidationError({
                    "tts_speaker": f"'{speaker}' is not a valid speaker for {tts_model}."
                })

        # Pace range depends on model.
        pace = attrs.get("tts_pace")
        if pace is not None:
            lo, hi = (0.5, 2.0) if tts_model == TTSModel.BULBUL_V3 else (0.3, 3.0)
            if not (lo <= pace <= hi):
                raise serializers.ValidationError({
                    "tts_pace": f"Pace for {tts_model} must be between {lo} and {hi}."
                })

        # Make sure the right LLM model field is populated for the provider.
        provider = attrs.get("llm_provider") or getattr(self.instance, "llm_provider", LLMProvider.SARVAM)
        if provider == LLMProvider.SARVAM and not (
            attrs.get("sarvam_llm_model") or getattr(self.instance, "sarvam_llm_model", "")
        ):
            raise serializers.ValidationError({"sarvam_llm_model": "Required for Sarvam provider."})
        if provider == LLMProvider.GEMINI and not (
            attrs.get("gemini_model") or getattr(self.instance, "gemini_model", "")
        ):
            raise serializers.ValidationError({"gemini_model": "Required for Gemini provider."})
        return attrs


class AITranscriptTurnSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITranscriptTurn
        fields = ["id", "role", "text", "language", "confidence", "started_at"]


class AICallSessionSerializer(serializers.ModelSerializer):
    outcome_display = serializers.CharField(source="get_outcome_display", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    turns = AITranscriptTurnSerializer(many=True, read_only=True)

    class Meta:
        model = AICallSession
        fields = [
            "id", "agent", "agent_name", "call_uuid", "caller_number",
            "started_at", "ended_at", "duration_seconds",
            "outcome", "outcome_display", "detected_language",
            "transferred_to", "transfer_reason", "sentiment_score",
            "summary", "turns", "created_date",
        ]
        read_only_fields = fields


class AICallSessionListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views (no transcript)."""
    outcome_display = serializers.CharField(source="get_outcome_display", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = AICallSession
        fields = [
            "id", "agent", "agent_name", "caller_number",
            "started_at", "duration_seconds", "outcome", "outcome_display",
            "detected_language", "sentiment_score",
        ]


class AICallbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AICallback
        fields = [
            "id", "agent", "session", "caller_number", "requested_for",
            "notes", "status", "assigned_agent", "created_date",
        ]
        read_only_fields = ["id", "created_date"]
