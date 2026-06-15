# DialFlow Pro — AI Voice Agents (Phase 3: AI Call Review UI)

A **patch** into your existing repo, completing the AI agent feature. It adds an
admin page to review what the AI did on every call, plus an optional post-call
summarizer for the worker.

## What this adds

- **AI Call Review** page (`/ai-calls`): a filterable history of AI-handled
  calls with metrics (total, containment %, transferred, callbacks, avg
  duration), a per-call **transcript drawer** (caller vs AI bubbles, language,
  outcome, transfer reason, AI summary), and a **Callbacks** tab where managers
  mark AI-scheduled callbacks done/cancelled.
- **Optional** `ai_worker/summary.py`: one extra LLM call at hangup to fill
  `summary` + `sentiment_score`, reusing the agent's own provider. Off by
  default (`AI_POST_CALL_SUMMARY`), so it never adds latency unless you want it.

## Files

### Frontend (into `frontend/src/`)
| File | Purpose |
|------|---------|
| `hooks/useAISessions.ts` | sessions list/detail + callbacks hooks |
| `pages/admin/ai/AICallReviewPage.tsx` | the review page (calls + callbacks tabs, transcript drawer) |

### Worker (optional, into `ai_worker/`)
| File | Purpose |
|------|---------|
| `summary.py` | post-call summary + sentiment (Sarvam or Gemini) |

### Wiring
`docs/WIRING_PHASE3.py` — one frontend route + sidebar link; optional 6-line
worker change to enable summaries.

## Install

1. Copy the two frontend files in.
2. Add the route + sidebar link from `docs/WIRING_PHASE3.py`. Done — the page
   works immediately against the Phase 1 `/api/ai/sessions/` and
   `/api/ai/callbacks/` endpoints. **No backend changes.**
3. (Optional) Drop `summary.py` into `ai_worker/`, set
   `AI_POST_CALL_SUMMARY=true`, and apply the 6-line shutdown-path change in the
   wiring doc to populate the Summary panel + Sentiment column.

## How it fits the whole feature

- **Phase 1** — data model, admin config UI, knowledge base, subscription gate.
- **Phase 2** — LiveKit media worker: live STT→RAG→LLM→TTS, transfer/callback,
  writes `AICallSession`/transcripts/callbacks back to Django.
- **Phase 3 (this)** — the admin reads those rows: review transcripts, measure
  containment, manage callbacks.

That closes the loop: configure the agent → it answers and logs calls → you
review and improve. Everything is a patch into the existing DialFlow Pro repo
(plus the `ai_worker/` sibling process from Phase 2); nothing is a separate
project.

## Suggested next improvements (not built)

- Date-range + agent filter on the review list (the list endpoint already
  accepts `?agent=`; add `?from=&to=` server-side when you want it).
- Export transcripts to CSV (reuse your existing CDR export pattern).
- A small per-agent analytics panel on the agent detail page (containment trend,
  top transfer reasons) sourced from the same sessions data.
