# ============================================================================
# PHASE 3 WIRING
# ============================================================================

# ----------------------------------------------------------------------------
# 1. Frontend routes — frontend/src/App.tsx (admin routes, managers/superadmins)
# ----------------------------------------------------------------------------
# import { AICallReviewPage } from "@/pages/admin/ai/AICallReviewPage"
#
# <Route path="ai-calls" element={<AICallReviewPage />} />
#
# Add a sidebar link to /ai-calls (e.g. MessageSquare or Bot icon).
# The existing Phase 1 routes (/ai-agents, /ai-agents/:id) stay as-is.

# ----------------------------------------------------------------------------
# 2. No backend changes required for the review UI.
#    It consumes the Phase 1 endpoints already present:
#       GET /api/ai/sessions/            (list, optional ?agent=<id>)
#       GET /api/ai/sessions/{id}/       (detail incl. transcript turns)
#       GET /api/ai/callbacks/           (list)
#       PATCH /api/ai/callbacks/{id}/    (status updates)

# ----------------------------------------------------------------------------
# 3. OPTIONAL — populate summary + sentiment (ai_worker/summary.py)
#    Drop summary.py into ai_worker/, set in the worker's .env:
#       AI_POST_CALL_SUMMARY=true
#    Then in ai_worker/agent.py, make persist() async-aware or call the
#    summarizer just before save_result. Minimal change to the shutdown path:
#
#    # in DialFlowAIAgent.persist(), before building the payload:
#    #   (persist is sync; run the async summary via the worker loop, or
#    #    convert the shutdown callback to async — example below)
#
#    Replace the shutdown registration in main.py:
#        ctx.add_shutdown_callback(agent.persist)
#    with an async wrapper:
#
#        async def _on_shutdown():
#            from ai_worker.summary import summarize
#            extra = await summarize(
#                agent.transcript, agent.cfg,
#                sarvam_api_key=settings.sarvam_api_key,
#                gemini_api_key=settings.gemini_api_key,
#            )
#            if extra:
#                agent.summary = extra.get("summary", "")
#                agent.sentiment = extra.get("sentiment")
#            agent.persist()
#        ctx.add_shutdown_callback(_on_shutdown)
#
#    And include them in the save_result payload in persist():
#        "summary": getattr(self, "summary", ""),
#        "sentiment_score": getattr(self, "sentiment", None),
#
#    The worker_call_result endpoint (Phase 2) already accepts both fields, and
#    the review page already renders them — so with this on, the Summary panel
#    and Sentiment column populate automatically.
