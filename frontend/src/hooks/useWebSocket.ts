import { useEffect, useRef, useState, useCallback } from 'react'

export type WsStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected'

interface UseWebSocketOptions {
  onMessage?: (data: any) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  /** Auto-reconnect on drop (default true) */
  reconnect?: boolean
  /** Max reconnect attempts (default 20) */
  maxRetries?: number
  /** Heartbeat interval in ms (default 25000) */
  heartbeatInterval?: number
  /** Whether to connect immediately (default true) */
  enabled?: boolean
}

const BASE_DELAY = 1000
const MAX_DELAY = 30000

export function useWebSocket(path: string, options: UseWebSocketOptions = {}) {
  const {
    reconnect = true,
    maxRetries = 20,
    heartbeatInterval = 25000,
    enabled = true,
  } = options

  const [status, setStatus] = useState<WsStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const retryCount = useRef(0)
  const retryTimer = useRef<ReturnType<typeof setTimeout>>()
  const heartbeatTimer = useRef<ReturnType<typeof setInterval>>()
  const unmounted = useRef(false)

  // Keep callbacks in refs so reconnects don't stale-close
  const onMessageRef = useRef(options.onMessage)
  const onOpenRef = useRef(options.onOpen)
  const onCloseRef = useRef(options.onClose)
  const onErrorRef = useRef(options.onError)

  useEffect(() => { onMessageRef.current = options.onMessage }, [options.onMessage])
  useEffect(() => { onOpenRef.current = options.onOpen }, [options.onOpen])
  useEffect(() => { onCloseRef.current = options.onClose }, [options.onClose])
  useEffect(() => { onErrorRef.current = options.onError }, [options.onError])

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current)
      heartbeatTimer.current = undefined
    }
  }, [])

  const startHeartbeat = useCallback(() => {
    stopHeartbeat()
    heartbeatTimer.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'heartbeat' }))
      }
    }, heartbeatInterval)
  }, [heartbeatInterval, stopHeartbeat])

  const connect = useCallback(() => {
    if (unmounted.current) return
    // Don't open a second socket while one is already connecting or open
    const rs = wsRef.current?.readyState
    if (rs === WebSocket.OPEN || rs === WebSocket.CONNECTING) return

    const tenant = localStorage.getItem('tenant_schema')
    const token = localStorage.getItem('access_token')

    if (!token || token === 'null' || token === 'undefined') {
      console.warn('[WS] No auth token — skipping connection')
      return
    }

    // Build URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_WS_HOST || window.location.host
    const params = new URLSearchParams()
    params.set('token', token)
    if (tenant && tenant !== 'null') params.set('tenant', tenant)

    const url = `${protocol}//${host}${path}?${params.toString()}`

    setStatus(retryCount.current > 0 ? 'reconnecting' : 'connecting')

    const ws = new WebSocket(url)

    ws.onopen = () => {
      if (unmounted.current) { ws.close(); return }
      retryCount.current = 0
      setStatus('connected')
      // Send an immediate heartbeat so the server marks presence fresh at once
      try { ws.send(JSON.stringify({ action: 'heartbeat' })) } catch { /* noop */ }
      startHeartbeat()
      onOpenRef.current?.()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        // Suppress pong heartbeats from bubbling up
        if (data.type === 'pong') return
        onMessageRef.current?.(data)
      } catch (err) {
        console.error('[WS] Failed to parse message:', err)
      }
    }

    ws.onclose = (event) => {
      stopHeartbeat()
      setStatus('disconnected')
      onCloseRef.current?.()

      if (unmounted.current) return

      // Don't reconnect if server explicitly rejected (4xxx)
      if (event.code >= 4000) {
        console.warn(`[WS] Server rejected connection (${event.code}). Not reconnecting.`)
        return
      }

      // Auto-reconnect with exponential backoff
      if (reconnect && retryCount.current < maxRetries) {
        const delay = Math.min(
          BASE_DELAY * Math.pow(2, retryCount.current) + Math.random() * 500,
          MAX_DELAY,
        )
        retryCount.current += 1
        console.log(`[WS] Reconnecting in ${Math.round(delay)}ms (attempt ${retryCount.current}/${maxRetries})`)
        retryTimer.current = setTimeout(connect, delay)
      }
    }

    ws.onerror = (error) => {
      console.error('[WS] Error:', error)
      onErrorRef.current?.(error)
    }

    wsRef.current = ws
  }, [path, reconnect, maxRetries, startHeartbeat, stopHeartbeat])

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    unmounted.current = false
    if (enabled) connect()

    return () => {
      unmounted.current = true
      clearTimeout(retryTimer.current)
      stopHeartbeat()
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect on intentional close
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [path, enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
      return true
    }
    console.warn('[WS] Cannot send — socket not open')
    return false
  }, [])

  const disconnect = useCallback(() => {
    clearTimeout(retryTimer.current)
    stopHeartbeat()
    retryCount.current = maxRetries // prevent auto-reconnect
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('disconnected')
  }, [maxRetries, stopHeartbeat])

  return {
    status,
    isConnected: status === 'connected',
    send,
    disconnect,
    reconnect: connect,
  }
}
