import { useMemo, useState } from 'react'
import {
  Headphones, Mic, Users, PhoneForwarded, CircleDot, Square,
  Radio, Coffee, LogOut, PhoneCall, Activity,
} from 'lucide-react'
import { useAgentTracking, TrackedAgent } from '@/hooks/useAgentTracking'
import { formatTime } from '@/lib/utils'

const STATUS = { LOGGED_OUT: 0, AVAILABLE: 1, ON_BREAK: 2, ON_DEMAND: 3 }

function statusMeta(a: TrackedAgent) {
  if (a.on_call) return { label: 'On Call', color: 'text-blue-400', dot: 'bg-blue-500', ring: 'ring-blue-500/30' }
  if (a.state === 'Receiving') return { label: 'Ringing', color: 'text-amber-400', dot: 'bg-amber-500 animate-pulse', ring: 'ring-amber-500/30' }
  if (a.status === STATUS.ON_BREAK) return { label: 'On Break', color: 'text-orange-400', dot: 'bg-orange-500', ring: 'ring-orange-500/20' }
  if (a.status === STATUS.LOGGED_OUT || !a.registered) return { label: 'Offline', color: 'text-gray-500', dot: 'bg-gray-600', ring: 'ring-gray-700/40' }
  return { label: 'Ready', color: 'text-green-400', dot: 'bg-green-500', ring: 'ring-green-500/20' }
}

export function LiveAgentTracking() {
  const { agents, feed, loading, listen, whisper, barge, takeover, stopMonitor } = useAgentTracking()
  const [busy, setBusy] = useState<number | null>(null)
  const [err, setErr] = useState<string>('')

  const run = async (id: number, fn: () => Promise<any>) => {
    setBusy(id); setErr('')
    try { await fn() } catch (e: any) {
      setErr(e?.response?.data?.error || 'Action failed')
    } finally { setBusy(null) }
  }

  const counts = useMemo(() => {
    const ready = agents.filter(a => a.registered && a.status === STATUS.AVAILABLE && !a.on_call).length
    const onCall = agents.filter(a => a.on_call).length
    const breakC = agents.filter(a => a.status === STATUS.ON_BREAK).length
    const offline = agents.filter(a => !a.registered || a.status === STATUS.LOGGED_OUT).length
    return { ready, onCall, breakC, offline, total: agents.length }
  }, [agents])

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Agent Tracking</h1>
          <p className="text-gray-400">Real-time presence, status & live-call control</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-green-400 text-sm font-medium">Live</span>
        </div>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Summary icon={<CircleDot className="w-5 h-5 text-green-400" />} label="Ready" value={counts.ready} />
        <Summary icon={<PhoneCall className="w-5 h-5 text-blue-400" />} label="On Call" value={counts.onCall} />
        <Summary icon={<Coffee className="w-5 h-5 text-orange-400" />} label="On Break" value={counts.breakC} />
        <Summary icon={<LogOut className="w-5 h-5 text-gray-500" />} label="Offline" value={counts.offline} />
        <Summary icon={<Users className="w-5 h-5 text-purple-400" />} label="Total" value={counts.total} />
      </div>

      {err && (
        <div className="px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
          {err}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent grid */}
        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Agents</h2>
          {loading ? (
            <div className="py-16 text-center text-gray-500 text-sm">Loading agents…</div>
          ) : agents.length === 0 ? (
            <div className="py-16 text-center text-gray-500 text-sm">No agents configured</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {agents.map(a => {
                const m = statusMeta(a)
                const monitored = a.monitoredMode
                return (
                  <div
                    key={a.id}
                    className={`bg-[#111827] border border-gray-800 rounded-2xl p-4 ring-1 ${m.ring} transition-all`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <div className="w-10 h-10 rounded-full bg-[#1F2937] flex items-center justify-center text-sm font-semibold text-gray-200">
                            {a.name.slice(0, 2).toUpperCase()}
                          </div>
                          <span className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[#111827] ${m.dot}`} />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-white leading-tight">{a.name}</div>
                          <div className="text-xs text-gray-500">ext {a.extension || '—'}</div>
                        </div>
                      </div>
                      <span className={`text-xs font-medium ${m.color}`}>{m.label}</span>
                    </div>

                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                      <span>{a.calls_answered} calls</span>
                      <span>{formatTime(a.talk_time || 0)} talk</span>
                      {monitored && (
                        <span className="ml-auto inline-flex items-center gap-1 text-purple-400">
                          <Radio className="w-3 h-3" /> {monitored}
                        </span>
                      )}
                    </div>

                    {/* Live-call controls */}
                    <div className="grid grid-cols-4 gap-1.5 mt-4">
                      <CtrlBtn label="Listen" disabled={!a.on_call || busy === a.id}
                        onClick={() => run(a.id, () => listen(a.id))}
                        icon={<Headphones className="w-3.5 h-3.5" />} />
                      <CtrlBtn label="Whisper" disabled={!a.on_call || busy === a.id}
                        onClick={() => run(a.id, () => whisper(a.id))}
                        icon={<Mic className="w-3.5 h-3.5" />} />
                      <CtrlBtn label="Barge" disabled={!a.on_call || busy === a.id}
                        onClick={() => run(a.id, () => barge(a.id))}
                        icon={<Users className="w-3.5 h-3.5" />} />
                      <CtrlBtn label="Take" disabled={!a.on_call || busy === a.id} danger
                        onClick={() => run(a.id, () => takeover(a.id))}
                        icon={<PhoneForwarded className="w-3.5 h-3.5" />} />
                    </div>
                    {monitored && (
                      <button
                        onClick={() => run(a.id, () => stopMonitor(a.id))}
                        className="mt-2 w-full flex items-center justify-center gap-1.5 py-1.5 text-xs text-gray-300 bg-[#1F2937] hover:bg-gray-700 rounded-lg transition-colors"
                      >
                        <Square className="w-3 h-3" /> Stop monitoring
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Live call feed */}
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Live Call Feed</h2>
          <div className="bg-[#111827] border border-gray-800 rounded-2xl divide-y divide-gray-800/60 max-h-[560px] overflow-y-auto">
            {feed.length === 0 ? (
              <div className="py-12 text-center text-gray-600 text-sm flex flex-col items-center gap-2">
                <Activity className="w-6 h-6 text-gray-700" /> Waiting for activity…
              </div>
            ) : feed.map((f, i) => (
              <div key={i} className="px-4 py-3 flex items-center gap-3">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  f.event === 'answered' ? 'bg-blue-500'
                  : f.event === 'ringing' ? 'bg-amber-500' : 'bg-gray-600'
                }`} />
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-gray-200 truncate">
                    {f.agent_name || 'Agent'} · <span className="text-gray-400">{f.event}</span>
                  </div>
                  <div className="text-xs text-gray-600 truncate">
                    {f.caller || '—'} {f.duration ? `· ${formatTime(f.duration)}` : ''}
                  </div>
                </div>
                <span className="text-[10px] text-gray-600 flex-shrink-0">
                  {new Date(f.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Summary({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-1">{icon}<span className="text-xs text-gray-500">{label}</span></div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}

function CtrlBtn({ label, icon, onClick, disabled, danger }: {
  label: string; icon: React.ReactNode; onClick: () => void; disabled?: boolean; danger?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={label}
      className={`flex flex-col items-center gap-1 py-2 rounded-lg text-[10px] transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${
        danger
          ? 'text-red-400 bg-red-500/10 hover:bg-red-500/20'
          : 'text-gray-300 bg-[#1F2937] hover:bg-gray-700'
      }`}
    >
      {icon}{label}
    </button>
  )
}
