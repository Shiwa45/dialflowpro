import { useEffect } from 'react'
import { useAgentDesktop } from '@/hooks/useAgentDesktop'
import { Softphone } from '@/components/agent/Softphone'
import { IncomingCallPanel } from '@/components/agent/IncomingCallPanel'
import { ActiveCallPanel } from '@/components/agent/ActiveCallPanel'
import { CustomerInfoPanel } from '@/components/agent/CustomerInfoPanel'
import { MetricsBar } from '@/components/agent/MetricsBar'
import { BottomBar } from '@/components/agent/BottomBar'
import { WrapUpPanel } from '@/components/agent/WrapUpPanel'
import { AgentStatus } from '@/types'
import {
  Phone,
  Wifi,
  WifiOff,
  Loader2,
  LogIn,
} from 'lucide-react'

export function AgentPanel() {
  const {
    agent,
    activeCall,
    wsStatus,
    isConnected,
    todayStats,
    queues,
    notification,
    login,
  } = useAgentDesktop()

  // Prevent accidental page close during active call
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (activeCall && activeCall.state !== 'idle') {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [activeCall])

  // ── Loading state ──
  if (!agent) {
    return (
      <div className="h-screen bg-[#0A0E1A] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <span className="text-gray-400 text-sm">Connecting to agent desktop…</span>
        </div>
      </div>
    )
  }

  // ── Logged out state ──
  if (agent.status === AgentStatus.LOGGED_OUT) {
    return (
      <div className="h-screen bg-[#0A0E1A] flex items-center justify-center">
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Phone className="w-8 h-8 text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Agent Desktop</h1>
          <p className="text-gray-400 text-sm mb-2">{agent.name}</p>
          <p className="text-gray-500 text-xs mb-8">
            Extension {agent.sip_extension || '—'}
          </p>

          <button
            onClick={login}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-6 rounded-xl transition-colors"
          >
            <LogIn className="w-5 h-5" />
            Go Available
          </button>

          <div className="mt-6 flex items-center justify-center gap-2 text-xs">
            {isConnected ? (
              <>
                <Wifi className="w-3 h-3 text-green-500" />
                <span className="text-green-500">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3 text-red-500" />
                <span className="text-red-400">{wsStatus}</span>
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ── Determine main content panel ──
  const renderMainContent = () => {
    if (!activeCall || activeCall.state === 'idle') {
      return (
        <div className="flex-1 flex items-center justify-center bg-[#0A0E1A]">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center">
              <Phone className="w-10 h-10 text-gray-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-400 mb-2">Ready for calls</h2>
            <p className="text-sm text-gray-600">
              {queues.length > 0
                ? `Listening on ${queues.length} queue${queues.length > 1 ? 's' : ''}`
                : 'No queues assigned'}
            </p>
          </div>
        </div>
      )
    }

    if (activeCall.state === 'ringing') {
      return <IncomingCallPanel />
    }

    if (activeCall.state === 'wrap_up') {
      return <WrapUpPanel />
    }

    // active, held, transferring
    return <ActiveCallPanel />
  }

  return (
    <div className="h-screen bg-[#0A0E1A] flex flex-col overflow-hidden select-none">
      {/* ── Notification toast ── */}
      {notification && (
        <div
          className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 px-5 py-2.5 rounded-xl text-sm font-medium shadow-xl transition-all animate-[slideDown_0.3s_ease] ${
            notification.type === 'error'
              ? 'bg-red-500/90 text-white'
              : notification.type === 'success'
                ? 'bg-green-500/90 text-white'
                : 'bg-blue-500/90 text-white'
          }`}
        >
          {notification.message}
        </div>
      )}

      {/* ── Metrics bar (top) ── */}
      <MetricsBar />

      {/* ── Main 3-column layout ── */}
      <div className="flex-1 flex min-h-0">
        {/* Left — Softphone */}
        <div className="w-80 flex-shrink-0">
          <Softphone />
        </div>

        {/* Center — Call content */}
        {renderMainContent()}

        {/* Right — Customer Info (only during active/held/wrap-up call) */}
        {activeCall && activeCall.state !== 'idle' && activeCall.state !== 'ringing' && (
          <div className="w-96 flex-shrink-0">
            <CustomerInfoPanel />
          </div>
        )}
      </div>

      {/* ── Bottom bar ── */}
      <BottomBar />
    </div>
  )
}
