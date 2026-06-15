import { create } from 'zustand'
import {
  Agent,
  AgentStatus,
  ActiveCall,
  CallState,
  QueueInfo,
  LeadInfo,
  CampaignInfo,
  AgentDesktopEvent,
} from '@/types'
type WsStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected'

interface AgentDesktopState {
  // ── Agent ──
  agent: Agent | null
  queues: QueueInfo[]
  todayStats: { calls: number; duration: number; avg_duration: number }

  // ── Active call ──
  activeCall: ActiveCall | null
  callDuration: number // seconds, updated by timer

  // ── UI state ──
  selectedQueueId: number | null
  wrapUpTime: number // seconds left in wrap-up
  isDialpadOpen: boolean
  dialInput: string
  volume: number
  isMuted: boolean

  // ── Disposition ──
  dispositions: string[]

  // ── Peer agents (for awareness) ──
  peerAgents: Map<number, { name: string; status: number; status_display: string }>

  // ── WebSocket status ──
  wsStatus: WsStatus

  // WS sender — registered by the single top-level useAgentDesktop instance.
  // Child components send commands through this shared socket.
  wsSend: (data: any) => boolean

  // ── Errors / notifications ──
  notification: { type: 'success' | 'error' | 'info'; message: string } | null

  // ── Actions ──
  setWsStatus: (s: WsStatus) => void
  setWsSend: (fn: (data: any) => boolean) => void
  setAgent: (agent: Agent) => void
  setQueues: (queues: QueueInfo[]) => void
  setTodayStats: (stats: { calls: number; duration: number; avg_duration: number }) => void
  handleWsEvent: (event: AgentDesktopEvent) => void

  // Call actions
  setActiveCall: (call: ActiveCall | null) => void
  updateCallState: (state: CallState) => void
  setCallDuration: (d: number) => void
  incrementCallDuration: () => void

  // UI actions
  setSelectedQueue: (id: number | null) => void
  setWrapUpTime: (t: number) => void
  decrementWrapUp: () => void
  toggleDialpad: () => void
  setDialInput: (v: string) => void
  appendDialDigit: (d: string) => void
  clearDialInput: () => void
  setVolume: (v: number) => void
  toggleMute: () => void
  setNotification: (n: { type: 'success' | 'error' | 'info'; message: string } | null) => void
  clearNotification: () => void
}

export const useAgentDesktopStore = create<AgentDesktopState>((set, get) => ({
  // ── Initial state ──
  agent: null,
  queues: [],
  todayStats: { calls: 0, duration: 0, avg_duration: 0 },

  activeCall: null,
  callDuration: 0,

  selectedQueueId: null,
  wrapUpTime: 0,
  isDialpadOpen: false,
  dialInput: '',
  volume: 75,
  isMuted: false,

  dispositions: [
    'Sale',
    'No Answer',
    'Busy',
    'Voicemail',
    'Callback',
    'Not Interested',
    'Do Not Call',
    'Wrong Number',
    'Other',
  ],

  peerAgents: new Map(),

  wsStatus: 'disconnected',
  wsSend: () => false,
  notification: null,

  // ── Setters ──
  setWsStatus: (s) => set({ wsStatus: s }),
  setWsSend: (fn) => set({ wsSend: fn }),
  setAgent: (agent) => set({ agent }),
  setQueues: (queues) => set({ queues }),
  setTodayStats: (stats) => set({ todayStats: stats }),

  // ── Master event handler ──
  handleWsEvent: (event) => {
    const state = get()

    switch (event.type) {
      case 'agent_state': {
        set({
          agent: event.agent,
          queues: event.queues ?? state.queues,
        })
        // Auto-select first queue if none selected
        if (!state.selectedQueueId && event.queues?.length) {
          set({ selectedQueueId: event.queues[0].id })
        }
        break
      }

      case 'incoming_call': {
        const call: ActiveCall = {
          call_id: event.call_id,
          caller_number: event.caller_number,
          caller_name: event.caller_name || '',
          queue_name: event.queue_name || '',
          campaign_name: event.campaign_name || '',
          state: 'ringing',
          started_at: Date.now(),
          lead: event.lead || {},
        }
        set({
          activeCall: call,
          callDuration: 0,
          notification: {
            type: 'info',
            message: `Incoming call from ${event.caller_number}`,
          },
        })
        // Play ringtone (browser API)
        try {
          navigator.vibrate?.([200, 100, 200])
        } catch { /* noop */ }
        break
      }

      case 'call_answered': {
        if (state.activeCall) {
          set({
            activeCall: {
              ...state.activeCall,
              state: 'active',
              started_at: Date.now(),
            },
            callDuration: 0,
            notification: null,
          })
        }
        if (state.agent) {
          set({
            agent: { ...state.agent, state: 'In a queue call' as any },
          })
        }
        break
      }

      case 'call_ended': {
        const prevCall = state.activeCall

        // Always go to mandatory wrap-up. The call does NOT auto-clear — the
        // agent must submit a disposition (which makes them available again).
        set({
          activeCall: prevCall
            ? { ...prevCall, state: 'wrap_up' }
            : null,
          wrapUpTime: state.agent?.wrap_up_time ?? 0,
          notification: {
            type: 'info',
            message: `Call ended${event.hangup_cause ? ` (${event.hangup_cause})` : ''} — please complete wrap-up`,
          },
        })

        // Agent is in after-call work (Idle), NOT available, until disposed.
        if (state.agent) {
          set({
            agent: { ...state.agent, state: 'Idle' as any },
            todayStats: {
              ...state.todayStats,
              calls: state.todayStats.calls + 1,
              duration: state.todayStats.duration + (event.duration || 0),
            },
          })
        }
        break
      }

      case 'call_held': {
        if (state.activeCall) {
          set({
            activeCall: {
              ...state.activeCall,
              state: 'held',
              held_at: Date.now(),
            },
          })
        }
        break
      }

      case 'call_resumed': {
        if (state.activeCall) {
          set({
            activeCall: {
              ...state.activeCall,
              state: 'active',
              held_at: undefined,
            },
          })
        }
        break
      }

      case 'campaign_lead': {
        if (state.activeCall) {
          set({
            activeCall: {
              ...state.activeCall,
              lead: event.lead,
              campaign_name:
                event.campaign?.name || state.activeCall.campaign_name,
            },
          })
        }
        break
      }

      case 'queue_stats': {
        const updatedQueues = state.queues.map((q) =>
          q.id === event.queue_id
            ? {
                ...q,
                waiting_calls: event.waiting_calls,
                active_agents: event.active_agents,
              }
            : q
        )
        set({ queues: updatedQueues })
        break
      }

      case 'peer_status': {
        const peers = new Map(state.peerAgents)
        peers.set(event.agent_id, {
          name: event.agent_name,
          status: event.status,
          status_display: event.status_display,
        })
        set({ peerAgents: peers })
        break
      }

      case 'disposition_saved': {
        set({
          notification: {
            type: 'success',
            message: `Disposition saved: ${event.disposition}`,
          },
        })
        // Clear activeCall after saving disposition
        setTimeout(() => set({ activeCall: null, wrapUpTime: 0 }), 1500)
        break
      }

      case 'transfer_result': {
        set({
          notification: {
            type: event.status === 'transferred' ? 'success' : 'error',
            message:
              event.status === 'transferred'
                ? `Call transferred to ${event.target}`
                : `Transfer failed`,
          },
        })
        if (event.status === 'transferred') {
          set({ activeCall: null })
        }
        break
      }

      case 'error': {
        set({
          notification: {
            type: 'error',
            message: event.message || 'An error occurred',
          },
        })
        break
      }
    }
  },

  // ── Call actions ──
  setActiveCall: (call) => set({ activeCall: call }),
  updateCallState: (state) => {
    const call = get().activeCall
    if (call) set({ activeCall: { ...call, state } })
  },
  setCallDuration: (d) => set({ callDuration: d }),
  incrementCallDuration: () => set((s) => ({ callDuration: s.callDuration + 1 })),

  // ── UI actions ──
  setSelectedQueue: (id) => set({ selectedQueueId: id }),
  setWrapUpTime: (t) => set({ wrapUpTime: t }),
  decrementWrapUp: () => {
    const t = get().wrapUpTime
    if (t > 0) set({ wrapUpTime: t - 1 })
    // Do NOT auto-clear when the countdown ends — disposition is mandatory.
    // The call clears only after the agent submits a disposition.
  },
  toggleDialpad: () => set((s) => ({ isDialpadOpen: !s.isDialpadOpen })),
  setDialInput: (v) => set({ dialInput: v }),
  appendDialDigit: (d) => set((s) => ({ dialInput: s.dialInput + d })),
  clearDialInput: () => set({ dialInput: '' }),
  setVolume: (v) => set({ volume: v }),
  toggleMute: () => set((s) => ({ isMuted: !s.isMuted })),
  setNotification: (n) => set({ notification: n }),
  clearNotification: () => set({ notification: null }),
}))
