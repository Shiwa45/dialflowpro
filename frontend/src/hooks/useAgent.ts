import { useState, useEffect } from 'react'
import { Agent, AgentStatus } from '@/types'
import api from '@/api/client'
import { useWebSocket } from './useWebSocket'

export function useAgent() {
  const [agent, setAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)

  // Fetch current agent data
  useEffect(() => {
    const fetchAgent = async () => {
      try {
        const { data } = await api.get('/callcenter/agents/me/')
        setAgent(data)
      } catch (error) {
        console.error('Failed to fetch agent:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchAgent()
  }, [])

  // WebSocket updates
  useWebSocket('/ws/callcenter/agents/', {
    onMessage: (data) => {
      if (data.type === 'agent_status' && data.agent_id === agent?.id) {
        setAgent(prev => prev ? { ...prev, status: data.status, state: data.state } : null)
      }
    },
  })

  const setAvailable = async () => {
    try {
      const { data } = await api.post(`/callcenter/agents/${agent?.id}/set_available/`)
      setAgent(data)
    } catch (error) {
      console.error('Failed to set available:', error)
    }
  }

  const setOnBreak = async () => {
    try {
      const { data } = await api.post(`/callcenter/agents/${agent?.id}/set_on_break/`)
      setAgent(data)
    } catch (error) {
      console.error('Failed to set on break:', error)
    }
  }

  const setLoggedOut = async () => {
    try {
      const { data } = await api.post(`/callcenter/agents/${agent?.id}/set_logged_out/`)
      setAgent(data)
    } catch (error) {
      console.error('Failed to set logged out:', error)
    }
  }

  return {
    agent,
    loading,
    setAvailable,
    setOnBreak,
    setLoggedOut,
    isAvailable: agent?.status === AgentStatus.AVAILABLE,
  }
}
