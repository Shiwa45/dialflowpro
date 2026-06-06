import { useCallback } from 'react'
import { useAgentDesktopStore } from '@/store/agentDesktopStore'

/**
 * useAgentCommands — command senders for the agent desktop.
 *
 * Does NOT open a WebSocket. It sends through the single shared socket that
 * the top-level useAgentDesktop() registered into the store. Any number of
 * child components can use this safely without spawning extra connections.
 */
export function useAgentCommands() {
  const wsSend = useAgentDesktopStore((s) => s.wsSend)
  const setSelectedQueue = useAgentDesktopStore((s) => s.setSelectedQueue)

  const login = useCallback(() => wsSend({ action: 'login' }), [wsSend])
  const logout = useCallback(() => wsSend({ action: 'logout' }), [wsSend])

  const setStatus = useCallback(
    (s: 'available' | 'on_break') => wsSend({ action: 'set_status', status: s }),
    [wsSend],
  )

  const answerCall = useCallback(
    (callId: string) => wsSend({ action: 'answer_call', call_id: callId }),
    [wsSend],
  )

  const hangupCall = useCallback(
    (callId: string, disposition?: string) =>
      wsSend({ action: 'hangup_call', call_id: callId, disposition }),
    [wsSend],
  )

  const holdCall = useCallback(
    (callId: string) => wsSend({ action: 'hold_call', call_id: callId }),
    [wsSend],
  )

  const resumeCall = useCallback(
    (callId: string) => wsSend({ action: 'resume_call', call_id: callId }),
    [wsSend],
  )

  const transferCall = useCallback(
    (callId: string, target: string) =>
      wsSend({ action: 'transfer_call', call_id: callId, target }),
    [wsSend],
  )

  const sendDtmf = useCallback(
    (callId: string, digits: string) =>
      wsSend({ action: 'send_dtmf', call_id: callId, digits }),
    [wsSend],
  )

  const setDisposition = useCallback(
    (callId: string, disposition: string, notes?: string) =>
      wsSend({ action: 'set_disposition', call_id: callId, disposition, notes }),
    [wsSend],
  )

  const selectQueue = useCallback(
    (queueId: number) => {
      setSelectedQueue(queueId)
      wsSend({ action: 'select_queue', queue_id: queueId })
    },
    [wsSend, setSelectedQueue],
  )

  const makeCall = useCallback(
    (destination: string) => wsSend({ action: 'make_call', destination }),
    [wsSend],
  )

  return {
    login,
    logout,
    setStatus,
    answerCall,
    hangupCall,
    holdCall,
    resumeCall,
    transferCall,
    sendDtmf,
    setDisposition,
    selectQueue,
    makeCall,
  }
}
