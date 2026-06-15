import { useCallback, useEffect, useState } from 'react'
import api from '@/api/client'
import { AIAgent, AISubscription, AIKnowledgeItem } from '@/types/aiAgent'

export function useAISubscription() {
  const [sub, setSub] = useState<AISubscription | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    api.get('/ai/subscription/')
      .then(({ data }) => setSub(Array.isArray(data) ? data[0] : data))
      .catch(() => setSub({ is_active: false }))
      .finally(() => setLoading(false))
  }, [])
  return { sub, loading }
}

export function useAIAgents() {
  const [agents, setAgents] = useState<AIAgent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/ai/agents/')
      setAgents(data.results ?? data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load AI agents')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const create = (payload: Partial<AIAgent>) =>
    api.post('/ai/agents/', payload).then(r => r.data)
  const update = (id: number, payload: Partial<AIAgent>) =>
    api.patch(`/ai/agents/${id}/`, payload).then(r => r.data)
  const remove = (id: number) => api.delete(`/ai/agents/${id}/`)
  const activate = (id: number) => api.post(`/ai/agents/${id}/activate/`).then(r => r.data)
  const pause = (id: number) => api.post(`/ai/agents/${id}/pause/`).then(r => r.data)
  const train = (id: number) => api.post(`/ai/agents/${id}/train/`).then(r => r.data)
  const previewPrompt = (id: number) =>
    api.get(`/ai/agents/${id}/preview_prompt/`).then(r => r.data.system_prompt as string)

  return { agents, loading, error, refresh, create, update, remove, activate, pause, train, previewPrompt }
}

export function useKnowledge(agentId?: number) {
  const [items, setItems] = useState<AIKnowledgeItem[]>([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!agentId) return
    setLoading(true)
    try {
      const { data } = await api.get(`/ai/knowledge/?agent=${agentId}`)
      setItems(data.results ?? data)
    } finally { setLoading(false) }
  }, [agentId])

  useEffect(() => { refresh() }, [refresh])

  const add = (payload: Partial<AIKnowledgeItem>) =>
    api.post('/ai/knowledge/', { ...payload, agent: agentId }).then(r => r.data)
  const update = (id: number, payload: Partial<AIKnowledgeItem>) =>
    api.patch(`/ai/knowledge/${id}/`, payload).then(r => r.data)
  const remove = (id: number) => api.delete(`/ai/knowledge/${id}/`)

  return { items, loading, refresh, add, update, remove }
}
