import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Plus, Play, Pause, Square, Eye, Pencil, Trash2, RotateCcw,
  Phone, Clock, Search, RefreshCw, AlertTriangle,
  CheckCircle, TrendingUp, Users,
} from 'lucide-react'
import api from '@/api/client'

const STATUS_CONFIG: Record<number, { label: string; className: string; dotColor: string; pulse: boolean }> = {
  1: { label: 'Paused',  className: 'bg-yellow-400/10 text-yellow-400 border border-yellow-400/20', dotColor: 'bg-yellow-400', pulse: false },
  2: { label: 'Aborted', className: 'bg-red-400/10 text-red-400 border border-red-400/20',         dotColor: 'bg-red-400',    pulse: false },
  3: { label: 'Running', className: 'bg-green-400/10 text-green-400 border border-green-400/20',   dotColor: 'bg-green-400',  pulse: true  },
  4: { label: 'Ended',   className: 'bg-gray-500/10 text-gray-400 border border-gray-700',         dotColor: 'bg-gray-400',   pulse: false },
  5: { label: 'Pending', className: 'bg-blue-400/10 text-blue-400 border border-blue-400/20',      dotColor: 'bg-blue-400',   pulse: false },
}

function StatusBadge({ status }: { status: number }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG[5]
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.className}`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dotColor} ${cfg.pulse ? 'animate-pulse' : ''}`} />
      {cfg.label}
    </span>
  )
}

function DeleteModal({ campaign, onConfirm, onCancel }: { campaign: any; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#0D1117] border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 flex items-center justify-center rounded-full bg-red-500/10 border border-red-500/20 flex-shrink-0">
            <AlertTriangle className="w-6 h-6 text-red-400" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Delete Campaign</h3>
            <p className="text-xs text-gray-500 mt-0.5">This action cannot be undone</p>
          </div>
        </div>
        <p className="text-sm text-gray-300 mb-6">
          Are you sure you want to delete{' '}
          <span className="font-semibold text-white">"{campaign.name}"</span>?{' '}
          All subscribers and associated data will be permanently removed.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm font-medium"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors text-sm font-medium shadow-lg shadow-red-500/20"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

export function CampaignsPage() {
  const navigate = useNavigate()
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<any>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  const fetchCampaigns = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true)
    else setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter
      const { data } = await api.get('/dialer-campaign/campaigns/', { params })
      setCampaigns(data.results || data)
    } catch (err) {
      console.error('Failed to fetch campaigns:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [statusFilter])

  useEffect(() => { fetchCampaigns() }, [fetchCampaigns])

  const handleAction = async (id: number, action: 'start' | 'pause' | 'stop' | 'reset') => {
    setActionLoading(id)
    try {
      const { data } = await api.post(`/dialer-campaign/campaigns/${id}/${action}/`)
      if (action === 'reset') {
        alert(`Campaign reset — ${data.pending_now} contact(s) ready to dial again.`)
      }
      await fetchCampaigns(true)
    } catch (err) {
      console.error(`Failed to ${action}:`, err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleteLoading(true)
    try {
      await api.delete(`/dialer-campaign/campaigns/${deleteTarget.id}/`)
      setDeleteTarget(null)
      await fetchCampaigns(true)
    } catch (err) {
      console.error('Failed to delete:', err)
    } finally {
      setDeleteLoading(false)
    }
  }

  const filtered = campaigns.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    (c.campaign_code ?? '').toLowerCase().includes(search.toLowerCase())
  )

  const stats = {
    total:   campaigns.length,
    running: campaigns.filter((c) => c.status === 3).length,
    paused:  campaigns.filter((c) => c.status === 1).length,
    pending: campaigns.filter((c) => c.status === 5).length,
  }

  return (
    <div className="p-8">
      {deleteTarget && (
        <DeleteModal
          campaign={deleteTarget}
          onConfirm={handleDelete}
          onCancel={() => !deleteLoading && setDeleteTarget(null)}
        />
      )}

      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Campaigns</h1>
          <p className="text-gray-400 text-sm">Manage and monitor your voice broadcast campaigns</p>
        </div>
        <button
          onClick={() => navigate('/campaigns/create')}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-colors shadow-lg shadow-blue-500/25"
        >
          <Plus className="w-4 h-4" />
          New Campaign
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Campaigns" value={stats.total}   icon={<Phone      className="w-5 h-5 text-blue-400"   />} accent="blue"   />
        <StatCard label="Running"         value={stats.running} icon={<Play       className="w-5 h-5 text-green-400"  />} accent="green"  />
        <StatCard label="Paused"          value={stats.paused}  icon={<Pause      className="w-5 h-5 text-yellow-400" />} accent="yellow" />
        <StatCard label="Pending"         value={stats.pending} icon={<Clock      className="w-5 h-5 text-purple-400" />} accent="purple" />
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by name or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#111827] border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 bg-[#111827] border border-gray-700 rounded-xl text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer"
        >
          <option value="">All Status</option>
          <option value="3">Running</option>
          <option value="1">Paused</option>
          <option value="5">Pending</option>
          <option value="4">Ended</option>
          <option value="2">Aborted</option>
        </select>

        <button
          onClick={() => fetchCampaigns(true)}
          disabled={refreshing}
          title="Refresh"
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Table */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="py-16 flex items-center justify-center gap-3 text-gray-500">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span className="text-sm">Loading campaigns...</span>
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState hasFilter={!!(search || statusFilter)} onCreate={() => navigate('/campaigns/create')} />
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800 bg-[#0D1117]">
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Campaign</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Schedule</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Progress</th>
                <th className="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filtered.map((c) => (
                <CampaignRow
                  key={c.id}
                  campaign={c}
                  busy={actionLoading === c.id}
                  onStart={() => handleAction(c.id, 'start')}
                  onPause={() => handleAction(c.id, 'pause')}
                  onStop={() => handleAction(c.id, 'stop')}
                  onReset={() => handleAction(c.id, 'reset')}
                  onView={() => navigate(`/campaigns/${c.id}`)}
                  onEdit={() => navigate(`/campaigns/${c.id}/edit`)}
                  onDelete={() => setDeleteTarget(c)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {!loading && (
        <p className="mt-3 text-xs text-gray-600">
          Showing {filtered.length} of {campaigns.length} campaign{campaigns.length !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  )
}

/* ─── Sub-components ─────────────────────────────────────────────── */

function CampaignRow({
  campaign, busy,
  onStart, onPause, onStop, onReset, onView, onEdit, onDelete,
}: {
  campaign: any; busy: boolean
  onStart: () => void; onPause: () => void; onStop: () => void; onReset: () => void
  onView: () => void; onEdit: () => void; onDelete: () => void
}) {
  const isRunning = campaign.status === 3
  const isEnded   = campaign.status === 4 || campaign.status === 2
  const total      = campaign.totalcontact ?? 0
  const done       = campaign.completed ?? 0
  const pct        = total > 0 ? Math.round((done / total) * 100) : 0
  const start      = campaign.startingdate   ? new Date(campaign.startingdate).toLocaleDateString()   : '—'
  const end        = campaign.expirationdate ? new Date(campaign.expirationdate).toLocaleDateString() : '—'

  return (
    <tr className="hover:bg-white/[0.02] transition-colors">
      {/* Name + code */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
            <Phone className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <button
              onClick={onView}
              className="text-sm font-semibold text-white hover:text-blue-400 transition-colors text-left leading-tight"
            >
              {campaign.name}
            </button>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-600 font-mono">{campaign.campaign_code}</span>
              {campaign.dial_mode_display && (
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${
                  campaign.dial_mode === 1 ? 'text-blue-400 bg-blue-500/10 border-blue-500/20' :
                  campaign.dial_mode === 2 ? 'text-purple-400 bg-purple-500/10 border-purple-500/20' :
                  campaign.dial_mode === 3 ? 'text-green-400 bg-green-500/10 border-green-500/20' :
                  'text-gray-400 bg-gray-700/50 border-gray-700'
                }`}>
                  {campaign.dial_mode_display}
                </span>
              )}
              {campaign.queue_name && (
                <span className="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded border border-gray-700">
                  {campaign.queue_name}
                </span>
              )}
            </div>
          </div>
        </div>
      </td>

      {/* Status */}
      <td className="px-6 py-4"><StatusBadge status={campaign.status} /></td>

      {/* Schedule */}
      <td className="px-6 py-4">
        <div className="text-xs leading-relaxed">
          <div className="text-gray-300">{start}</div>
          <div className="text-gray-600">↳ {end}</div>
        </div>
      </td>

      {/* Progress */}
      <td className="px-6 py-4">
        <div className="w-32">
          <div className="flex justify-between mb-1.5">
            <span className="text-xs text-gray-500">{done} / {total}</span>
            <span className="text-xs font-semibold text-gray-300">{pct}%</span>
          </div>
          <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${pct}%`,
                background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
              }}
            />
          </div>
        </div>
      </td>

      {/* Actions */}
      <td className="px-6 py-4">
        <div className="flex items-center justify-end gap-1">
          {/* Play/Pause/Stop cluster */}
          {isRunning && (
            <>
              <IconBtn title="Pause"  onClick={onPause} disabled={busy} cls="text-yellow-400 hover:bg-yellow-400/10"><Pause  className="w-4 h-4" /></IconBtn>
              <IconBtn title="Stop"   onClick={onStop}  disabled={busy} cls="text-red-400   hover:bg-red-400/10"   ><Square className="w-4 h-4" /></IconBtn>
            </>
          )}
          {!isRunning && !isEnded && (
            <IconBtn title="Start" onClick={onStart} disabled={busy} cls="text-green-400 hover:bg-green-400/10"><Play className="w-4 h-4" /></IconBtn>
          )}
          <IconBtn title="Reset & re-dial (mark all contacts pending again)" onClick={onReset} disabled={busy} cls="text-blue-400 hover:bg-blue-400/10"><RotateCcw className="w-4 h-4" /></IconBtn>

          <div className="w-px h-4 bg-gray-700 mx-1" />

          {/* CRUD cluster */}
          <IconBtn title="View details" onClick={onView}   cls="text-gray-400 hover:bg-gray-700/50 hover:text-white">   <Eye    className="w-4 h-4" /></IconBtn>
          <IconBtn title="Edit"         onClick={onEdit}   cls="text-gray-400 hover:bg-blue-500/10  hover:text-blue-400"><Pencil className="w-4 h-4" /></IconBtn>
          <IconBtn title="Delete"       onClick={onDelete} cls="text-gray-400 hover:bg-red-500/10   hover:text-red-400"> <Trash2 className="w-4 h-4" /></IconBtn>
        </div>
      </td>
    </tr>
  )
}

function IconBtn({
  children, title, onClick, disabled, cls,
}: {
  children: React.ReactNode; title: string
  onClick: () => void; disabled?: boolean; cls: string
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      disabled={disabled}
      className={`p-1.5 rounded-lg transition-colors disabled:opacity-40 ${cls}`}
    >
      {children}
    </button>
  )
}

function StatCard({
  label, value, icon, accent,
}: {
  label: string; value: number; icon: React.ReactNode
  accent: 'blue' | 'green' | 'yellow' | 'purple'
}) {
  const accentBorder: Record<string, string> = {
    blue:   'border-blue-500/20',
    green:  'border-green-500/20',
    yellow: 'border-yellow-500/20',
    purple: 'border-purple-500/20',
  }
  return (
    <div className={`bg-[#111827] border ${accentBorder[accent]} rounded-2xl p-5`}>
      <div className="flex items-center justify-between mb-3">
        <div className="p-2 bg-gray-800/80 rounded-lg">{icon}</div>
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}

function EmptyState({ hasFilter, onCreate }: { hasFilter: boolean; onCreate: () => void }) {
  return (
    <div className="py-20 text-center">
      <div className="w-16 h-16 bg-gray-800/80 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-gray-700">
        <Phone className="w-8 h-8 text-gray-600" />
      </div>
      <h3 className="text-base font-semibold text-white mb-2">
        {hasFilter ? 'No campaigns match your filter' : 'No campaigns yet'}
      </h3>
      <p className="text-sm text-gray-500 mb-6">
        {hasFilter
          ? 'Try adjusting your search or status filter.'
          : 'Create your first voice campaign to start dialing.'}
      </p>
      {!hasFilter && (
        <button
          onClick={onCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-colors text-sm font-medium shadow-lg shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" />
          Create Campaign
        </button>
      )}
    </div>
  )
}
