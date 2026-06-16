import { useEffect, useCallback, useRef } from 'react'
import { useWebSocket } from './useWebSocket'
import { useAgentCommands } from './useAgentCommands'
import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { AgentDesktopEvent } from '@/types'
import api from '@/api/client'

/**
 * useAgentDesktop — single hook for the entire agent panel.
 *
 * Connects to ws://host/ws/callcenter/agent-desktop/
 * Routes every WS event through the Zustand store.
 * Exposes command functions that send JSON over the WS.
 */
export function useAgentDesktop() {
  const store = useAgentDesktopStore()
  const initialLoaded = useRef(false)

  // ── 1. Fetch initial profile via REST ──
  useEffect(() => {
    if (initialLoaded.current) return
    initialLoaded.current = true

    api
      .get('/callcenter/agents/me/')
      .then(({ data }) => {
        store.setAgent({
          id: data.id,
          name: data.name,
          status: data.status,
          status_display: data.status_display,
          state: data.state,
          sip_extension: data.sip_extension,
          calls_answered: data.calls_answered,
          talk_time: data.talk_time,
          wrap_up_time: data.wrap_up_time,
          max_no_answer: data.max_no_answer,
          last_bridge_start: data.last_bridge_start,
          last_bridge_end: data.last_bridge_end,
        })
        store.setQueues(data.queues || [])
        store.setTodayStats(data.today || { calls: 0, duration: 0, avg_duration: 0 })
        if (data.queues?.length && !store.selectedQueueId) {
          store.setSelectedQueue(data.queues[0].id)
        }
      })
      .catch((err) => {
        console.error('[AgentDesktop] Failed to fetch profile:', err)
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── 2. WebSocket connection ──
  const handleMessage = useCallback(
    (data: AgentDesktopEvent) => {
      store.handleWsEvent(data)
    },
    [] // eslint-disable-line react-hooks/exhaustive-deps
  )

  const { status: wsStatus, isConnected, send } = useWebSocket(
    '/ws/callcenter/agent-desktop/',
    {
      onMessage: handleMessage,
      reconnect: true,
      maxRetries: 50,
      heartbeatInterval: 15000,
    },
  )

  // Sync WS status into the store so any component can read it directly
  useEffect(() => {
    store.setWsStatus(wsStatus)
  }, [wsStatus]) // eslint-disable-line react-hooks/exhaustive-deps

  // Register the single shared socket sender so child components (via
  // useAgentCommands) send through this one connection — no extra sockets.
  useEffect(() => {
    store.setWsSend(send)
  }, [send]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── 3. Call duration timer ──
  useEffect(() => {
    const interval = setInterval(() => {
      const call = useAgentDesktopStore.getState().activeCall
      if (call?.state === 'active') {
        useAgentDesktopStore.getState().incrementCallDuration()
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // ── 4. Wrap-up countdown timer ──
  useEffect(() => {
    const interval = setInterval(() => {
      const wt = useAgentDesktopStore.getState().wrapUpTime
      if (wt > 0) {
        useAgentDesktopStore.getState().decrementWrapUp()
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // ── 5. Auto-clear notifications ──
  useEffect(() => {
    if (!store.notification) return
    const t = setTimeout(() => store.clearNotification(), 4000)
    return () => clearTimeout(t)
  }, [store.notification]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── 6. Command senders (shared — send through the one socket) ──
  const commands = useAgentCommands()

  return {
    // State
    ...store,
    wsStatus,
    isConnected,

    // Commands
    ...commands,
  }
}
