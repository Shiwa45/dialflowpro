import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { formatDuration } from '@/lib/utils'
import {
  Phone,
  Clock,
  PhoneIncoming,
  Timer,
  TrendingUp,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'

export function MetricsBar() {
  const { agent, queues, todayStats, wsStatus } = useAgentDesktopStore()

  const totalWaiting = queues.reduce((sum, q) => sum + (q.waiting_calls || 0), 0)

  const metrics = [
    {
      icon: PhoneIncoming,
      label: 'In Queue',
      value: String(totalWaiting),
      color: totalWaiting > 0 ? 'text-orange-400' : 'text-gray-400',
      pulse: totalWaiting > 3,
    },
    {
      icon: Phone,
      label: 'Answered Today',
      value: String(todayStats.calls),
      color: 'text-blue-400',
    },
    {
      icon: Timer,
      label: 'Avg Handle',
      value: todayStats.avg_duration > 0 ? formatDuration(Math.round(todayStats.avg_duration)) : '—',
      color: 'text-cyan-400',
    },
    {
      icon: Clock,
      label: 'Talk Time',
      value: formatDuration(todayStats.duration),
      color: 'text-purple-400',
    },
    {
      icon: TrendingUp,
      label: 'Total Calls',
      value: String(agent?.calls_answered ?? 0),
      color: 'text-green-400',
    },
  ]

  return (
    <header className="h-14 bg-[#111827] border-b border-gray-800 px-6 flex items-center justify-between flex-shrink-0">
      {/* Left — Agent identity */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Phone className="w-4 h-4 text-blue-500" />
          <span className="text-white font-semibold text-sm">Agent Desktop</span>
        </div>
        <div className="h-5 w-px bg-gray-700" />
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              agent?.status === 1
                ? 'bg-green-500 animate-pulse'
                : agent?.status === 2
                  ? 'bg-yellow-500'
                  : 'bg-gray-500'
            }`}
          />
          <span className="text-xs text-gray-300 font-medium">
            {agent?.name || '—'}
          </span>
          <span className="text-xs text-gray-600">
            ext. {agent?.sip_extension || '—'}
          </span>
        </div>
      </div>

      {/* Center — Metrics */}
      <div className="flex items-center gap-6">
        {metrics.map((m) => (
          <div key={m.label} className="flex items-center gap-2">
            <m.icon className={`w-3.5 h-3.5 ${m.color}`} />
            <div className="flex flex-col">
              <span
                className={`text-sm font-bold leading-none ${m.color} ${
                  m.pulse ? 'animate-pulse' : ''
                }`}
              >
                {m.value}
              </span>
              <span className="text-[10px] text-gray-600 leading-none mt-0.5">
                {m.label}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Right — Connection status */}
      <div className="flex items-center gap-2">
        {wsStatus === 'connected' ? (
          <>
            <Wifi className="w-3.5 h-3.5 text-green-500" />
            <span className="text-xs text-green-500 font-medium">Live</span>
          </>
        ) : wsStatus === 'reconnecting' ? (
          <>
            <WifiOff className="w-3.5 h-3.5 text-yellow-500 animate-pulse" />
            <span className="text-xs text-yellow-500 font-medium">Reconnecting…</span>
          </>
        ) : (
          <>
            <WifiOff className="w-3.5 h-3.5 text-red-500" />
            <span className="text-xs text-red-400 font-medium">Offline</span>
          </>
        )}
      </div>
    </header>
  )
}
