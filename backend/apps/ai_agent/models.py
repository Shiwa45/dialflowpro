"""
AI Agent models.

A tenant with an AI subscription can create AIAgents. Each AIAgent bundles:
  * the voice pipeline config (STT / TTS / language / speaker),
  * the 'brain' config (LLM provider + model + behaviour),
  * a knowledge base the admin fills with product details (used as RAG /
    structured system-prompt context — note: this is retrieval grounding, not
    model fine-tuning),
  * escalation rules (when to transfer to a human / arrange a callback).

Runtime call data is captured in AICallSession + AITranscriptTurn so the media
layer (Phase 2, LiveKit worker) has a place to write and the admin can review.

All models live in the TENANT schema (see settings TENANT_APPS), so rows are
naturally isolated per tenant. The subscription gate is enforced in the API
layer via the AISubscription row.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel
from .constants import (
    LLMProvider, SarvamLLMModel, GeminiModel, TTSModel, STTModel, STTMode,
    Language, AIAgentStatus, CallOutcome, KBSourceType, TransferReason,
)


class AISubscription(TimeStampedModel):
    """
    Per-tenant entitlement to the AI agent feature. One row per tenant.
    The tenant admin can only create/run AI agents while `is_active` and within
    `max_agents` / `monthly_minute_quota`.
    """
    tenant = models.OneToOneField(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="ai_subscription",
        verbose_name=_("tenant"),
    )
    is_active = models.BooleanField(default=False, verbose_name=_("active"))
    plan_name = models.CharField(max_length=80, default="standard")
    max_agents = models.PositiveIntegerField(default=1)
    monthly_minute_quota = models.PositiveIntegerField(
        default=1000, help_text=_("AI talk-minutes per month")
    )
    minutes_used_this_period = models.PositiveIntegerField(default=0)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "ai_subscription"
        verbose_name = _("AI subscription")

    def __str__(self):
        return f"AI sub for tenant {self.tenant_id} ({'on' if self.is_active else 'off'})"

    @property
    def minutes_remaining(self) -> int:
        return max(0, self.monthly_minute_quota - self.minutes_used_this_period)

    @property
    def quota_exhausted(self) -> bool:
        return self.minutes_used_this_period >= self.monthly_minute_quota


class AIAgent(TimeStampedModel):
    """A configured AI voice agent."""
    name = models.CharField(max_length=120, verbose_name=_("agent name"))
    description = models.TextField(blank=True)
    status = models.IntegerField(
        choices=AIAgentStatus.choices, default=AIAgentStatus.DRAFT
    )

    # Owner (tenant admin who created it)
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="ai_agents"
    )

    # ---- Persona / behaviour ---- #
    CALL_DIRECTION_CHOICES = (
        ("inbound", _("Inbound — answers customer calls")),
        ("outbound", _("Outbound — sales executive who calls customers")),
    )
    call_direction = models.CharField(
        max_length=10, choices=CALL_DIRECTION_CHOICES, default="inbound",
        help_text=_("Outbound agents lead the conversation and pitch; inbound agents assist callers"),
    )

    persona_name = models.CharField(
        max_length=80, default="Assistant",
        help_text=_("Name the AI uses to introduce itself"),
    )
    greeting = models.TextField(
        default="Hello! How can I help you today?",
        help_text=_("First thing the AI says when it answers"),
    )
    system_prompt = models.TextField(
        blank=True,
        help_text=_("Base instructions. Knowledge base is appended automatically."),
    )
    # 0.0-2.0 — passed to whichever LLM
    temperature = models.FloatField(default=0.6)
    max_response_tokens = models.PositiveIntegerField(default=300)

    # ---- LLM (brain), configurable per agent ---- #
    llm_provider = models.CharField(
        max_length=20, choices=LLMProvider.choices, default=LLMProvider.SARVAM
    )
    sarvam_llm_model = models.CharField(
        max_length=30, choices=SarvamLLMModel.choices,
        default=SarvamLLMModel.SARVAM_30B, blank=True,
    )
    gemini_model = models.CharField(
        max_length=40, choices=GeminiModel.choices,
        default=GeminiModel.GEMINI_FLASH, blank=True,
    )
    enable_thinking = models.BooleanField(
        default=False,
        help_text=_("Sarvam hybrid 'think' mode / Gemini reasoning for hard queries"),
    )

    # ---- Voice pipeline (Sarvam) ---- #
    primary_language = models.CharField(
        max_length=10, choices=Language.choices, default=Language.HI_IN
    )
    auto_detect_language = models.BooleanField(default=True)
    stt_model = models.CharField(
        max_length=20, choices=STTModel.choices, default=STTModel.SAARAS_V3
    )
    stt_mode = models.CharField(
        max_length=15, choices=STTMode.choices, default=STTMode.TRANSCRIBE
    )
    tts_model = models.CharField(
        max_length=15, choices=TTSModel.choices, default=TTSModel.BULBUL_V3
    )
    tts_speaker = models.CharField(
        max_length=30, default="manan",
        help_text=_("Bulbul speaker id (lowercase, must match model)"),
    )
    tts_pace = models.FloatField(default=1.0, help_text=_("0.5-2.0 for v3"))
    tts_temperature = models.FloatField(default=0.6, help_text=_("v3 only, 0.01-2.0"))

    # ---- Escalation / routing ---- #
    allow_human_transfer = models.BooleanField(default=True)
    transfer_queue = models.ForeignKey(
        "callcenter.Queue", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ai_transfer_agents",
        help_text=_("Human queue to transfer to when escalating"),
    )
    allow_callback = models.BooleanField(
        default=True,
        help_text=_("If no human available, offer to schedule a callback"),
    )
    confidence_transfer_threshold = models.FloatField(
        default=0.4,
        help_text=_("Transfer to human if AI confidence drops below this (0-1)"),
    )
    max_call_duration_seconds = models.PositiveIntegerField(default=600)

    # ---- Knowledge base indexing state ---- #
    kb_last_indexed = models.DateTimeField(null=True, blank=True)
    kb_chunk_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ai_agent"
        verbose_name = _("AI agent")
        ordering = ["-created_date"]

    def __str__(self):
        return self.name

    @property
    def active_llm_model(self) -> str:
        if self.llm_provider == LLMProvider.GEMINI:
            return self.gemini_model
        return self.sarvam_llm_model


class AIKnowledgeItem(TimeStampedModel):
    """
    A single piece of business knowledge the admin adds to 'train' the agent.

    On save these are chunked + embedded into AIKnowledgeChunk for retrieval at
    call time (Phase 2). Product details, FAQs, free-form notes and uploaded doc
    extracts all land here.
    """
    agent = models.ForeignKey(
        AIAgent, on_delete=models.CASCADE, related_name="knowledge_items"
    )
    source_type = models.CharField(
        max_length=15, choices=KBSourceType.choices, default=KBSourceType.PRODUCT
    )
    title = models.CharField(max_length=200)
    content = models.TextField(help_text=_("The knowledge text the AI can draw on"))

    # Structured product fields (optional, used when source_type=product)
    product_name = models.CharField(max_length=200, blank=True)
    product_price = models.CharField(max_length=80, blank=True)
    product_attributes = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ai_knowledge_item"
        verbose_name = _("AI knowledge item")
        ordering = ["-created_date"]

    def __str__(self):
        return f"{self.get_source_type_display()}: {self.title}"


class AIKnowledgeChunk(TimeStampedModel):
    """
    Embedded retrieval chunk derived from an AIKnowledgeItem.

    `embedding` is stored as JSON for portability (no pgvector dependency in
    Phase 1). The Phase 2 retriever loads these and does cosine similarity; if
    you later add pgvector, swap this field for a VectorField with no API change.
    """
    agent = models.ForeignKey(
        AIAgent, on_delete=models.CASCADE, related_name="knowledge_chunks"
    )
    item = models.ForeignKey(
        AIKnowledgeItem, on_delete=models.CASCADE, related_name="chunks"
    )
    text = models.TextField()
    embedding = models.JSONField(null=True, blank=True)
    token_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ai_knowledge_chunk"
        indexes = [models.Index(fields=["agent"])]


class AICallSession(TimeStampedModel):
    """
    One AI-handled call. Written by the media worker (Phase 2); readable now in
    the admin so the UI is complete from day one.
    """
    agent = models.ForeignKey(
        AIAgent, on_delete=models.CASCADE, related_name="call_sessions"
    )
    # Link back to telephony
    call_uuid = models.CharField(max_length=120, db_index=True, blank=True)
    livekit_room = models.CharField(max_length=160, blank=True)
    caller_number = models.CharField(max_length=64, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    outcome = models.CharField(
        max_length=15, choices=CallOutcome.choices, blank=True
    )
    detected_language = models.CharField(max_length=10, blank=True)
    transferred_to = models.ForeignKey(
        "callcenter.Agent", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ai_handoffs",
    )
    transfer_reason = models.CharField(
        max_length=20, choices=TransferReason.choices, blank=True
    )
    sentiment_score = models.FloatField(null=True, blank=True)
    summary = models.TextField(blank=True)

    class Meta:
        db_table = "ai_call_session"
        verbose_name = _("AI call session")
        ordering = ["-created_date"]
        indexes = [models.Index(fields=["agent", "outcome"])]

    def __str__(self):
        return f"AICall {self.call_uuid or self.id} [{self.outcome or 'live'}]"


class AITranscriptTurn(TimeStampedModel):
    """A single utterance within an AI call (caller or AI)."""
    session = models.ForeignKey(
        AICallSession, on_delete=models.CASCADE, related_name="turns"
    )
    ROLE_CHOICES = (("caller", "Caller"), ("ai", "AI"), ("system", "System"))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    text = models.TextField()
    language = models.CharField(max_length=10, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_transcript_turn"
        ordering = ["started_at", "id"]


class AICallback(TimeStampedModel):
    """A callback the AI scheduled when no human was available."""
    agent = models.ForeignKey(
        AIAgent, on_delete=models.CASCADE, related_name="callbacks"
    )
    session = models.ForeignKey(
        AICallSession, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="callbacks",
    )
    caller_number = models.CharField(max_length=64)
    requested_for = models.DateTimeField(
        help_text=_("When the customer wants to be called back")
    )
    notes = models.TextField(blank=True)
    STATUS = (("pending", "Pending"), ("done", "Completed"), ("cancelled", "Cancelled"))
    status = models.CharField(max_length=12, choices=STATUS, default="pending")
    assigned_agent = models.ForeignKey(
        "callcenter.Agent", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ai_callbacks",
    )

    class Meta:
        db_table = "ai_callback"
        verbose_name = _("AI callback")
        ordering = ["requested_for"]
