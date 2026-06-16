import { useCallback, useEffect, useRef, useState } from 'react'
import api from '@/api/client'
import { useWebSocket } from './useWebSocket'

export interface TrackedAgent {
  id: number
  name: string
  extension: string
  status: number          // 0 logged out, 1 available, 2 break, 3 on demand
  status_display: string
  state: string
  state_display: string
  registered: boolean
  on_call: boolean
  calls_answered: number
  talk_time: number
  monitoredMode?: string | null   // listen | whisper | barge | takeover | null
}

export interface CallFeedItem {
  event: string
  agent_id: number | null
  agent_name: string
  caller: string
  callee: string
  uuid: string
  duration: number
  timestamp: string
}

const STATUS = { LOGGED_OUT: 0, AVAILABLE: 1, ON_BREAK: 2, ON_DEMAND: 3 }

export function useAgentTracking() {
  const [agents, setAgents] = useState<TrackedAgent[]>([])
  const [feed, setFeed] = useState<CallFeedItem[]>([])
  const [loading, setLoading] = useState(true)
  const agentsRef = useRef<TrackedAgent[]>([])
  agentsRef.current = agents

  // Initial snapshot
  useEffect(() => {
    let active = true
    api.get('/callcenter/monitor/live_agents/')
      .then(({ data }) => { if (active) setAgents(data) })
      .catch((e) => console.error('live_agents failed', e))
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const upsert = useCallback((id: number, patch: Partial<TrackedAgent>) => {
    setAgents(prev => {
      const idx = prev.findIndex(a => a.id === id)
      if (idx < 0) return prev
      const next = [...prev]
      next[idx] = { ...next[idx], ...patch }
      return next
    })
  }, [])

  useWebSocket('/ws/callcenter/dashboard/', {
    onMessage: (data: any) => {
      switch (data.type) {
        case 'agent_status':
          upsert(data.agent_id, {
            status: data.status,
            status_display: data.status_display,
            state: data.state,
            state_display: data.state_display,
            on_call: data.state === 'In a queue call',
            registered: data.status !== STATUS.LOGGED_OUT,
            calls_answered: data.calls_answered,
            talk_time: data.talk_time,
          })
          break
        case 'agent_presence':
          upsert(data.agent_id, {
            registered: data.registered,
            status: data.registered ? STATUS.AVAILABLE : STATUS.LOGGED_OUT,
          })
          break
        case 'call_event':
          if (data.agent_id) {
            upsert(data.agent_id, {
              on_call: data.event === 'answered',
              state: data.event === 'answered' ? 'In a queue call'
                   : data.event === 'ringing' ? 'Receiving' : 'Waiting',
            })
          }
          setFeed(prev => [data as CallFeedItem, ...prev.slice(0, 24)])
          break
        case 'monitor_event':
          upsert(data.agent_id, {
            monitoredMode: data.active ? data.mode : null,
          })
          break
      }
    },
  })

  // Actions
  const act = async (agentId: number, verb: string, body?: any) => {
    const { data } = await api.post(`/callcenter/monitor/${agentId}/${verb}/`, body || {})
    return data
  }

  return {
    agents,
    feed,
    loading,
    listen: (id: number) => act(id, 'listen'),
    whisper: (id: number) => act(id, 'whisper'),
    barge: (id: number) => act(id, 'barge'),
    takeover: (id: number) => act(id, 'takeover'),
    stopMonitor: (id: number, supervisorUuid?: string) =>
      act(id, 'stop', { supervisor_uuid: supervisorUuid }),
  }
}
