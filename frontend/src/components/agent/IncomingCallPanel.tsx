import { useEffect, useState } from 'react'
import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { useAgentCommands } from '@/hooks/useAgentCommands'
import { formatPhone } from '@/lib/utils'
import { Phone, PhoneOff, User } from 'lucide-react'

export function IncomingCallPanel() {
  const { activeCall } = useAgentDesktopStore()
  const { answerCall, hangupCall } = useAgentCommands()
  const [ringPulse, setRingPulse] = useState(0)

  // Pulsing ring animation counter
  useEffect(() => {
    const interval = setInterval(() => {
      setRingPulse((p) => p + 1)
    }, 1500)
    return () => clearInterval(interval)
  }, [])

  if (!activeCall) return null

  const displayNumber = formatPhone(activeCall.caller_number)
  const displayName = activeCall.caller_name || activeCall.lead?.first_name
    ? `${activeCall.lead?.first_name || ''} ${activeCall.lead?.last_name || ''}`.trim() || activeCall.caller_name
    : 'Unknown Caller'

  return (
    <div className="flex-1 flex items-center justify-center bg-[#0A0E1A] relative overflow-hidden">
      {/* Background pulse rings */}
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
        >
          <div
            className="rounded-full border border-blue-500/10"
            style={{
              width: `${200 + i * 120}px`,
              height: `${200 + i * 120}px`,
              animation: `ping 3s cubic-bezier(0, 0, 0.2, 1) infinite`,
              animationDelay: `${i * 0.5}s`,
              opacity: 0.3 - i * 0.08,
            }}
          />
        </div>
      ))}

      <div className="relative z-10 flex flex-col items-center gap-8 max-w-md">
        {/* Caller avatar */}
        <div className="relative">
          <div className="w-28 h-28 rounded-full bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-2 border-blue-500/30 flex items-center justify-center animate-pulse">
            <User className="w-14 h-14 text-blue-400" />
          </div>
          {/* Ringing indicator */}
          <div className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full animate-bounce flex items-center justify-center">
            <Phone className="w-2.5 h-2.5 text-white" />
          </div>
        </div>

        {/* Caller info */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-1">{displayName}</h2>
          <p className="text-lg text-blue-400 font-mono">{displayNumber}</p>

          {activeCall.queue_name && (
            <p className="text-sm text-gray-500 mt-2">
              via <span className="text-gray-300">{activeCall.queue_name}</span>
            </p>
          )}
          {activeCall.campaign_name && (
            <p className="text-xs text-gray-600 mt-1">
              Campaign: {activeCall.campaign_name}
            </p>
          )}
        </div>

        {/* Ringing text */}
        <p className="text-sm text-gray-400 animate-pulse">
          Incoming call{'.'.repeat((ringPulse % 3) + 1)}
        </p>

        {/* Action buttons */}
        <div className="flex items-center gap-8">
          {/* Decline */}
          <button
            onClick={() => hangupCall(activeCall.call_id)}
            className="group flex flex-col items-center gap-2"
          >
            <div className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-500 active:bg-red-700 flex items-center justify-center transition-all group-active:scale-90 shadow-lg shadow-red-500/20">
              <PhoneOff className="w-7 h-7 text-white" />
            </div>
            <span className="text-xs text-gray-400 group-hover:text-red-400 transition-colors">
              Decline
            </span>
          </button>

          {/* Answer */}
          <button
            onClick={() => answerCall(activeCall.call_id)}
            className="group flex flex-col items-center gap-2"
          >
            <div className="w-20 h-20 rounded-full bg-green-600 hover:bg-green-500 active:bg-green-700 flex items-center justify-center transition-all group-active:scale-90 shadow-lg shadow-green-500/30 animate-[wiggle_1s_ease-in-out_infinite]">
              <Phone className="w-9 h-9 text-white" />
            </div>
            <span className="text-xs text-gray-400 group-hover:text-green-400 transition-colors">
              Answer
            </span>
          </button>
        </div>
      </div>

      <style>{`
        @keyframes wiggle {
          0%, 100% { transform: rotate(-3deg); }
          50% { transform: rotate(3deg); }
        }
      `}</style>
    </div>
  )
}
