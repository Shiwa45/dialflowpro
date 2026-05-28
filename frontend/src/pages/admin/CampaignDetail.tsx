import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft, Play, Pause, Square, Pencil,
  Phone, Calendar, Zap, Users, CheckCircle,
  TrendingUp, Clock, Shield,
} from 'lucide-react'
import api from '@/api/client'

const STATUS_CONFIG: Record<number, { label: string; className: string; dotColor: string; pulse: boolean }> = {
  1: { label: 'Paused',  className: 'bg-yellow-400/10 text-yellow-400 border border-yellow-400/20', dotColor: 'bg-yellow-400', pulse: false },
  2: { label: 'Aborted', className: 'bg-red-400/10 text-red-400 border border-red-400/20',         dotColor: 'bg-red-400',    pulse: false },
  3: { label: 'Running', className: 'bg-green-400/10 text-green-400 border border-green-400/20',   dotColor: 'bg-green-400',  pulse: true  },
  4: { label: 'Ended',   className: 'bg-gray-500/10 text-gray-400 border border-gray-700',         dotColor: 'bg-gray-400',   pulse: false },
  5: { label: 'Pending', className: 'bg-blue-400/10 text-blue-400 border border-blue-400/20',      dotColor: 'bg-blue-400',   pulse: false },
}

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

const SUB_STATUS_COLORS: Record<number, string> = {
  1: 'text-gray-400',
  2: 'text-yellow-400',
  3: 'text-red-400',
  4: 'text-red-400',
  5: 'text-green-400',
  6: 'text-blue-400',
  7: 'text-orange-400',
  8: 'text-green-400',
}

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadCampaign()
  }, [id])

  const loadCampaign = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/dialer-campaign/campaigns/${id}/`)
      setCampaign(data)
    } catch (err) {
      console.error('Failed to load campaign:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (action: 'start' | 'pause' | 'stop') => {
    setActionLoading(true)
    try {
      await api.post(`/dialer-campaign/campaigns/${id}/${action}/`)
      await loadCampaign()
    } catch (err) {
      console.error(`Failed to ${action}:`, err)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-64">
        <div className="flex items-center gap-3 text-gray-500 text-sm">
          <div className="w-5 h-5 border-2 border-gray-600 border-t-blue-500 rounded-full animate-spin" />
          Loading campaign...
        </div>
      </div>
    )
  }

  if (!campaign) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 mb-4">Campaign not found.</p>
        <button onClick={() => navigate('/campaigns')} className="text-blue-400 hover:underline text-sm">
          Back to campaigns
        </button>
      </div>
    )
  }

  const cfg       = STATUS_CONFIG[campaign.status] ?? STATUS_CONFIG[5]
  const isRunning = campaign.status === 3
  const isEnded   = campaign.status === 4 || campaign.status === 2
  const total     = campaign.totalcontact ?? 0
  const done      = campaign.completed ?? 0
  const pct       = total > 0 ? Math.round((done / total) * 100) : 0

  return (
    <div className="p-8 max-w-6xl">
      {/* Back + Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/campaigns')}
          className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Campaigns
        </button>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-white">{campaign.name}</h1>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.className}`}>
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dotColor} ${cfg.pulse ? 'animate-pulse' : ''}`} />
                {cfg.label}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-gray-500 bg-gray-800 px-2 py-0.5 rounded-lg border border-gray-700">
                {campaign.campaign_code}
              </span>
              {campaign.description && (
                <span className="text-sm text-gray-400">{campaign.description}</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => navigate(`/campaigns/${id}/edit`)}
              className="flex items-center gap-2 px-4 py-2 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm"
            >
              <Pencil className="w-4 h-4" />
              Edit
            </button>

            {isRunning && (
              <>
                <button
                  onClick={() => handleAction('pause')}
                  disabled={actionLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 rounded-xl border border-yellow-500/20 transition-colors text-sm disabled:opacity-50"
                >
                  <Pause className="w-4 h-4" />
                  Pause
                </button>
                <button
                  onClick={() => handleAction('stop')}
                  disabled={actionLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl border border-red-500/20 transition-colors text-sm disabled:opacity-50"
                >
                  <Square className="w-4 h-4" />
                  Stop
                </button>
              </>
            )}

            {!isRunning && !isEnded && (
              <button
                onClick={() => handleAction('start')}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-xl transition-colors text-sm shadow-lg shadow-green-500/20 disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                Start Campaign
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MiniStat label="Total Contacts" value={total}           icon={<Users      className="w-5 h-5 text-blue-400"   />} />
        <MiniStat label="Completed"      value={done}            icon={<CheckCircle className="w-5 h-5 text-green-400"  />} />
        <MiniStat label="Frequency"      value={`${campaign.frequency}/min`} icon={<Zap className="w-5 h-5 text-yellow-400" />} />
        <MiniStat label="Progress"       value={`${pct}%`}       icon={<TrendingUp className="w-5 h-5 text-purple-400"  />} />
      </div>

      {/* Progress bar */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 mb-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-semibold text-white">Campaign Progress</span>
          <span className="text-sm text-gray-400">{done} of {total} contacts reached</span>
        </div>
        <div className="h-2.5 bg-gray-700/80 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${pct}%`, background: 'linear-gradient(90deg, #3b82f6, #818cf8)' }}
          />
        </div>
        <div className="mt-2 text-xs text-gray-600">{pct}% complete</div>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-2 gap-5 mb-6">
        {/* Schedule card */}
        <InfoCard
          icon={<Calendar className="w-4 h-4 text-blue-400" />}
          title="Schedule"
        >
          <InfoRow label="Start Date"    value={campaign.startingdate   ? new Date(campaign.startingdate).toLocaleString()   : '—'} />
          <InfoRow label="End Date"      value={campaign.expirationdate ? new Date(campaign.expirationdate).toLocaleString() : '—'} />
          <InfoRow label="Daily Window"  value={`${campaign.daily_start_time ?? '00:00'} – ${campaign.daily_stop_time ?? '23:59'}`} />
          <div>
            <span className="text-xs text-gray-500 block mb-2">Active Days</span>
            <div className="flex gap-1.5 flex-wrap">
              {DAYS.map((d) => (
                <span
                  key={d}
                  className={`px-2 py-0.5 rounded-lg text-xs font-medium border ${
                    campaign[d]
                      ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                      : 'bg-gray-800/50 text-gray-600 border-gray-700'
                  }`}
                >
                  {d.slice(0, 3).toUpperCase()}
                </span>
              ))}
            </div>
          </div>
        </InfoCard>

        {/* Dialing config card */}
        <InfoCard
          icon={<Phone className="w-4 h-4 text-green-400" />}
          title="Dialing Configuration"
        >
          <InfoRow label="Caller ID"      value={campaign.callerid     || '—'} />
          <InfoRow label="Caller Name"    value={campaign.caller_name  || '—'} />
          <InfoRow label="Frequency"      value={`${campaign.frequency} calls/min`} />
          <InfoRow label="Call Timeout"   value={`${campaign.calltimeout}s`} />
          <InfoRow label="Max Retries"    value={String(campaign.maxretry)} />
          <InfoRow label="Retry Interval" value={`${campaign.intervalretry}s`} />
        </InfoCard>
      </div>

      {/* Subscribers table */}
      {campaign.subscribers && campaign.subscribers.length > 0 && (
        <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-white">Subscribers</h3>
              <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
                {campaign.subscribers.length}
              </span>
            </div>
          </div>
          <table className="w-full">
            <thead className="bg-[#0D1117]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Contact</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Attempts</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Attempt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {campaign.subscribers.slice(0, 25).map((sub: any) => (
                <tr key={sub.id} className="hover:bg-white/[0.015] transition-colors">
                  <td className="px-6 py-3 text-sm text-gray-300 font-mono">{sub.duplicate_contact}</td>
                  <td className="px-6 py-3 text-sm">
                    <span className={SUB_STATUS_COLORS[sub.status] ?? 'text-gray-400'}>{sub.status_display}</span>
                  </td>
                  <td className="px-6 py-3 text-sm text-gray-400">{sub.count_attempt}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">
                    {sub.last_attempt ? new Date(sub.last_attempt).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {campaign.subscribers.length > 25 && (
            <div className="px-6 py-3 text-xs text-gray-600 border-t border-gray-800">
              Showing 25 of {campaign.subscribers.length} subscribers
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ─── Sub-components ───────────────────────────────────── */

function MiniStat({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 bg-gray-800 rounded-lg">{icon}</div>
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}

function InfoCard({
  icon, title, children,
}: {
  icon: React.ReactNode; title: string; children: React.ReactNode
}) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gray-800">
        {icon}
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className="text-sm text-gray-200 font-medium">{value}</dd>
    </div>
  )
}
