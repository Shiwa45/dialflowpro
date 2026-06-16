import { useEffect, useState, useCallback } from 'react'
import {
  Plus, Pencil, Trash2, X, AlertTriangle, RefreshCw,
  Users, Phone, PhoneIncoming, Settings, UserPlus,
  UserMinus, Activity, ListOrdered, CheckCircle2,
} from 'lucide-react'
import api from '@/api/client'

/* ─── constants ─────────────────────────────────────────── */
const STRATEGIES = [
  { value: 1, label: 'Ring All' },
  { value: 2, label: 'Longest Idle Agent' },
  { value: 3, label: 'Round Robin' },
  { value: 4, label: 'Top Down' },
  { value: 5, label: 'Least Talk Time' },
  { value: 6, label: 'Fewest Calls' },
  { value: 7, label: 'Sequential' },
  { value: 8, label: 'Random' },
]
const strategyLabel = (v: number) => STRATEGIES.find(s => s.value === v)?.label ?? `Strategy ${v}`

/* ─── shared styles ─────────────────────────────────────── */
const inp = 'w-full px-4 py-2.5 bg-[#1F2937] border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 placeholder-gray-500'
const lbl = 'block text-sm font-medium text-gray-300 mb-1.5'

/* ═══ Modal shell ═══════════════════════════════════════════ */
function Modal({
  title, onClose, children, wide,
}: {
  title: string; onClose: () => void; children: React.ReactNode; wide?: boolean
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className={`bg-[#0D1117] border border-gray-700 rounded-2xl shadow-2xl max-h-[90vh] overflow-y-auto w-full ${wide ? 'max-w-3xl' : 'max-w-lg'}`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 sticky top-0 bg-[#0D1117] z-10">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-white rounded-lg hover:bg-gray-800 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}

function ModalFooter({ onClose, busy, label }: { onClose: () => void; busy: boolean; label: string }) {
  return (
    <div className="flex gap-3 pt-4 border-t border-gray-800 mt-4">
      <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">
        Cancel
      </button>
      <button type="submit" disabled={busy} className="flex-1 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-colors text-sm font-medium">
        {busy ? 'Saving…' : label}
      </button>
    </div>
  )
}

/* ═══ Create / Edit Queue Modal ════════════════════════════ */
const BLANK: Record<string, any> = {
  name: '', description: '', strategy: 3,
  max_wait_time: 0, max_wait_time_with_no_agent: 0,
  ring_progressively_delay: 10, discard_abandoned_after: 60,
  time_base_score: 0, tier_rules_apply: false,
  tier_rule_wait_second: 0, tier_rule_wait_multiply_level: false,
  tier_rule_no_agent_no_wait: false, moh_sound: '',
}

function QueueModal({ initial, onSave, onClose }: {
  initial?: any; onSave: () => void; onClose: () => void
}) {
  const isEdit = !!initial
  const [form, setForm] = useState<typeof BLANK>(isEdit ? {
    name: initial.name ?? '',
    description: initial.description ?? '',
    strategy: initial.strategy ?? 3,
    max_wait_time: initial.max_wait_time ?? 0,
    max_wait_time_with_no_agent: initial.max_wait_time_with_no_agent ?? 0,
    ring_progressively_delay: initial.ring_progressively_delay ?? 10,
    discard_abandoned_after: initial.discard_abandoned_after ?? 60,
    time_base_score: initial.time_base_score ?? 0,
    tier_rules_apply: initial.tier_rules_apply ?? false,
    tier_rule_wait_second: initial.tier_rule_wait_second ?? 0,
    tier_rule_wait_multiply_level: initial.tier_rule_wait_multiply_level ?? false,
    tier_rule_no_agent_no_wait: initial.tier_rule_no_agent_no_wait ?? false,
    moh_sound: initial.moh_sound ?? '',
  } : { ...BLANK })
  const [busy, setBusy] = useState(false)
  const [err,  setErr]  = useState('')
  const [tab,  setTab]  = useState<'basic' | 'advanced'>('basic')

  const set = (p: Partial<typeof BLANK>) => setForm(f => ({ ...f, ...p }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      isEdit
        ? await api.patch(`/callcenter/queues/${initial.id}/`, form)
        : await api.post('/callcenter/queues/', form)
      onSave()
    } catch (e: any) {
      const d = e?.response?.data
      setErr(typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Failed to save queue.')
    } finally { setBusy(false) }
  }

  return (
    <Modal title={isEdit ? `Edit Queue — ${initial.name}` : 'Create New Queue'} onClose={onClose}>
      <form onSubmit={submit}>
        {err && <p className="text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-3 py-2 mb-4">{err}</p>}

        {/* Tab switcher */}
        <div className="flex gap-1 mb-5 bg-gray-800/50 p-1 rounded-xl">
          {(['basic', 'advanced'] as const).map(t => (
            <button key={t} type="button" onClick={() => setTab(t)}
              className={`flex-1 py-1.5 text-sm rounded-lg transition-colors capitalize ${tab === t ? 'bg-blue-500 text-white font-medium' : 'text-gray-400 hover:text-gray-300'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Basic tab */}
        {tab === 'basic' && (
          <div className="space-y-4">
            <div>
              <label className={lbl}>Queue Name <span className="text-red-400">*</span></label>
              <input value={form.name} onChange={e => set({ name: e.target.value })}
                className={inp} placeholder="e.g. Sales Queue" required />
            </div>
            <div>
              <label className={lbl}>Description</label>
              <textarea value={form.description} onChange={e => set({ description: e.target.value })}
                className={inp} rows={2} placeholder="Optional notes about this queue" />
            </div>
            <div>
              <label className={lbl}>Routing Strategy <span className="text-red-400">*</span></label>
              <select value={form.strategy} onChange={e => set({ strategy: Number(e.target.value) })} className={inp}>
                {STRATEGIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
              <p className="text-xs text-gray-600 mt-1.5">Determines which available agent receives the next call.</p>
            </div>
            <div>
              <label className={lbl}>Music on Hold (sound file path)</label>
              <input value={form.moh_sound} onChange={e => set({ moh_sound: e.target.value })}
                className={inp} placeholder="e.g. local_stream://default" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={lbl}>Max Wait Time (s)</label>
                <input type="number" min={0} value={form.max_wait_time} onChange={e => set({ max_wait_time: Number(e.target.value) })} className={inp} />
                <p className="text-xs text-gray-600 mt-1">0 = unlimited</p>
              </div>
              <div>
                <label className={lbl}>Max Wait (no agents) (s)</label>
                <input type="number" min={0} value={form.max_wait_time_with_no_agent} onChange={e => set({ max_wait_time_with_no_agent: Number(e.target.value) })} className={inp} />
                <p className="text-xs text-gray-600 mt-1">0 = unlimited</p>
              </div>
              <div>
                <label className={lbl}>Ring Delay (s)</label>
                <input type="number" min={1} value={form.ring_progressively_delay} onChange={e => set({ ring_progressively_delay: Number(e.target.value) })} className={inp} />
                <p className="text-xs text-gray-600 mt-1">Between ring attempts</p>
              </div>
              <div>
                <label className={lbl}>Discard Abandoned After (s)</label>
                <input type="number" min={0} value={form.discard_abandoned_after} onChange={e => set({ discard_abandoned_after: Number(e.target.value) })} className={inp} />
                <p className="text-xs text-gray-600 mt-1">Remove abandoned calls</p>
              </div>
            </div>
          </div>
        )}

        {/* Advanced tab */}
        {tab === 'advanced' && (
          <div className="space-y-4">
            <div>
              <label className={lbl}>Time Base Score (s)</label>
              <input type="number" min={0} value={form.time_base_score} onChange={e => set({ time_base_score: Number(e.target.value) })} className={inp} />
              <p className="text-xs text-gray-600 mt-1.5">Seconds before increasing caller priority in queue.</p>
            </div>

            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider pt-2">Tier Rules</p>

            <label className="flex items-center gap-3 p-3 bg-gray-800/40 border border-gray-700 rounded-xl cursor-pointer hover:border-gray-600 transition-colors">
              <input type="checkbox" checked={form.tier_rules_apply} onChange={e => set({ tier_rules_apply: e.target.checked })} className="w-4 h-4 rounded text-blue-500 bg-gray-700 border-gray-600" />
              <span className="text-sm text-gray-300">Apply tier rules (route by tier level)</span>
            </label>

            {form.tier_rules_apply && (
              <div className="pl-2 space-y-3 border-l-2 border-blue-500/30">
                <div>
                  <label className={lbl}>Tier Wait Seconds</label>
                  <input type="number" min={0} value={form.tier_rule_wait_second} onChange={e => set({ tier_rule_wait_second: Number(e.target.value) })} className={inp} />
                  <p className="text-xs text-gray-600 mt-1">Wait before trying next tier level.</p>
                </div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={form.tier_rule_wait_multiply_level} onChange={e => set({ tier_rule_wait_multiply_level: e.target.checked })} className="w-4 h-4 rounded text-blue-500 bg-gray-700 border-gray-600" />
                  <span className="text-sm text-gray-300">Multiply wait time by tier level</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={form.tier_rule_no_agent_no_wait} onChange={e => set({ tier_rule_no_agent_no_wait: e.target.checked })} className="w-4 h-4 rounded text-blue-500 bg-gray-700 border-gray-600" />
                  <span className="text-sm text-gray-300">Skip tier immediately if no agents available</span>
                </label>
              </div>
            )}
          </div>
        )}

        <ModalFooter onClose={onClose} busy={busy} label={isEdit ? 'Save Changes' : 'Create Queue'} />
      </form>
    </Modal>
  )
}

/* ═══ Manage Queue Modal (Agents + Stats tabs) ═════════════ */
function ManageQueueModal({ queue, onClose, onQueueUpdated }: {
  queue: any; onClose: () => void; onQueueUpdated: () => void
}) {
  const [tab,          setTab]         = useState<'agents' | 'stats'>('agents')
  const [tiers,        setTiers]       = useState<any[]>([])
  const [agents,       setAgents]      = useState<any[]>([])
  const [loading,      setLoading]     = useState(true)
  const [showAssign,   setShowAssign]  = useState(false)
  const [removeId,     setRemoveId]    = useState<number | null>(null)
  const [showEdit,     setShowEdit]    = useState(false)
  const [toastMsg,     setToastMsg]    = useState('')

  const toast = (msg: string) => { setToastMsg(msg); setTimeout(() => setToastMsg(''), 3000) }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [tiersRes, agentsRes] = await Promise.all([
        api.get(`/callcenter/tiers/?queue=${queue.id}`),
        api.get('/callcenter/agents/'),
      ])
      const agentMap = new Map(
        (agentsRes.data.results ?? agentsRes.data).map((a: any) => [a.id, a])
      )
      const raw: any[] = tiersRes.data.results ?? tiersRes.data
      setTiers(raw.map(t => ({
        ...t,
        agent_name:      t.agent_name      ?? agentMap.get(t.agent)?.name          ?? `Agent #${t.agent}`,
        agent_extension: t.agent_extension ?? agentMap.get(t.agent)?.sip_extension ?? null,
      })))
      setAgents(agentsRes.data.results ?? agentsRes.data)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }, [queue.id])

  useEffect(() => { load() }, [load])

  const handleRemove = async (tierId: number) => {
    try {
      await api.delete(`/callcenter/tiers/${tierId}/`)
      setRemoveId(null); load(); toast('Agent removed from queue.')
    } catch (e) { console.error(e) }
  }

  const assignedIds   = new Set(tiers.map(t => t.agent))
  const availAgents   = agents.filter(a => !assignedIds.has(a.id))

  return (
    <>
      <Modal title={`Manage — ${queue.name}`} onClose={onClose} wide>
        {toastMsg && (
          <div className="fixed top-6 right-6 z-[60] bg-green-500 text-white text-sm font-medium px-4 py-2.5 rounded-xl shadow-lg flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> {toastMsg}
          </div>
        )}

        {/* Queue summary bar */}
        <div className="flex items-center gap-4 p-4 bg-gray-800/40 border border-gray-700 rounded-xl mb-5">
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
            <ListOrdered className="w-5 h-5 text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-white text-sm">{queue.name}</div>
            <div className="text-xs text-gray-500 mt-0.5">
              {strategyLabel(queue.strategy)} · Ring delay {queue.ring_progressively_delay ?? 10}s
            </div>
          </div>
          <button onClick={() => setShowEdit(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 hover:text-white border border-gray-700 hover:border-gray-600 rounded-lg transition-colors flex-shrink-0">
            <Pencil className="w-3 h-3" /> Edit Settings
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-5 bg-gray-800/50 p-1 rounded-xl">
          {[
            { key: 'agents', label: 'Agent Assignments', icon: Users },
            { key: 'stats',  label: 'Queue Stats',       icon: Activity },
          ].map(t => (
            <button key={t.key} onClick={() => setTab(t.key as any)}
              className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm rounded-lg transition-colors ${tab === t.key ? 'bg-blue-500 text-white font-medium' : 'text-gray-400 hover:text-gray-300'}`}>
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </div>

        {/* ── Agents tab ───────────────────────────────────── */}
        {tab === 'agents' && (
          <>
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-gray-400">
                {tiers.length} agent{tiers.length !== 1 ? 's' : ''} assigned
              </p>
              <button onClick={() => setShowAssign(true)} disabled={availAgents.length === 0}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-xl transition-colors">
                <UserPlus className="w-4 h-4" /> Assign Agent
              </button>
            </div>

            {loading ? (
              <div className="py-10 flex items-center justify-center gap-2 text-gray-500">
                <RefreshCw className="w-4 h-4 animate-spin" /> Loading…
              </div>
            ) : tiers.length === 0 ? (
              <div className="py-12 text-center">
                <Users className="w-12 h-12 text-gray-700 mx-auto mb-3" />
                <p className="text-sm text-gray-500 mb-1">No agents assigned to this queue yet.</p>
                <p className="text-xs text-gray-600">Click "Assign Agent" to start routing calls here.</p>
              </div>
            ) : (
              <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-[#0D1117] border-b border-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Agent</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Extension</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Level</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Position</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/60">
                    {tiers.map(tier => (
                      <TierRow key={tier.id} tier={tier}
                        onRemove={() => setRemoveId(tier.id)}
                        onUpdated={() => { load(); toast('Tier updated.') }}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {!loading && availAgents.length === 0 && agents.length > 0 && tiers.length > 0 && (
              <p className="text-xs text-gray-600 mt-2 text-center">All available agents are already assigned.</p>
            )}
          </>
        )}

        {/* ── Stats tab ────────────────────────────────────── */}
        {tab === 'stats' && <QueueStatsPanel queue={queue} />}
      </Modal>

      {/* Assign agent sub-modal */}
      {showAssign && (
        <AssignAgentModal
          queueId={queue.id}
          availableAgents={availAgents}
          onSave={() => { setShowAssign(false); load(); toast('Agent assigned.') }}
          onClose={() => setShowAssign(false)}
        />
      )}

      {/* Remove confirmation */}
      {removeId !== null && (
        <Modal title="Remove Agent" onClose={() => setRemoveId(null)}>
          <div className="flex items-start gap-4 mb-6">
            <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <p className="text-sm text-gray-300 mt-1">
              Remove this agent from <span className="font-semibold text-white">{queue.name}</span>? They will stop receiving calls from this queue.
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setRemoveId(null)} className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">Cancel</button>
            <button onClick={() => handleRemove(removeId)} className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors text-sm font-medium">Remove</button>
          </div>
        </Modal>
      )}

      {/* Edit queue settings sub-modal */}
      {showEdit && (
        <QueueModal
          initial={queue}
          onSave={() => { setShowEdit(false); onQueueUpdated(); toast('Queue settings updated.') }}
          onClose={() => setShowEdit(false)}
        />
      )}
    </>
  )
}

/* ═══ Tier Row — inline level/position editing ══════════════ */
function TierRow({ tier, onRemove, onUpdated }: {
  tier: any; onRemove: () => void; onUpdated: () => void
}) {
  const [editing,  setEditing]  = useState(false)
  const [level,    setLevel]    = useState(tier.level)
  const [position, setPosition] = useState(tier.position)
  const [busy,     setBusy]     = useState(false)

  const save = async () => {
    setBusy(true)
    try {
      await api.patch(`/callcenter/tiers/${tier.id}/`, { level, position })
      setEditing(false); onUpdated()
    } catch (e) { console.error(e) } finally { setBusy(false) }
  }

  const cancel = () => { setEditing(false); setLevel(tier.level); setPosition(tier.position) }

  return (
    <tr className="hover:bg-white/[0.02] transition-colors">
      {/* Agent name */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center text-xs font-bold text-green-400 flex-shrink-0">
            {tier.agent_name?.[0]?.toUpperCase() ?? '?'}
          </div>
          <span className="text-sm text-white font-medium">{tier.agent_name}</span>
        </div>
      </td>

      {/* Extension */}
      <td className="px-4 py-3">
        {tier.agent_extension ? (
          <span className="text-xs font-mono text-gray-400 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
            {tier.agent_extension}
          </span>
        ) : (
          <span className="text-xs text-gray-600">—</span>
        )}
      </td>

      {/* Level */}
      <td className="px-4 py-3">
        {editing ? (
          <select value={level} onChange={e => setLevel(Number(e.target.value))}
            className="bg-[#1F2937] border border-gray-600 rounded-lg text-white text-sm px-2 py-1 w-16 focus:outline-none focus:ring-1 focus:ring-blue-500">
            {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        ) : (
          <span className="text-sm text-gray-300">{tier.level}</span>
        )}
      </td>

      {/* Position */}
      <td className="px-4 py-3">
        {editing ? (
          <select value={position} onChange={e => setPosition(Number(e.target.value))}
            className="bg-[#1F2937] border border-gray-600 rounded-lg text-white text-sm px-2 py-1 w-16 focus:outline-none focus:ring-1 focus:ring-blue-500">
            {[1,2,3,4,5,6,7,8,9,10].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        ) : (
          <span className="text-sm text-gray-300">{tier.position}</span>
        )}
      </td>

      {/* Actions */}
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-1">
          {editing ? (
            <>
              <button onClick={save} disabled={busy}
                className="px-2.5 py-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 text-white text-xs rounded-lg transition-colors">
                {busy ? '…' : 'Save'}
              </button>
              <button onClick={cancel}
                className="px-2.5 py-1 border border-gray-700 text-gray-400 hover:text-white text-xs rounded-lg transition-colors">
                Cancel
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setEditing(true)} title="Edit level/position"
                className="p-1.5 text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors">
                <Pencil className="w-3.5 h-3.5" />
              </button>
              <button onClick={onRemove} title="Remove from queue"
                className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                <UserMinus className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  )
}

/* ═══ Assign Agent Modal ════════════════════════════════════ */
function AssignAgentModal({ queueId, availableAgents, onSave, onClose }: {
  queueId: number; availableAgents: any[]; onSave: () => void; onClose: () => void
}) {
  const [form, setForm] = useState({ agent: String(availableAgents[0]?.id ?? ''), level: 1, position: 1 })
  const [busy, setBusy] = useState(false)
  const [err,  setErr]  = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.agent) return
    setBusy(true); setErr('')
    try {
      await api.post('/callcenter/tiers/', { queue: queueId, agent: Number(form.agent), level: form.level, position: form.position })
      onSave()
    } catch (e: any) {
      const d = e?.response?.data
      setErr(typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Failed to assign agent.')
    } finally { setBusy(false) }
  }

  const set = (p: Partial<typeof form>) => setForm(f => ({ ...f, ...p }))

  return (
    <Modal title="Assign Agent to Queue" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {err && <p className="text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-3 py-2">{err}</p>}

        <div>
          <label className={lbl}>Agent <span className="text-red-400">*</span></label>
          <select value={form.agent} onChange={e => set({ agent: e.target.value })} className={inp} required>
            <option value="">Select agent…</option>
            {availableAgents.map(a => (
              <option key={a.id} value={a.id}>
                {a.name}{a.sip_extension ? ` (ext. ${a.sip_extension})` : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={lbl}>Tier Level</label>
            <select value={form.level} onChange={e => set({ level: Number(e.target.value) })} className={inp}>
              {[1,2,3,4,5].map(n => <option key={n} value={n}>Level {n}</option>)}
            </select>
            <p className="text-xs text-gray-600 mt-1.5">1 = highest priority</p>
          </div>
          <div>
            <label className={lbl}>Position</label>
            <select value={form.position} onChange={e => set({ position: Number(e.target.value) })} className={inp}>
              {[1,2,3,4,5,6,7,8,9,10].map(n => <option key={n} value={n}>Position {n}</option>)}
            </select>
            <p className="text-xs text-gray-600 mt-1.5">Within same tier</p>
          </div>
        </div>

        <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-xl">
          <p className="text-xs text-blue-300">
            <strong>Level</strong> determines priority between tiers — Level 1 agents are tried first.{' '}
            <strong>Position</strong> controls order within the same level.
          </p>
        </div>

        <ModalFooter onClose={onClose} busy={busy} label="Assign Agent" />
      </form>
    </Modal>
  )
}

/* ═══ Queue Stats Panel ══════════════════════════════════════ */
function QueueStatsPanel({ queue }: { queue: any }) {
  const [stats,   setStats]   = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/callcenter/queues/${queue.id}/stats/`)
      .then(({ data }) => setStats(data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [queue.id])

  if (loading) {
    return (
      <div className="py-8 flex items-center justify-center gap-2 text-gray-500">
        <RefreshCw className="w-4 h-4 animate-spin" /> Loading stats…
      </div>
    )
  }

  const items = [
    { label: 'Strategy',             value: strategyLabel(queue.strategy)                     },
    { label: 'Ring Delay',           value: `${queue.ring_progressively_delay ?? 10}s`        },
    { label: 'Max Wait Time',        value: queue.max_wait_time ? `${queue.max_wait_time}s` : 'Unlimited' },
    { label: 'Max Wait (no agents)', value: queue.max_wait_time_with_no_agent ? `${queue.max_wait_time_with_no_agent}s` : 'Unlimited' },
    { label: 'Discard Abandoned',    value: `${queue.discard_abandoned_after ?? 60}s`         },
    { label: 'Time Base Score',      value: `${queue.time_base_score ?? 0}s`                  },
    { label: 'Tier Rules',           value: queue.tier_rules_apply ? 'Enabled' : 'Disabled'  },
    { label: '⚡ Waiting Calls',      value: stats?.waiting_calls ?? queue.waiting_calls ?? 0 },
    { label: '⚡ Active Agents',      value: stats?.active_agents ?? queue.agent_count   ?? 0 },
  ]

  return (
    <div className="grid grid-cols-2 gap-3">
      {items.map(item => (
        <div key={item.label} className="bg-gray-800/40 border border-gray-700 rounded-xl p-3">
          <div className="text-xs text-gray-500 mb-1">{item.label}</div>
          <div className="text-sm font-semibold text-white">{item.value}</div>
        </div>
      ))}
    </div>
  )
}

/* ═══ Delete Confirmation Modal ══════════════════════════════ */
function DeleteModal({ name, onConfirm, onCancel }: { name: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <Modal title="Delete Queue" onClose={onCancel}>
      <div className="flex items-start gap-4 mb-6">
        <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>
        <p className="text-sm text-gray-300 mt-1">
          Delete queue <span className="font-semibold text-white">"{name}"</span>? All agent assignments will be removed. This cannot be undone.
        </p>
      </div>
      <div className="flex gap-3">
        <button onClick={onCancel}  className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">Cancel</button>
        <button onClick={onConfirm} className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors text-sm font-medium">Delete Queue</button>
      </div>
    </Modal>
  )
}

/* ═══ Stat Card ══════════════════════════════════════════════ */
function StatCard({ label, value, icon, accent }: {
  label: string; value: string | number; icon: React.ReactNode; accent: string
}) {
  const borders: Record<string, string> = {
    blue: 'border-blue-500/20', green: 'border-green-500/20',
    yellow: 'border-yellow-500/20', purple: 'border-purple-500/20',
  }
  return (
    <div className={`bg-[#111827] border ${borders[accent] ?? 'border-gray-800'} rounded-2xl p-5`}>
      <div className="p-2 bg-gray-800/80 rounded-lg w-fit mb-3">{icon}</div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}

/* ═══════════════ MAIN PAGE ══════════════════════════════════ */
export function QueuesPage() {
  const [queues,      setQueues]     = useState<any[]>([])
  const [loading,     setLoading]    = useState(true)
  const [search,      setSearch]     = useState('')
  const [showCreate,  setShowCreate] = useState(false)
  const [manageQueue, setManageQueue] = useState<any>(null)
  const [deleteQueue, setDeleteQueue] = useState<any>(null)
  const [toastMsg,    setToastMsg]   = useState('')

  const toast = (msg: string) => { setToastMsg(msg); setTimeout(() => setToastMsg(''), 3000) }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/callcenter/queues/')
      setQueues(data.results ?? data)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async () => {
    if (!deleteQueue) return
    try {
      await api.delete(`/callcenter/queues/${deleteQueue.id}/`)
      setDeleteQueue(null); load(); toast(`Queue "${deleteQueue.name}" deleted.`)
    } catch (e) { console.error(e) }
  }

  const filtered = queues.filter(q =>
    `${q.name} ${q.description ?? ''}`.toLowerCase().includes(search.toLowerCase())
  )

  const totalAgents  = queues.reduce((s, q) => s + (q.agent_count   ?? 0), 0)
  const totalWaiting = queues.reduce((s, q) => s + (q.waiting_calls ?? 0), 0)
  const totalActive  = queues.reduce((s, q) => s + (q.active_calls  ?? 0), 0)

  return (
    <div className="p-8">
      {/* Toast */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 bg-green-500 text-white text-sm font-medium px-4 py-2.5 rounded-xl shadow-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {toastMsg}
        </div>
      )}

      {/* Modals */}
      {showCreate && (
        <QueueModal
          onSave={() => { setShowCreate(false); load(); toast('Queue created.') }}
          onClose={() => setShowCreate(false)}
        />
      )}
      {deleteQueue && (
        <DeleteModal name={deleteQueue.name} onConfirm={handleDelete} onCancel={() => setDeleteQueue(null)} />
      )}
      {manageQueue && (
        <ManageQueueModal
          queue={manageQueue}
          onClose={() => setManageQueue(null)}
          onQueueUpdated={load}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Call Center Queues</h1>
          <p className="text-gray-400 text-sm">Manage queues, routing strategies, and agent assignments</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-colors shadow-lg shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" /> New Queue
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Queues"    value={queues.length} icon={<ListOrdered  className="w-5 h-5 text-blue-400"   />} accent="blue"   />
        <StatCard label="Assigned Agents" value={totalAgents}   icon={<Users        className="w-5 h-5 text-green-400"  />} accent="green"  />
        <StatCard label="Waiting Calls"   value={totalWaiting}  icon={<PhoneIncoming className="w-5 h-5 text-yellow-400" />} accent="yellow" />
        <StatCard label="Active Calls"    value={totalActive}   icon={<Phone        className="w-5 h-5 text-purple-400" />} accent="purple" />
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <ListOrdered className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          <input
            type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search queues…"
            className="w-full pl-9 pr-4 py-2 bg-[#111827] border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>
        <button onClick={load} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Table */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="py-16 flex items-center justify-center gap-3 text-gray-500">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span className="text-sm">Loading queues…</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center">
            <ListOrdered className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm mb-1">
              {search ? 'No queues match your search.' : 'No queues yet.'}
            </p>
            {!search && (
              <button onClick={() => setShowCreate(true)}
                className="mt-3 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-xl transition-colors">
                Create your first queue
              </button>
            )}
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-[#0D1117] border-b border-gray-800">
              <tr>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Queue</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Strategy</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Agents</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Waiting</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Active</th>
                <th className="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filtered.map(queue => (
                <QueueRow
                  key={queue.id}
                  queue={queue}
                  onManage={() => setManageQueue(queue)}
                  onDelete={() => setDeleteQueue(queue)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {!loading && (
        <p className="mt-3 text-xs text-gray-600">
          Showing {filtered.length} of {queues.length} queue{queues.length !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  )
}

/* ═══ Queue Table Row ════════════════════════════════════════ */
function QueueRow({ queue, onManage, onDelete }: {
  queue: any; onManage: () => void; onDelete: () => void
}) {
  const hasWaiting = (queue.waiting_calls ?? 0) > 0
  const hasActive  = (queue.active_calls  ?? 0) > 0

  return (
    <tr className="hover:bg-white/[0.02] transition-colors">
      {/* Queue name */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
            <ListOrdered className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">{queue.name}</div>
            {queue.description && (
              <div className="text-xs text-gray-500 mt-0.5 max-w-xs truncate">{queue.description}</div>
            )}
          </div>
        </div>
      </td>

      {/* Strategy */}
      <td className="px-6 py-4">
        <span className="text-xs font-medium text-gray-300 bg-gray-800 px-2.5 py-1 rounded-lg border border-gray-700">
          {strategyLabel(queue.strategy)}
        </span>
      </td>

      {/* Agents */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-1.5">
          <Users className={`w-4 h-4 ${queue.agent_count > 0 ? 'text-green-400' : 'text-gray-600'}`} />
          <span className={`text-sm font-medium ${queue.agent_count > 0 ? 'text-green-400' : 'text-gray-500'}`}>
            {queue.agent_count ?? 0}
          </span>
        </div>
      </td>

      {/* Waiting */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-1.5">
          <PhoneIncoming className={`w-4 h-4 ${hasWaiting ? 'text-yellow-400' : 'text-gray-600'}`} />
          <span className={`text-sm font-medium ${hasWaiting ? 'text-yellow-400 animate-pulse' : 'text-gray-500'}`}>
            {queue.waiting_calls ?? 0}
          </span>
        </div>
      </td>

      {/* Active */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-1.5">
          <Activity className={`w-4 h-4 ${hasActive ? 'text-purple-400' : 'text-gray-600'}`} />
          <span className={`text-sm font-medium ${hasActive ? 'text-purple-400' : 'text-gray-500'}`}>
            {queue.active_calls ?? 0}
          </span>
        </div>
      </td>

      {/* Actions */}
      <td className="px-6 py-4 text-right">
        <div className="flex items-center justify-end gap-2">
          <button onClick={onManage}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-medium rounded-lg border border-blue-500/20 transition-colors">
            <Settings className="w-3.5 h-3.5" /> Manage
          </button>
          <button onClick={onDelete} title="Delete queue"
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}
