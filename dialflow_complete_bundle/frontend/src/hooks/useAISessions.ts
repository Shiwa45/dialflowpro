import { useCallback, useEffect, useState } from 'react'
import api from '@/api/client'

export interface AISessionListItem {
  id: number
  agent: number
  agent_name: string
  caller_number: string
  started_at: string | null
  duration_seconds: number
  outcome: string
  outcome_display: string
  detected_language: string
  sentiment_score: number | null
}

export interface AITranscriptTurn {
  id: number
  role: 'caller' | 'ai' | 'system'
  text: string
  language: string
  confidence: number | null
  started_at: string | null
}

export interface AISessionDetail extends AISessionListItem {
  ended_at: string | null
  livekit_room?: string
  call_uuid?: string
  transfer_reason: string
  summary: string
  turns: AITranscriptTurn[]
}

export interface AICallback {
  id: number
  agent: number
  caller_number: string
  requested_for: string
  notes: string
  status: 'pending' | 'done' | 'cancelled'
  assigned_agent: number | null
  created_date: string
}

export function useAISessions(agentId?: number) {
  const [sessions, setSessions] = useState<AISessionListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const q = agentId ? `?agent=${agentId}` : ''
      const { data } = await api.get(`/ai/sessions/${q}`)
      setSessions(data.results ?? data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load call sessions')
    } finally {
      setLoading(false)
    }
  }, [agentId])

  useEffect(() => { refresh() }, [refresh])

  return { sessions, loading, error, refresh }
}

export function useAISessionDetail(id?: number) {
  const [session, setSession] = useState<AISessionDetail | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.get(`/ai/sessions/${id}/`)
      .then(({ data }) => setSession(data))
      .catch(() => setSession(null))
      .finally(() => setLoading(false))
  }, [id])

  return { session, loading }
}

export function useAICallbacks() {
  const [callbacks, setCallbacks] = useState<AICallback[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/ai/callbacks/')
      setCallbacks(data.results ?? data)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const setStatus = (id: number, status: AICallback['status']) =>
    api.patch(`/ai/callbacks/${id}/`, { status }).then(refresh)

  return { callbacks, loading, refresh, setStatus }
}
