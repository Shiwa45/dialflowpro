# ============================================================================
# WIRING SNIPPETS — apply these to the existing project (do not overwrite files)
# ============================================================================

# ---------------------------------------------------------------------------
# 1. backend/config/settings/base.py
#    Add the app to TENANT_APPS (each tenant gets its own AI data, isolated).
# ---------------------------------------------------------------------------
TENANT_APPS = [
    # ... existing ...
    "apps.callcenter",
    "apps.ai_agent",          # <-- ADD
]

# AI provider keys (read from .env). Per-tenant keys can be added later;
# these are the platform-level defaults the media worker (Phase 2) uses.
SARVAM_API_KEY = env("SARVAM_API_KEY", default="")
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")

# LiveKit (Phase 2 media worker)
LIVEKIT_URL = env("LIVEKIT_URL", default="")
LIVEKIT_API_KEY = env("LIVEKIT_API_KEY", default="")
LIVEKIT_API_SECRET = env("LIVEKIT_API_SECRET", default="")


# ---------------------------------------------------------------------------
# 2. backend/config/urls.py
#    Mount the AI API under /api/ai/
# ---------------------------------------------------------------------------
# urlpatterns = [
#     ...
#     path("api/ai/", include("apps.ai_agent.urls")),
# ]


# ---------------------------------------------------------------------------
# 3. frontend/src/App.tsx  (admin routes — managers/superadmins only)
# ---------------------------------------------------------------------------
# import { AIAgentsPage } from "@/pages/admin/ai/AIAgentsPage"
# import { AIAgentBuilder } from "@/pages/admin/ai/AIAgentBuilder"
#
# <Route path="ai-agents" element={<AIAgentsPage />} />
# <Route path="ai-agents/new" element={<AIAgentBuilder />} />
# <Route path="ai-agents/:id" element={<AIAgentBuilder />} />
#
# Add a sidebar link to /ai-agents (e.g. with the Bot icon from lucide-react).


# ---------------------------------------------------------------------------
# 4. Provision a subscription (server-side; tenant admins cannot self-grant)
# ---------------------------------------------------------------------------
#   python manage.py provision_ai_subscription --schema <tenant> \
#       --plan standard --max-agents 3 --minutes 5000 --active
