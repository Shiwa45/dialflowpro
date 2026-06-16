# DialFlow Pro — AI Voice Agents (Phase 2: Media Worker, end-to-end)

This is a **patch** into your existing repo. It adds:
- files into the existing `backend/apps/ai_agent/` app (embeddings, worker REST,
  updated tasks/urls), and
- a new sibling folder `ai_worker/` — the standalone LiveKit media-worker
  process (like `fs_event_listener`, it's a separate long-running process, not
  Django request code).

Nothing from Phase 1 is replaced except `tasks.py` and `urls.py` (extended).

## What now works end-to-end

A caller dials an AI-enabled DID → FreeSWITCH bridges into LiveKit → the worker
answers as the configured AIAgent → real-time **Sarvam STT → RAG → LLM
(Sarvam/Gemini per agent) → Sarvam TTS** with barge-in → it can **transfer to a
human queue** or **schedule a callback** → on hangup the transcript, outcome and
**AI minutes used** are written back to Django (visible in the Phase 1 admin).

## Hybrid LiveKit (your requirement)

The worker reads `LIVEKIT_URL` + keys from env. Cloud now, self-hosted on your
office servers later = change three env values, restart the worker. No code
change. The FreeSWITCH gateway's `LIVEKIT_SIP_HOST` likewise just repoints.

## Pluggable embeddings (your requirement)

`AI_EMBEDDING_PROVIDER` = `sarvam` | `gemini` | `local` | `none`. The Django
indexer (`embeddings.py`) embeds knowledge chunks accordingly; the retriever
auto-uses vectors when present and falls back to lexical match otherwise, so the
agent works even with `none`.

## Files

### Backend (into `backend/apps/ai_agent/`)
| File | Change |
|------|--------|
| `embeddings.py` | NEW — pluggable provider (sarvam/gemini/local/none) |
| `tasks.py` | REPLACE — `embed_text` now delegates to the provider |
| `worker_api.py` | NEW — shared-secret worker REST (config/retrieve/result/callback) |
| `urls.py` | REPLACE — adds `worker/*` routes |
| `scripts/dialplan_ai_bridge.xml` | NEW — FreeSWITCH → LiveKit bridge |

### Worker (new sibling folder `ai_worker/`)
| File | Purpose |
|------|---------|
| `config.py` | env + Django API client (hybrid LiveKit) |
| `llm_adapter.py` | builds Sarvam(OpenAI-compatible) or Gemini LLM per agent |
| `agent.py` | the pipeline, RAG, transfer/callback tools, persistence |
| `transfer.py` | brings a human into the room via LiveKit SIP |
| `main.py` | entrypoint + dispatch + duration guard |
| `scripts/livekit_sip_setup.py` | one-time trunk + dispatch rule |
| `requirements.txt`, `.env.example` | deps + config template |

## Install

### 1. Backend
- Copy the backend files in. Apply `docs/WIRING_PHASE2.py` to settings.
- Mount stays the same as Phase 1 (`path("api/ai/", include("apps.ai_agent.urls"))`).
- If using `local` embeddings: `pip install sentence-transformers`.
- Re-index agents after choosing a provider (admin → agent → Train, or
  `index_agent_knowledge.delay(agent_id)`).

### 2. LiveKit
- Cloud: create a project, grab URL + API key/secret.
- Self-hosted later: run LiveKit + the SIP service on your server; set the same
  three env vars to point at it.
- Run once: `python ai_worker/scripts/livekit_sip_setup.py` (creates the inbound
  trunk + dispatch rule for agent `dialflow-ai`).

### 3. FreeSWITCH
- Add `scripts/dialplan_ai_bridge.xml` (adjust DID regex + `LIVEKIT_SIP_HOST`).
- Define the `livekit` gateway (template in the same file).
- In production, replace the hardcoded `X-Agent-Id` / `X-Tenant-Schema` with a
  Lua/HTTP lookup keyed on the dialed DID.

### 4. Worker
```bash
cd ai_worker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in LiveKit + backend + provider keys
python -m ai_worker.main dev      # or: start (production)
```
Run it under supervisor/systemd alongside Daphne, Celery, and
`fs_event_listener`.

## Call flow (precise)

```
PSTN/SIP → FreeSWITCH (AI DID) ──bridge(PCMU)──► LiveKit SIP trunk
  → dispatch rule: room "ai-call-<uuid>", dispatch agent "dialflow-ai",
    attributes: X-Agent-Id, X-Tenant-Schema, X-Caller-Number
  → worker main.entrypoint:
       _extract_call_meta → GET /api/ai/worker/config/?agent_id=..  (X-Tenant)
       quota check → build AgentSession(STT=saaras:v3 8k, LLM=per cfg, TTS=bulbul:v3 mulaw)
       on_enter → speak greeting
       loop: STT → on_user_turn_completed → POST /worker/retrieve/ (RAG)
             → LLM (tools: transfer_to_human, schedule_callback) → TTS
             barge-in handled by Sarvam STT + turn_detection="stt"
       transfer_to_human → transfer.perform_transfer → LiveKit SIP dials
            sip:queue-<id>@<fs-host> into the room (human joins)
            no human → offer callback (if allowed)
       schedule_callback → POST /worker/callback/
  → hangup / max duration → shutdown cb → POST /worker/result/
       (writes AICallSession + AITranscriptTurn, meters AI minutes)
```

## Telephony audio notes (from Sarvam + LiveKit docs)

- STT: Saaras v3 at **8000 Hz**, `flush_signal=True`; `turn_detection="stt"` +
  `min_endpointing_delay=0.07` on the session (Sarvam's documented best practice
  for snappy turns + barge-in). Do **not** pass a separate VAD to the session.
- TTS: Bulbul v3, `output_audio_codec="mulaw"`, `speech_sample_rate=8000` to
  match the PCMU bridge.
- FreeSWITCH bridge pinned to `PCMU` so sample rates line up end-to-end.

## Security

- Worker auth is a shared secret (`AI_WORKER_TOKEN`) — set a long random value,
  keep it out of the frontend, rotate if leaked.
- Lock the LiveKit inbound trunk `allowed_addresses` to your FreeSWITCH IP.
- The worker endpoints are server-to-server only; never expose the token to
  browser code.

## What's intentionally left to you

- DID → agent_id/tenant mapping logic in the dialplan (one Lua/HTTP lookup).
- Production embedding provider choice + a one-time re-index.
- Sentiment scoring / call summary generation can be added in the shutdown
  path (an extra LLM call) — the schema field `sentiment_score`/`summary`
  already exists; left optional to keep latency/cost predictable.
