"""
Constants for the AI Agent app.

These encode the choices that map directly onto the upstream provider APIs:
Sarvam (STT/TTS + optional LLM) and the configurable LLM backends. Values were
taken from the Sarvam docs (Bulbul v3 speakers, Saaras v3 languages, chat
models) so the admin UI never offers an option the provider will reject.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class LLMProvider(models.TextChoices):
    """The 'brain'. Configurable per agent."""
    SARVAM = "sarvam", _("Sarvam (Indic-native)")
    GEMINI = "gemini", _("Google Gemini")


class SarvamLLMModel(models.TextChoices):
    SARVAM_105B = "sarvam-105b", _("Sarvam 105B (flagship)")
    SARVAM_30B = "sarvam-30b", _("Sarvam 30B (balanced)")
    SARVAM_M = "sarvam-m", _("Sarvam-M 24B (legacy)")


class GeminiModel(models.TextChoices):
    GEMINI_FLASH = "gemini-2.0-flash", _("Gemini 2.0 Flash")
    GEMINI_PRO = "gemini-1.5-pro", _("Gemini 1.5 Pro")
    GEMINI_FLASH_15 = "gemini-1.5-flash", _("Gemini 1.5 Flash")


class TTSModel(models.TextChoices):
    BULBUL_V3 = "bulbul:v3", _("Bulbul v3 (recommended)")
    BULBUL_V2 = "bulbul:v2", _("Bulbul v2 (legacy)")


class STTModel(models.TextChoices):
    SAARAS_V3 = "saaras:v3", _("Saaras v3 (recommended)")
    SAARIKA_V25 = "saarika:v2.5", _("Saarika v2.5 (legacy)")


class STTMode(models.TextChoices):
    TRANSCRIBE = "transcribe", _("Transcribe (same language)")
    TRANSLATE = "translate", _("Translate to English")
    CODEMIX = "codemix", _("Code-mixed (Hinglish etc.)")


class Language(models.TextChoices):
    """BCP-47 codes accepted by both Sarvam STT and TTS."""
    AUTO = "unknown", _("Auto-detect")
    EN_IN = "en-IN", _("English (India)")
    HI_IN = "hi-IN", _("Hindi")
    BN_IN = "bn-IN", _("Bengali")
    TA_IN = "ta-IN", _("Tamil")
    TE_IN = "te-IN", _("Telugu")
    GU_IN = "gu-IN", _("Gujarati")
    KN_IN = "kn-IN", _("Kannada")
    ML_IN = "ml-IN", _("Malayalam")
    MR_IN = "mr-IN", _("Marathi")
    PA_IN = "pa-IN", _("Punjabi")
    OD_IN = "od-IN", _("Odia")


# Bulbul v3 speakers — MUST match the installed livekit-plugins-sarvam list
# (the plugin validates and rejects unknown speakers). Keep in sync with the
# media worker's plugin version.
BULBUL_V3_SPEAKERS = [
    "shubh", "ritu", "rahul", "pooja", "simran", "kavya", "amit", "ratan",
    "rohan", "dev", "ishita", "shreya", "manan", "sumit", "priya", "aditya",
    "kabir", "neha", "varun", "roopa", "aayan", "ashutosh", "advait", "amelia",
    "sophia", "suhani", "rupali", "tanya", "shruti", "kavitha",
]

BULBUL_V2_SPEAKERS = [
    "anushka", "manisha", "vidya", "arya",          # female
    "abhilash", "karun", "hitesh",                  # male
]


class AIAgentStatus(models.IntegerChoices):
    DRAFT = 0, _("Draft")          # being configured, not live
    ACTIVE = 1, _("Active")        # answering calls
    PAUSED = 2, _("Paused")        # temporarily disabled
    TRAINING = 3, _("Training")    # knowledge base being (re)indexed


class CallOutcome(models.TextChoices):
    """How an AI-handled call ended."""
    RESOLVED = "resolved", _("Resolved by AI")
    TRANSFERRED = "transferred", _("Transferred to human")
    CALLBACK = "callback", _("Callback scheduled")
    ABANDONED = "abandoned", _("Caller hung up")
    FAILED = "failed", _("Failed / error")


class KBSourceType(models.TextChoices):
    """Where a knowledge chunk came from."""
    PRODUCT = "product", _("Product detail")
    FAQ = "faq", _("FAQ")
    DOCUMENT = "document", _("Uploaded document")
    FREEFORM = "freeform", _("Free-form note")


class TransferReason(models.TextChoices):
    CUSTOMER_REQUEST = "customer_request", _("Customer asked for human")
    LOW_CONFIDENCE = "low_confidence", _("AI unsure")
    ESCALATION = "escalation", _("Policy escalation")
    SENTIMENT = "sentiment", _("Negative sentiment")
