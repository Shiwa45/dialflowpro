import { useMemo, useState } from 'react'
import {
  Bot, Phone, ArrowRightLeft, CalendarClock, CheckCircle2, XCircle,
  Clock, X, MessageSquare, Smile, Frown, Meh, PhoneOutgoing,
} from 'lucide-react'
import { useAISessions, useAISessionDetail, useAICallbacks, AISessionListItem } from '@/hooks/useAISessions'
import { formatTime } from '@/lib/utils'

const OUTCOME_META: Record<string, { label: string; cls: string; icon: any }> = {
  resolved:    { label: 'Resolved',    cls: 'bg-green-500/10 text-green-400 border-green-500/20', icon: CheckCircle2 },
  transferred: { label: 'Transferred', cls: 'bg-blue-500/10 text-blue-400 border-blue-500/20', icon: ArrowRightLeft },
  callback:    { label: 'Callback',    cls: 'bg-purple-500/10 text-purple-400 border-purple-500/20', icon: CalendarClock },
  abandoned:   { label: 'Abandoned',   cls: 'bg-gray-500/10 text-gray-400 border-gray-700', icon: XCircle },
  failed:      { label: 'Failed',      cls: 'bg-red-500/10 text-red-400 border-red-500/20', icon: XCircle },
}

function sentimentIcon(score: number | null) {
  if (score == null) return <Meh className="w-4 h-4 text-gray-600" />
  if (score >= 0.33) return <Smile className="w-4 h-4 text-green-400" />
  if (score <= -0.33) return <Frown className="w-4 h-4 text-red-400" />
  return <Meh className="w-4 h-4 text-yellow-400" />
}

export function AICallReviewPage() {
  const { sessions, loading } = useAISessions()
  const [tab, setTab] = useState<'calls' | 'callbacks'>('calls')
  const [openId, setOpenId] = useState<number | null>(null)
  const [outcomeFilter, setOutcomeFilter] = useState<string>('all')

  const filtered = useMemo(
    () => outcomeFilter === 'all' ? sessions : sessions.filter(s => s.outcome === outcomeFilter),
    [sessions, outcomeFilter]
  )

  const metrics = useMemo(() => {
    const total = sessions.length
    const resolved = sessions.filter(s => s.outcome === 'resolved').length
    const transferred = sessions.filter(s => s.outcome === 'transferred').length
    const callback = sessions.filter(s => s.outcome === 'callback').length
    const avg = total ? Math.round(sessions.reduce((a, s) => a + s.duration_seconds, 0) / total) : 0
    const containment = total ? Math.round((resolved / total) * 100) : 0
    return { total, resolved, transferred, callback, avg, containment }
  }, [sessions])

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1 flex items-center gap-2">
            <Bot className="w-7 h-7 text-blue-400" /> AI Call Review
          </h1>
          <p className="text-gray-400">Transcripts, outcomes & callbacks from AI-handled calls</p>
        </div>
      </div>

      {/* metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Metric icon={<Phone className="w-5 h-5 text-blue-400" />} label="Total AI calls" value={metrics.total} />
        <Metric icon={<CheckCircle2 className="w-5 h-5 text-green-400" />} label="Containment" value={`${metrics.containment}%`} />
        <Metric icon={<ArrowRightLeft className="w-5 h-5 text-blue-400" />} label="Transferred" value={metrics.transferred} />
        <Metric icon={<CalendarClock className="w-5 h-5 text-purple-400" />} label="Callbacks" value={metrics.callback} />
        <Metric icon={<Clock className="w-5 h-5 text-gray-400" />} label="Avg duration" value={formatTime(metrics.avg)} />
      </div>

      {/* tabs */}
      <div className="flex gap-1 bg-[#111827] border border-gray-800 rounded-xl p-1 w-fit">
        <TabBtn active={tab === 'calls'} onClick={() => setTab('calls')} icon={MessageSquare} label="Call History" />
        <TabBtn active={tab === 'callbacks'} onClick={() => setTab('callbacks')} icon={CalendarClock} label="Callbacks" />
      </div>

      {tab === 'calls' ? (
        <>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Filter:</span>
            {['all', 'resolved', 'transferred', 'callback', 'abandoned', 'failed'].map(o => (
              <button key={o} onClick={() => setOutcomeFilter(o)}
                className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
                  outcomeFilter === o ? 'bg-blue-500 text-white' : 'bg-[#1F2937] text-gray-400 hover:text-white'}`}>
                {o === 'all' ? 'All' : (OUTCOME_META[o]?.label ?? o)}
              </button>
            ))}
          </div>

          <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
            {loading ? (
              <div className="py-16 text-center text-gray-500 text-sm">Loading…</div>
            ) : filtered.length === 0 ? (
              <div className="py-16 text-center text-gray-600 text-sm">No AI calls yet</div>
            ) : (
              <table className="w-full">
                <thead className="bg-[#0D1117]">
                  <tr>
                    {['Time', 'Caller', 'AI Agent', 'Language', 'Outcome', 'Sentiment', 'Duration'].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {filtered.map((s: AISessionListItem) => {
                    const m = OUTCOME_META[s.outcome] ?? OUTCOME_META.failed
                    return (
                      <tr key={s.id} onClick={() => setOpenId(s.id)}
                        className="hover:bg-[#1F2937]/40 cursor-pointer transition-colors">
                        <td className="px-5 py-3.5 text-sm text-gray-300">
                          {s.started_at ? new Date(s.started_at).toLocaleString() : '—'}
                        </td>
                        <td className="px-5 py-3.5 text-sm text-gray-200 font-medium">{s.caller_number || '—'}</td>
                        <td className="px-5 py-3.5 text-sm text-gray-400">{s.agent_name}</td>
                        <td className="px-5 py-3.5 text-sm text-gray-400">{s.detected_language || '—'}</td>
                        <td className="px-5 py-3.5">
                          <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border ${m.cls}`}>
                            <m.icon className="w-3 h-3" /> {m.label}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">{sentimentIcon(s.sentiment_score)}</td>
                        <td className="px-5 py-3.5 text-sm text-gray-400">{formatTime(s.duration_seconds)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </>
      ) : (
        <CallbacksTab />
      )}

      {openId !== null && <TranscriptDrawer id={openId} onClose={() => setOpenId(null)} />}
    </div>
  )
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-1">{icon}<span className="text-xs text-gray-500">{label}</span></div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}

function TabBtn({ active, onClick, icon: Icon, label }: any) {
  return (
    <button onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm transition-colors ${
        active ? 'bg-blue-500 text-white' : 'text-gray-400 hover:text-white'}`}>
      <Icon className="w-4 h-4" /> {label}
    </button>
  )
}

function TranscriptDrawer({ id, onClose }: { id: number; onClose: () => void }) {
  const { session, loading } = useAISessionDetail(id)
  const m = session ? (OUTCOME_META[session.outcome] ?? OUTCOME_META.failed) : null

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative w-full max-w-xl bg-[#0D1117] border-l border-gray-800 h-full overflow-y-auto"
        onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-[#0D1117] border-b border-gray-800 px-5 py-4 flex items-center justify-between">
          <h3 className="font-semibold text-white">Call Transcript</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X className="w-5 h-5" /></button>
        </div>

        {loading || !session ? (
          <div className="py-16 text-center text-gray-500 text-sm">Loading…</div>
        ) : (
          <div className="p-5 space-y-5">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Detail label="Caller" value={session.caller_number || '—'} />
              <Detail label="AI Agent" value={session.agent_name} />
              <Detail label="Language" value={session.detected_language || '—'} />
              <Detail label="Duration" value={formatTime(session.duration_seconds)} />
              <Detail label="Outcome" value={
                m && <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border ${m.cls}`}><m.icon className="w-3 h-3" /> {m.label}</span>
              } />
              {session.transfer_reason && <Detail label="Transfer reason" value={session.transfer_reason} />}
            </div>

            {session.summary && (
              <div className="bg-[#111827] border border-gray-800 rounded-xl p-4">
                <div className="text-xs text-gray-500 mb-1">AI Summary</div>
                <p className="text-sm text-gray-300">{session.summary}</p>
              </div>
            )}

            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Conversation</div>
              <div className="space-y-3">
                {session.turns.length === 0 ? (
                  <p className="text-sm text-gray-600">No transcript captured.</p>
                ) : session.turns.map(t => (
                  <div key={t.id} className={`flex ${t.role === 'caller' ? 'justify-start' : 'justify-end'}`}>
                    <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                      t.role === 'caller' ? 'bg-[#1F2937] text-gray-200'
                      : t.role === 'ai' ? 'bg-blue-500/15 text-blue-100 border border-blue-500/20'
                      : 'bg-transparent text-gray-500 text-xs italic'}`}>
                      {t.role !== 'system' && (
                        <div className="text-[10px] uppercase tracking-wide opacity-60 mb-0.5">
                          {t.role === 'caller' ? 'Caller' : 'AI'}
                        </div>
                      )}
                      {t.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-gray-200">{value}</div>
    </div>
  )
}

function CallbacksTab() {
  const { callbacks, loading, setStatus } = useAICallbacks()
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
      {loading ? (
        <div className="py-16 text-center text-gray-500 text-sm">Loading…</div>
      ) : callbacks.length === 0 ? (
        <div className="py-16 text-center text-gray-600 text-sm">No callbacks scheduled by AI</div>
      ) : (
        <table className="w-full">
          <thead className="bg-[#0D1117]">
            <tr>
              {['Requested for', 'Caller', 'Notes', 'Status', ''].map(h => (
                <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {callbacks.map(cb => (
              <tr key={cb.id} className="hover:bg-[#1F2937]/40">
                <td className="px-5 py-3.5 text-sm text-gray-200">
                  <span className="inline-flex items-center gap-1.5">
                    <PhoneOutgoing className="w-3.5 h-3.5 text-purple-400" />
                    {new Date(cb.requested_for).toLocaleString()}
                  </span>
                </td>
                <td className="px-5 py-3.5 text-sm text-gray-200 font-medium">{cb.caller_number}</td>
                <td className="px-5 py-3.5 text-sm text-gray-400 max-w-xs truncate">{cb.notes || '—'}</td>
                <td className="px-5 py-3.5">
                  <span className={`text-xs px-2 py-1 rounded-full border ${
                    cb.status === 'done' ? 'bg-green-500/10 text-green-400 border-green-500/20'
                    : cb.status === 'cancelled' ? 'bg-gray-500/10 text-gray-400 border-gray-700'
                    : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>
                    {cb.status}
                  </span>
                </td>
                <td className="px-5 py-3.5 text-right">
                  {cb.status === 'pending' && (
                    <div className="flex items-center justify-end gap-1.5">
                      <button onClick={() => setStatus(cb.id, 'done')}
                        className="text-xs px-2.5 py-1 text-green-400 bg-green-500/10 hover:bg-green-500/20 rounded-lg">Mark done</button>
                      <button onClick={() => setStatus(cb.id, 'cancelled')}
                        className="text-xs px-2.5 py-1 text-gray-400 bg-[#1F2937] hover:bg-gray-700 rounded-lg">Cancel</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
