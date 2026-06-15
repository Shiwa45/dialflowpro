# DialFlow Pro — AI Voice Agents (Phase 1: Data Model + Admin UI + Config)

This delivers the full configuration layer for AI voice agents: tenant
subscription gating, agent CRUD, the voice/brain/escalation config, and the
knowledge base ("training") — everything except the live media pipeline, which
is Phase 2 (specced in detail at the end so the schema we just built slots in
without rework).

## What "train the model" actually means here

None of Sarvam, Gemini, or any production AI dialer fine-tunes model weights on
your product data at call time. "Training" = **retrieval grounding**: the
product details / FAQs you add become a knowledge base that is (a) summarised
into the system prompt and (b) retrieved per-question at call time. This is the
correct, reliable approach — the AI can't "forget" or hallucinate your catalog
because the facts are injected fresh each turn. `brain.py` builds the prompt;
`tasks.py` chunks the knowledge; Phase 2 adds embeddings to the same chunks.

## Architecture decisions (locked for this build)

- **Media transport:** LiveKit Agents (Sarvam-official). FreeSWITCH bridges to
  LiveKit over SIP; the Sarvam plugins handle STT, VAD, barge-in and turn-taking
  — the hard real-time parts you don't want to hand-roll.
- **LLM:** configurable per agent (Sarvam `sarvam-105b/30b/m` or Gemini),
  stored on `AIAgent.llm_provider` + model fields.
- **STT:** Saaras v3, 8 kHz telephony PCM, `high_vad_sensitivity` + `vad_signals`
  for barge-in (per Sarvam streaming docs).
- **TTS:** Bulbul v3, mulaw/8 kHz for telephony, 30+ Indian-language voices.

## Files in this patch

### Backend — new app `apps/ai_agent/`
| File | Purpose |
|------|---------|
| `constants.py` | provider/model/voice/language choices (validated against Sarvam docs) |
| `models.py` | `AISubscription`, `AIAgent`, `AIKnowledgeItem`, `AIKnowledgeChunk`, `AICallSession`, `AITranscriptTurn`, `AICallback` |
| `serializers.py` | DRF serializers + speaker/pace/provider validation |
| `permissions.py` | `HasActiveAISubscription`, `IsTenantAdminForAI` |
| `views.py` | agent CRUD, knowledge, sessions, callbacks, subscription; `activate`/`pause`/`train`/`preview_prompt` actions |
| `brain.py` | system-prompt assembly + retrieval (lexical now, embeddings in P2) |
| `tasks.py` | Celery KB indexing; `embed_text` hook for P2 |
| `migrations/0001_initial.py` | schema |
| `management/commands/provision_ai_subscription.py` | server-side subscription provisioning |

### Frontend — new
| File | Purpose |
|------|---------|
| `types/aiAgent.ts` | types + language/speaker/model constants |
| `hooks/useAIAgents.ts` | subscription, agent CRUD, knowledge hooks |
| `pages/admin/ai/AIAgentsPage.tsx` | agent list + subscription gate |
| `pages/admin/ai/AIAgentBuilder.tsx` | config (Brain/Voice/Escalation/Knowledge tabs) |

### Wiring
See `docs/WIRING.py` for the 4 edits to existing files (settings, urls, routes,
provisioning command).

## Install (Phase 1)

1. Copy `apps/ai_agent/` into `backend/apps/` and the frontend files into place.
2. Apply the 4 edits in `docs/WIRING.py`.
3. Add to `.env`: `SARVAM_API_KEY`, `GEMINI_API_KEY` (LiveKit keys for P2).
4. Migrate: this app is tenant-scoped, so run the tenant migration:
   ```bash
   python manage.py migrate_schemas --tenant
   ```
5. Grant a tenant access:
   ```bash
   python manage.py provision_ai_subscription --schema acme --max-agents 3 --minutes 5000 --active
   ```
6. As a manager in that tenant, open **AI Agents → Create**, configure voice +
   brain, add product/FAQ knowledge, hit **Train / Re-index**, then **Activate**.

No new Python deps for Phase 1 (uses existing DRF/Celery). `preview_prompt`
lets you see exactly what the LLM will receive before going live.

## API surface (Phase 1)

```
GET    /api/ai/subscription/                 tenant entitlement + usage
GET    /api/ai/agents/                        list agents
POST   /api/ai/agents/                        create (gated by active sub + max_agents)
GET    /api/ai/agents/{id}/                    retrieve
PATCH  /api/ai/agents/{id}/                    update config
POST   /api/ai/agents/{id}/activate/           go live (requires >=1 KB item)
POST   /api/ai/agents/{id}/pause/
POST   /api/ai/agents/{id}/train/              (re)index knowledge base
GET    /api/ai/agents/{id}/preview_prompt/     assembled system prompt
GET/POST /api/ai/knowledge/?agent={id}         knowledge items
GET    /api/ai/sessions/?agent={id}            call history (written by P2)
GET/POST /api/ai/callbacks/                     AI-scheduled callbacks
```

---

# Phase 2 — Media Worker (spec, to build next)

The schema above already has the write targets (`AICallSession`,
`AITranscriptTurn`, `AICallback`, `livekit_room`, `call_uuid`). Phase 2 is a
standalone Python worker; the Django app does not change.

## Call flow

```
Caller → FreeSWITCH (inbound DID)
   → dialplan routes AI-enabled DIDs to a SIP bridge into LiveKit
   → LiveKit room created; AI worker (livekit-agents) joins as the agent
   → loop:  Sarvam STT (saaras:v3, 8kHz, vad_signals)
            → retrieve_context(agent, transcript)  [brain.py, shared]
            → LLM (Sarvam or Gemini per agent.llm_provider) with tools:
                 transfer_to_human(reason)
                 schedule_callback(when, notes)
            → Sarvam TTS (bulbul:v3, mulaw) streamed back into the room
            → barge-in: START_SPEECH event stops TTS playback
   → on transfer_to_human: SIP REFER / FreeSWITCH bridge to agent.transfer_queue
       (reuse the existing callcenter routing). If none available and
       agent.allow_callback → schedule_callback writes an AICallback row.
   → on hangup: worker writes AICallSession (outcome, duration, summary) +
       AITranscriptTurn rows; increments AISubscription.minutes_used_this_period.
```

## Worker components to build

1. **FreeSWITCH ↔ LiveKit SIP bridge** — LiveKit SIP inbound trunk pointed at a
   FreeSWITCH gateway; dialplan sends AI DIDs there. (No `mod_audio_fork`
   needed — LiveKit handles media.)
2. **`livekit-agents` worker** (`pip install "livekit-agents[sarvam]"`) using the
   per-agent config pulled from the Django API: language, speaker, STT/TTS
   models, LLM provider/model, greeting, `max_call_duration_seconds`.
   Apply Sarvam's documented best practices: `flush_signal=True`,
   `turn_detection="stt"`, `min_endpointing_delay=0.07`, no VAD on the session.
3. **LLM adapter** — for Sarvam use the OpenAI-compatible `/chat/completions`
   (`base_url=https://api.sarvam.ai/v1`, models `sarvam-105b/30b/m`,
   `reasoning_effort` for thinking mode). For Gemini use the LiveKit Gemini
   plugin or REST. Both get the same tool definitions so escalation/callback
   work identically.
4. **Embeddings** — implement `tasks.embed_text` against your chosen embedding
   endpoint; `retrieve_context` switches from lexical to cosine automatically.
5. **Subscription metering** — decrement minutes; when
   `AISubscription.quota_exhausted`, the worker declines new AI calls and falls
   back to the normal human queue.

## Why this split is safe

Phase 1 is fully usable and testable on its own (configure, preview the exact
prompt, review schema). Phase 2 only *reads* the config and *writes* call rows —
it never alters the models or the admin UI, so we can build and deploy it
without touching what you're approving now.
```
