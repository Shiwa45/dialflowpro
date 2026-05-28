import { useEffect, useState } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Activity, Phone, Users, Clock, TrendingUp, AlertCircle } from 'lucide-react'
import { formatTime } from '@/lib/utils'

export function LiveMonitoring() {
  const [stats, setStats] = useState({
    totalAgents: 0,
    availableAgents: 0,
    onCallAgents: 0,
    totalQueues: 0,
    waitingCalls: 0,
    activeCalls: 0,
    longestWait: 0,
    avgWaitTime: 0,
    serviceLevel: 0,
  })

  const [queues, setQueues] = useState<any[]>([])
  const [agents, setAgents] = useState<any[]>([])
  const [recentCalls, setRecentCalls] = useState<any[]>([])

  // WebSocket for live updates
  useWebSocket('/ws/callcenter/dashboard/', {
    onMessage: (data) => {
      if (data.type === 'dashboard_update') {
        setStats({
          totalAgents: data.total_agents,
          availableAgents: data.available_agents,
          onCallAgents: data.on_call_agents,
          totalQueues: data.total_queues,
          waitingCalls: data.total_waiting_calls,
          activeCalls: data.total_active_calls,
          longestWait: data.longest_wait_time,
          avgWaitTime: data.avg_wait_time,
          serviceLevel: data.service_level,
        })
      }
      
      if (data.type === 'queue_update') {
        setQueues(prev => {
          const idx = prev.findIndex(q => q.id === data.queue_id)
          if (idx >= 0) {
            const updated = [...prev]
            updated[idx] = { ...updated[idx], ...data }
            return updated
          }
          return prev
        })
      }

      if (data.type === 'agent_status') {
        setAgents(prev => {
          const idx = prev.findIndex(a => a.id === data.agent_id)
          if (idx >= 0) {
            const updated = [...prev]
            updated[idx] = { ...updated[idx], status: data.status, state: data.state }
            return updated
          }
          return prev
        })
      }

      if (data.type === 'call_event') {
        setRecentCalls(prev => [data, ...prev.slice(0, 19)])
      }
    },
  })

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Live Monitoring</h1>
          <p className="text-gray-400">Real-time call center performance</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-green-400 text-sm font-medium">Live</span>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Users className="w-6 h-6 text-blue-400" />}
          label="Available Agents"
          value={`${stats.availableAgents} / ${stats.totalAgents}`}
          trend={`${stats.onCallAgents} on call`}
          bgColor="bg-blue-500/10"
        />
        <MetricCard
          icon={<Phone className="w-6 h-6 text-purple-400" />}
          label="Active Calls"
          value={stats.activeCalls}
          trend={`${stats.waitingCalls} waiting`}
          bgColor="bg-purple-500/10"
        />
        <MetricCard
          icon={<Clock className="w-6 h-6 text-orange-400" />}
          label="Avg Wait Time"
          value={formatTime(stats.avgWaitTime)}
          trend={`Longest: ${formatTime(stats.longestWait)}`}
          bgColor="bg-orange-500/10"
        />
        <MetricCard
          icon={<TrendingUp className="w-6 h-6 text-green-400" />}
          label="Service Level"
          value={`${stats.serviceLevel}%`}
          trend="Last hour"
          bgColor="bg-green-500/10"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queue Status */}
        <div className="bg-[#111827] border border-gray-800 rounded-lg">
          <div className="p-4 border-b border-gray-800">
            <h3 className="text-lg font-semibold text-white">Queue Status</h3>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {queues.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No active queues
              </div>
            ) : (
              queues.map((queue) => (
                <QueueCard key={queue.id} queue={queue} />
              ))
            )}
          </div>
        </div>

        {/* Agent Status */}
        <div className="bg-[#111827] border border-gray-800 rounded-lg">
          <div className="p-4 border-b border-gray-800">
            <h3 className="text-lg font-semibold text-white">Agent Status</h3>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {agents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No agents online
              </div>
            ) : (
              agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Call Activity */}
      <div className="bg-[#111827] border border-gray-800 rounded-lg">
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">Recent Call Activity</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#1F2937] border-b border-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Number</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Queue</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Agent</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {recentCalls.map((call, idx) => (
                <tr key={idx} className="hover:bg-[#1F2937]">
                  <td className="px-4 py-3 text-sm text-gray-300">
                    {new Date(call.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-white font-mono">
                    {call.caller_number}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">{call.queue_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-300">{call.agent_name || '-'}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      call.status === 'answered' 
                        ? 'bg-green-500/10 text-green-400'
                        : call.status === 'ringing'
                        ? 'bg-blue-500/10 text-blue-400'
                        : 'bg-gray-500/10 text-gray-400'
                    }`}>
                      {call.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">
                    {call.duration ? formatTime(call.duration) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, trend, bgColor }: any) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-lg p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 ${bgColor} rounded-lg`}>{icon}</div>
        <div className="text-sm text-gray-400">{label}</div>
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-xs text-gray-500">{trend}</div>
    </div>
  )
}

function QueueCard({ queue }: any) {
  return (
    <div className="p-3 bg-[#1F2937] border border-gray-700 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-white">{queue.name}</h4>
        <span className="text-xs text-gray-400">{queue.strategy_display}</span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <div className="text-gray-500">Waiting</div>
          <div className="text-white font-medium">{queue.waiting_calls || 0}</div>
        </div>
        <div>
          <div className="text-gray-500">Agents</div>
          <div className="text-white font-medium">{queue.active_agents || 0}</div>
        </div>
        <div>
          <div className="text-gray-500">Longest Wait</div>
          <div className="text-white font-medium">
            {formatTime(queue.longest_wait || 0)}
          </div>
        </div>
      </div>
    </div>
  )
}

function AgentCard({ agent }: any) {
  const statusColor = {
    1: 'bg-green-500',
    2: 'bg-yellow-500',
    0: 'bg-gray-500',
  }[agent.status] || 'bg-gray-500'

  return (
    <div className="p-3 bg-[#1F2937] border border-gray-700 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${statusColor}`} />
          <div>
            <div className="text-sm font-medium text-white">{agent.name}</div>
            <div className="text-xs text-gray-400">{agent.state_display}</div>
          </div>
        </div>
        <div className="text-right text-xs text-gray-400">
          <div>Calls: {agent.calls_answered}</div>
          <div>Talk: {formatTime(agent.talk_time)}</div>
        </div>
      </div>
    </div>
  )
}
