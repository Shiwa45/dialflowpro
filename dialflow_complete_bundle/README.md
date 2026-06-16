# DialFlow Pro — Complete Patch Bundle

This single archive contains **all four patches** built in this session, merged
into one tree. Every file drops into your existing DialFlow Pro repo (paths
mirror it). The only new top-level addition is the `ai_worker/` sibling folder
(a standalone process, like `fs_event_listener`). Nothing here is a separate
project.

Where files were superseded across phases (`apps/ai_agent/tasks.py` and
`apps/ai_agent/urls.py`), this bundle contains the **final** version.

## Contents by patch

### A. Real-time agent tracking & supervisor monitoring
The missing `group_send` broadcast layer + FreeSWITCH event source, so live
agent status actually updates, plus listen/whisper/barge/takeover.
- `backend/apps/callcenter/`: `realtime.py`, `signals.py`, `monitoring.py`,
  `monitor_views.py`, `consumers.py`, `apps.py`, `routing.py`, `urls.py`,
  `management/commands/fs_event_listener.py`
- `backend/scripts/freeswitch_realtime.conf.xml`
- `frontend/src/hooks/useAgentTracking.ts`,
  `frontend/src/pages/admin/LiveAgentTracking.tsx`
- Guide: `REALTIME_TRACKING_README.md`

### B. AI Agents — Phase 1 (data model + admin UI + config)
- `backend/apps/ai_agent/` full app (models, serializers, views, permissions,
  brain, tasks, constants, migration, admin, provisioning command)
- `frontend/src/types/aiAgent.ts`, `frontend/src/hooks/useAIAgents.ts`,
  `frontend/src/pages/admin/ai/AIAgentsPage.tsx`,
  `frontend/src/pages/admin/ai/AIAgentBuilder.tsx`
- Guide: `AI_AGENTS_README.md`; wiring: `docs/WIRING.py`

### C. AI Agents — Phase 2 (LiveKit media worker, end-to-end)
- `ai_worker/` standalone process (config, llm_adapter, agent, transfer, main,
  SIP setup script, requirements, .env.example)
- `backend/apps/ai_agent/`: `embeddings.py`, `worker_api.py`, final `tasks.py`,
  final `urls.py`
- `backend/scripts/dialplan_ai_bridge.xml`
- Guide: `AI_AGENTS_PHASE2_README.md`; wiring: `docs/WIRING_PHASE2.py`

### D. AI Agents — Phase 3 (AI call review UI)
- `frontend/src/hooks/useAISessions.ts`,
  `frontend/src/pages/admin/ai/AICallReviewPage.tsx`
- `ai_worker/summary.py` (optional post-call summary + sentiment)
- Guide: `AI_AGENTS_PHASE3_README.md`; wiring: `docs/WIRING_PHASE3.py`

## Install order (recommended)

1. **Real-time tracking (A)** — independent; copy files, apply its README,
   run `python manage.py fs_event_listener` alongside Daphne/Celery.
2. **AI Phase 1 (B)** — add `apps.ai_agent` to `TENANT_APPS`, mount
   `path("api/ai/", include("apps.ai_agent.urls"))`, add the three React routes,
   `migrate_schemas --tenant`, provision a subscription.
3. **AI Phase 2 (C)** — apply `docs/WIRING_PHASE2.py` (AI_WORKER_TOKEN,
   embedding provider), set up LiveKit + dispatch rule, FreeSWITCH dialplan,
   run the `ai_worker` process.
4. **AI Phase 3 (D)** — add the `/ai-calls` route + sidebar link; optionally
   enable `AI_POST_CALL_SUMMARY`.

Each phase's own README has the detailed steps, call-flow traces, and
operational notes. The wiring files in `docs/` list the exact edits to existing
project files (none of which are included here, so nothing of yours is
overwritten).

## Verification status

Every Python file in this bundle byte-compiles cleanly. That is not the same as
a live call working: the real-time and media pieces depend on live FreeSWITCH /
LiveKit / Sarvam infrastructure that must be smoke-tested on a single DID before
rollout. Two specific things to verify against live services: the Sarvam
embeddings response shape in `embeddings.py`, and the installed
`livekit-agents[sarvam]` plugin version against `ai_worker/agent.py`.
