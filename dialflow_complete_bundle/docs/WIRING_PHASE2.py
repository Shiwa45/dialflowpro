# ============================================================================
# PHASE 2 WIRING — add to backend/config/settings/base.py
# ============================================================================

# Shared secret the media worker uses to authenticate to the worker REST surface.
# MUST match AI_WORKER_TOKEN in the worker's .env. Generate a long random value.
AI_WORKER_TOKEN = env("AI_WORKER_TOKEN", default="")

# Embedding provider for the knowledge base. One of: sarvam | gemini | local | none
#   sarvam -> uses SARVAM_API_KEY
#   gemini -> uses GEMINI_API_KEY
#   local  -> sentence-transformers (pip install sentence-transformers); no API
#   none   -> embeddings disabled; retrieval uses lexical matching (still works)
AI_EMBEDDING_PROVIDER = env("AI_EMBEDDING_PROVIDER", default="none")
AI_LOCAL_EMBEDDING_MODEL = env("AI_LOCAL_EMBEDDING_MODEL", default="all-MiniLM-L6-v2")
AI_GEMINI_EMBEDDING_MODEL = env("AI_GEMINI_EMBEDDING_MODEL", default="text-embedding-004")

# (SARVAM_API_KEY / GEMINI_API_KEY were already added in Phase 1.)
# (LIVEKIT_* were already added in Phase 1 for completeness.)

# ----------------------------------------------------------------------------
# NOTE on tenant schema switching in worker_api.py
# ----------------------------------------------------------------------------
# The worker endpoints call connection.set_schema(<schema>) based on the
# X-Tenant header. Ensure your django-tenants version exposes set_schema on the
# connection (it does in django-tenants 3.x). The endpoints are CSRF-exempt via
# DRF @api_view + AllowAny + shared-secret check, so they work without a session.

# No new INSTALLED_APPS entries — Phase 2 only adds files to the existing
# apps.ai_agent app plus the standalone ai_worker/ process.
