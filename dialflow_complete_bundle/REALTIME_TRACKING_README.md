# DialFlow Pro — Real-Time Agent Tracking & Live Call Monitoring

This patch adds end-to-end, DB-backed real-time agent tracking plus supervisor
listen / whisper / barge / takeover — the feature set commercial dialers ship.

## The gap it closes

Your consumers (`AgentStatusConsumer`, `LiveDashboardConsumer`, …) only ever
*received* group events. **Nothing in the codebase ever called `group_send`,**
and there was no FreeSWITCH event source feeding agent state. This patch adds:

- the broadcast layer (`realtime.py`) that every other piece calls,
- the **event source** — an ESL listener daemon translating FreeSWITCH events
  into agent state + WebSocket pushes,
- `post_save` signals so REST status changes also broadcast,
- supervisor monitoring over ESL (`monitoring.py` + `monitor_views.py`),
- a new admin **Agent Tracking** panel and `useAgentTracking` hook.

## Files

### Backend — replace
| Path | Change |
|------|--------|
| `apps/callcenter/consumers.py` | adds presence / call_event / monitor handlers + `AgentMonitorConsumer` |
| `apps/callcenter/apps.py` | registers signals in `ready()` |
| `apps/callcenter/routing.py` | adds `ws/callcenter/monitor/<id>/` |
| `apps/callcenter/urls.py` | registers `MonitorViewSet` |

### Backend — new
| Path | Purpose |
|------|---------|
| `apps/callcenter/realtime.py` | central `group_send` broadcast helpers |
| `apps/callcenter/signals.py` | `post_save` Agent → broadcast |
| `apps/callcenter/monitoring.py` | ESL eavesdrop / intercept helpers |
| `apps/callcenter/monitor_views.py` | `MonitorViewSet`: live_agents + listen/whisper/barge/takeover/stop |
| `apps/callcenter/management/commands/fs_event_listener.py` | the ESL event daemon |
| `scripts/freeswitch_realtime.conf.xml` | FS config snippet |

### Frontend — new
| Path | Purpose |
|------|---------|
| `src/hooks/useAgentTracking.ts` | snapshot + single dashboard socket |
| `src/pages/admin/LiveAgentTracking.tsx` | the tracking panel |

## Install

1. Copy the files into your tree (paths mirror the project).
2. No new Python deps — `greenswitch`, `channels`, `channels-redis` are already
   in `requirements.txt`.
3. Wire the route in your admin router (e.g. `App.tsx`):
   ```tsx
   import { LiveAgentTracking } from '@/pages/admin/LiveAgentTracking'
   // <Route path="agent-tracking" element={<LiveAgentTracking />} />
   ```
   and add a sidebar link to `/agent-tracking`.
4. FreeSWITCH: apply `scripts/freeswitch_realtime.conf.xml` (registration events
   + event socket), then `reloadxml` and `sofia profile internal restart`.

## Run the event listener (the new always-on process)

```bash
python manage.py fs_event_listener --node fs1
```

Run it under the same supervisor/systemd as Daphne + Celery. It reconnects with
backoff on FS restart. **Without this process, presence and live state won't
update** — it is the event source.

## How status maps

| Real-world event | FreeSWITCH event | Agent row | Broadcast |
|---|---|---|---|
| Softphone registers | `sofia::register` | status→Available, state→Waiting | presence + status |
| Inbound ringing | `CHANNEL_CREATE` | state→Receiving | call_event ringing |
| Call connected | `CHANNEL_ANSWER`/`BRIDGE` | state→In a queue call, bridge_start | call_event answered |
| Call ends | `CHANNEL_HANGUP` | state→Waiting, talk_time += billsec | call_event hangup |
| Break button (REST) | — | status→On Break | post_save signal |
| Unregister/expire | `sofia::unregister` | status→Logged Out | presence |

## Supervisor controls (REST)

All under `/api/callcenter/monitor/`:

- `GET  /live_agents/` — snapshot for initial render
- `POST /<id>/listen/` — silent monitor (eavesdrop)
- `POST /<id>/whisper/` — coach the agent only
- `POST /<id>/barge/` — 3-way conference
- `POST /<id>/takeover/` — `intercept` the customer leg, drop the agent
- `POST /<id>/stop/` — end the supervisor's monitor leg

The supervisor must have a SIP extension on their `agent_profile` (their
softphone rings, then bridges into the target call).

## Multi-tenant note

The listener scans tenant schemas to map a SIP extension → Agent
(`_find_agent_by_extension`). For multiple tenants with overlapping extension
ranges, prefix extensions per tenant or scope FS profiles per tenant so the
match is unambiguous.

## Verify

1. Start Daphne, Celery, Redis, and `fs_event_listener`.
2. Register an agent softphone → the agent appears **Ready** within ~1s.
3. Place a call → card flips to **Ringing** → **On Call** with a live feed entry.
4. As a supervisor (with an extension), hit **Listen** → your phone rings and
   bridges into the call muted; **Take** replaces the agent.
