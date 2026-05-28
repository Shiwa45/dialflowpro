import { useEffect, useRef, useState } from 'react'

interface UseWebSocketOptions {
  onMessage?: (data: any) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const tenant = localStorage.getItem('tenant_schema')
    const token = localStorage.getItem('access_token')

    if (!tenant || tenant === 'null' || tenant === 'undefined' || !token || token === 'null' || token === 'undefined') {
      console.error('Missing tenant or token for WebSocket connection')
      return
    }

    const wsUrl = `ws://localhost:8000${url}?token=${token}&tenant=${tenant}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
      options.onOpen?.()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        options.onMessage?.(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      options.onClose?.()
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      options.onError?.(error)
    }

    wsRef.current = ws

    return () => {
      ws.close()
    }
  }, [url])

  const send = (data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }

  return { isConnected, send }
}
