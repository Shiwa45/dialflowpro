import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { useAgentCommands } from '@/hooks/useAgentCommands'
import { formatTime } from '@/lib/utils'
import {
  Layers,
  Clock,
  PhoneIncoming,
  Users,
} from 'lucide-react'

export function BottomBar() {
  const {
    agent,
    queues,
    selectedQueueId,
    activeCall,
    callDuration,
    wrapUpTime,
  } = useAgentDesktopStore()
  const { selectQueue } = useAgentCommands()

  const selectedQueue = queues.find((q) => q.id === selectedQueueId)
  const totalWaiting = queues.reduce((sum, q) => sum + (q.waiting_calls || 0), 0)

  return (
    <footer className="h-12 bg-[#111827] border-t border-gray-800 px-6 flex items-center justify-between flex-shrink-0">
      {/* Left — Queue selector */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-gray-500" />
          <select
            value={selectedQueueId ?? ''}
            onChange={(e) => selectQueue(Number(e.target.value))}
            className="bg-transparent border-none text-xs text-gray-300 focus:outline-none cursor-pointer hover:text-white"
          >
            {queues.length === 0 && (
              <option value="">No queues</option>
            )}
            {queues.map((q) => (
              <option key={q.id} value={q.id} className="bg-[#1F2937]">
                {q.name}
                {q.waiting_calls > 0 ? ` (${q.waiting_calls} waiting)` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Queue stats */}
        {selectedQueue && (
          <>
            <div className="h-4 w-px bg-gray-700" />
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <PhoneIncoming className="w-3 h-3" />
                {selectedQueue.waiting_calls || 0} waiting
              </span>
              {selectedQueue.active_agents !== undefined && (
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {selectedQueue.active_agents} active
                </span>
              )}
            </div>
          </>
        )}
      </div>

      {/* Center — Active call info */}
      {activeCall && activeCall.state !== 'idle' && (
        <div className="flex items-center gap-3">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              activeCall.state === 'active'
                ? 'bg-green-500 animate-pulse'
                : activeCall.state === 'held'
                  ? 'bg-yellow-500'
                  : activeCall.state === 'ringing'
                    ? 'bg-blue-500 animate-pulse'
                    : 'bg-orange-500'
            }`}
          />
          <span className="text-xs text-gray-400">
            {activeCall.state === 'ringing'
              ? 'Incoming call'
              : activeCall.state === 'held'
                ? 'On hold'
                : activeCall.state === 'wrap_up'
                  ? `Wrap-up ${wrapUpTime > 0 ? formatTime(wrapUpTime) : ''}`
                  : formatTime(callDuration)}
          </span>
        </div>
      )}

      {/* Right — Status + queue count */}
      <div className="flex items-center gap-3 text-xs">
        {totalWaiting > 0 && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-orange-500/10 border border-orange-500/20 rounded-full">
            <PhoneIncoming className="w-3 h-3 text-orange-400" />
            <span className="text-orange-400 font-medium">
              {totalWaiting} in queue{totalWaiting !== 1 ? 's' : ''}
            </span>
          </div>
        )}

        <div className="flex items-center gap-1.5">
          <div
            className={`w-2 h-2 rounded-full ${
              agent?.status === 1
                ? 'bg-green-500'
                : agent?.status === 2
                  ? 'bg-yellow-500'
                  : 'bg-gray-500'
            }`}
          />
          <span className="text-gray-400 font-medium">
            {agent?.status_display || 'Offline'}
          </span>
        </div>

        <div className="h-4 w-px bg-gray-700" />

        <span className="text-gray-600">
          {queues.length} queue{queues.length !== 1 ? 's' : ''}
        </span>
      </div>
    </footer>
  )
}
