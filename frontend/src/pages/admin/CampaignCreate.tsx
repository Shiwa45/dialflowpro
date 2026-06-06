import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Save, ArrowLeft, AlertCircle, Zap, Eye, TrendingUp, Phone } from 'lucide-react'
import api from '@/api/client'

const DIAL_MODES = [
  {
    value: 1, label: 'Predictive',
    icon: Zap,
    color: 'text-blue-400 border-blue-500/40 bg-blue-500/10',
    desc: 'System auto-dials contacts and bridges answered calls to the first available agent in the queue.',
  },
  {
    value: 2, label: 'Preview',
    icon: Eye,
    color: 'text-purple-400 border-purple-500/40 bg-purple-500/10',
    desc: 'Agent sees contact info first, then clicks to dial. Good for complex sales or high-value leads.',
  },
  {
    value: 3, label: 'Progressive',
    icon: TrendingUp,
    color: 'text-green-400 border-green-500/40 bg-green-500/10',
    desc: 'One outbound call per available agent — no abandoned calls. Slower than predictive but safer.',
  },
  {
    value: 4, label: 'Manual',
    icon: Phone,
    color: 'text-gray-400 border-gray-600 bg-gray-800/40',
    desc: 'Agents dial numbers themselves from the softphone. Campaign tracks outcomes only.',
  },
]

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const

const DEFAULT_FORM = {
  name: '',
  description: '',
  callerid: '',
  caller_name: '',
  dial_mode: 1,
  queue: '',
  startingdate: '',
  expirationdate: '',
  daily_start_time: '09:00',
  daily_stop_time: '17:00',
  monday: true,
  tuesday: true,
  wednesday: true,
  thursday: true,
  friday: true,
  saturday: false,
  sunday: false,
  frequency: 10,
  lines_per_agent: 1,
  calltimeout: 30,
  callmaxduration: 1800,
  maxretry: 3,
  intervalretry: 300,
  phonebook: [] as string[],
  aleg_gateway: '',
  dnc: '',
  check_dnc: false,
}

function toDatetimeLocal(iso: string) {
  if (!iso) return ''
  return iso.slice(0, 16) // "2024-01-15T09:00"
}

export function CampaignCreate() {
  const { id } = useParams<{ id?: string }>()
  const isEdit = !!id
  const navigate = useNavigate()

  const [loading, setLoading] = useState(false)
  const [fetchLoading, setFetchLoading] = useState(isEdit)
  const [error, setError] = useState<string | null>(null)
  const [phonebooks, setPhonebooks] = useState<any[]>([])
  const [gateways, setGateways] = useState<any[]>([])
  const [dncLists, setDncLists] = useState<any[]>([])
  const [queues, setQueues] = useState<any[]>([])
  const [phonebookError, setPhonebookError] = useState(false)
  const [formData, setFormData] = useState({ ...DEFAULT_FORM })

  useEffect(() => {
    fetchOptions()
    if (isEdit) fetchCampaign()
  }, [id])

  const fetchOptions = async () => {
    // Use allSettled so a failed gateway/DNC endpoint never prevents phonebooks loading
    const [pbResult, gwResult, dncResult, qResult] = await Promise.allSettled([
      api.get('/dialer-contact/phonebooks/'),
      api.get('/dialer-gateway/gateways/'),
      api.get('/dnc/dnc/'),
      api.get('/callcenter/queues/'),
    ])

    if (pbResult.status === 'fulfilled') {
      setPhonebooks(pbResult.value.data.results ?? pbResult.value.data)
      setPhonebookError(false)
    } else {
      console.error('Failed to fetch phonebooks:', pbResult.reason)
      setPhonebookError(true)
    }

    if (gwResult.status === 'fulfilled') {
      setGateways(gwResult.value.data.results ?? gwResult.value.data)
    } else {
      console.error('Failed to fetch gateways:', gwResult.reason)
    }

    if (qResult.status === 'fulfilled') {
      setQueues(qResult.value.data.results ?? qResult.value.data)
    } else {
      console.error('Failed to fetch queues:', qResult.reason)
    }

    if (dncResult.status === 'fulfilled') {
      setDncLists(dncResult.value.data.results ?? dncResult.value.data)
    } else {
      console.error('Failed to fetch DNC lists:', dncResult.reason)
    }
  }

  const fetchCampaign = async () => {
    setFetchLoading(true)
    try {
      const { data } = await api.get(`/dialer-campaign/campaigns/${id}/`)
      setFormData({
        name:               data.name           ?? '',
        description:        data.description    ?? '',
        callerid:           data.callerid        ?? '',
        caller_name:        data.caller_name     ?? '',
        dial_mode:          data.dial_mode       ?? 1,
        queue:              data.queue != null ? String(data.queue) : '',
        startingdate:       toDatetimeLocal(data.startingdate),
        expirationdate:     toDatetimeLocal(data.expirationdate),
        daily_start_time:   data.daily_start_time?.slice(0, 5) ?? '09:00',
        daily_stop_time:    data.daily_stop_time?.slice(0, 5)  ?? '17:00',
        monday:    data.monday    ?? true,
        tuesday:   data.tuesday   ?? true,
        wednesday: data.wednesday ?? true,
        thursday:  data.thursday  ?? true,
        friday:    data.friday    ?? true,
        saturday:  data.saturday  ?? false,
        sunday:    data.sunday    ?? false,
        frequency:        data.frequency        ?? 10,
        lines_per_agent:  data.lines_per_agent   ?? 1,
        calltimeout:      data.calltimeout       ?? 30,
        callmaxduration:  data.callmaxduration   ?? 1800,
        maxretry:         data.maxretry          ?? 3,
        intervalretry:    data.intervalretry     ?? 300,
        phonebook:        (data.phonebook ?? []).map(String),
        aleg_gateway:     data.aleg_gateway != null ? String(data.aleg_gateway) : '',
        dnc:              data.dnc != null ? String(data.dnc) : '',
        check_dnc:        data.check_dnc ?? false,
      })
    } catch (err) {
      setError('Failed to load campaign data.')
      console.error(err)
    } finally {
      setFetchLoading(false)
    }
  }

  const set = (patch: Partial<typeof formData>) => setFormData((f) => ({ ...f, ...patch }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const payload = {
      ...formData,
      dial_mode:    Number(formData.dial_mode),
      queue:        formData.queue        ? Number(formData.queue)        : null,
      phonebook:    formData.phonebook.map(Number),
      aleg_gateway: formData.aleg_gateway ? Number(formData.aleg_gateway) : null,
      dnc:          formData.dnc          ? Number(formData.dnc)          : null,
    }

    try {
      if (isEdit) {
        await api.patch(`/dialer-campaign/campaigns/${id}/`, payload)
      } else {
        await api.post('/dialer-campaign/campaigns/', payload)
      }
      navigate('/campaigns')
    } catch (err: any) {
      const detail = err?.response?.data
      if (typeof detail === 'object') {
        const messages = Object.entries(detail)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' | ')
        setError(messages)
      } else {
        setError(`Failed to ${isEdit ? 'update' : 'create'} campaign. Please check the form and try again.`)
      }
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full px-4 py-2.5 bg-[#1F2937] border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 placeholder-gray-500'
  const labelCls = 'block text-sm font-medium text-gray-300 mb-2'

  if (fetchLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-64">
        <div className="flex items-center gap-3 text-gray-500 text-sm">
          <div className="w-5 h-5 border-2 border-gray-600 border-t-blue-500 rounded-full animate-spin" />
          Loading campaign data...
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(isEdit ? `/campaigns/${id}` : '/campaigns')}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors mb-4"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            {isEdit ? 'Back to Campaign' : 'Back to Campaigns'}
          </button>
          <h1 className="text-3xl font-bold text-white mb-1">
            {isEdit ? 'Edit Campaign' : 'New Campaign'}
          </h1>
          <p className="text-gray-400 text-sm">
            {isEdit ? 'Update the campaign settings below.' : 'Set up a new voice broadcast campaign.'}
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-6">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Basic Info */}
          <Section title="Basic Information">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Campaign Name <Required /></label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => set({ name: e.target.value })}
                  className={inputCls}
                  placeholder="e.g. Summer Outreach 2024"
                  required
                />
              </div>
              <div>
                <label className={labelCls}>Caller ID</label>
                <input
                  type="text"
                  value={formData.callerid}
                  onChange={(e) => set({ callerid: e.target.value })}
                  className={inputCls}
                  placeholder="+15551234567"
                />
              </div>
              <div>
                <label className={labelCls}>Caller Name</label>
                <input
                  type="text"
                  value={formData.caller_name}
                  onChange={(e) => set({ caller_name: e.target.value })}
                  className={inputCls}
                  placeholder="e.g. My Company"
                />
              </div>
              <div className="md:col-span-2">
                <label className={labelCls}>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => set({ description: e.target.value })}
                  rows={2}
                  className={inputCls}
                  placeholder="Optional campaign description..."
                />
              </div>
            </div>
          </Section>

          {/* Dial Mode + Queue */}
          <Section title="Dialing Mode & Agent Routing">
            <p className="text-xs text-gray-500 mb-4">
              Choose how calls are initiated and how answered calls reach your agents.
            </p>

            {/* Mode cards */}
            <div className="grid grid-cols-2 gap-3 mb-5">
              {DIAL_MODES.map((mode) => {
                const Icon = mode.icon
                const active = formData.dial_mode === mode.value
                return (
                  <button
                    key={mode.value}
                    type="button"
                    onClick={() => set({ dial_mode: mode.value, queue: active ? formData.queue : formData.queue })}
                    className={`flex items-start gap-3 p-4 border-2 rounded-xl text-left transition-all ${
                      active
                        ? `${mode.color} border-opacity-100`
                        : 'border-gray-700 bg-[#1F2937] hover:border-gray-600'
                    }`}
                  >
                    <div className={`mt-0.5 flex-shrink-0 p-1.5 rounded-lg ${active ? mode.color : 'text-gray-500 bg-gray-700/60'}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className={`text-sm font-semibold mb-0.5 ${active ? 'text-white' : 'text-gray-400'}`}>
                        {mode.label}
                      </div>
                      <div className="text-xs text-gray-500 leading-relaxed">{mode.desc}</div>
                    </div>
                  </button>
                )
              })}
            </div>

            {/* Queue selector — required for Predictive and Progressive */}
            {(formData.dial_mode === 1 || formData.dial_mode === 3) && (
              <div>
                <label className={labelCls}>
                  Agent Queue{' '}
                  <span className="text-red-400">*</span>
                  <span className="ml-2 text-xs text-gray-500 font-normal">
                    Answered calls are routed to agents in this queue
                  </span>
                </label>
                {queues.length === 0 ? (
                  <div className="flex items-center gap-3 px-4 py-3 bg-yellow-500/5 border border-yellow-500/20 rounded-xl text-sm text-yellow-300">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    No queues found. Go to <strong className="mx-1">Call Center → Queues</strong> and create one first.
                  </div>
                ) : (
                  <select
                    value={formData.queue}
                    onChange={(e) => set({ queue: e.target.value })}
                    className={inputCls}
                    required={formData.dial_mode === 1 || formData.dial_mode === 3}
                  >
                    <option value="">Select a queue…</option>
                    {queues.map((q: any) => (
                      <option key={q.id} value={String(q.id)}>
                        {q.name}{q.agent_count != null ? ` (${q.agent_count} agent${q.agent_count !== 1 ? 's' : ''})` : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}
          </Section>

          {/* Schedule */}
          <Section title="Schedule">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className={labelCls}>Start Date & Time <Required /></label>
                <input
                  type="datetime-local"
                  value={formData.startingdate}
                  onChange={(e) => set({ startingdate: e.target.value })}
                  className={inputCls}
                  required
                />
              </div>
              <div>
                <label className={labelCls}>End Date & Time <Required /></label>
                <input
                  type="datetime-local"
                  value={formData.expirationdate}
                  onChange={(e) => set({ expirationdate: e.target.value })}
                  className={inputCls}
                  required
                />
              </div>
              <div>
                <label className={labelCls}>Daily Start Time</label>
                <input
                  type="time"
                  value={formData.daily_start_time}
                  onChange={(e) => set({ daily_start_time: e.target.value })}
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Daily Stop Time</label>
                <input
                  type="time"
                  value={formData.daily_stop_time}
                  onChange={(e) => set({ daily_stop_time: e.target.value })}
                  className={inputCls}
                />
              </div>
            </div>

            <div>
              <label className={labelCls}>Active Days</label>
              <div className="flex gap-2">
                {DAYS.map((day) => (
                  <label
                    key={day}
                    className={`flex-1 flex items-center justify-center py-2 border rounded-xl cursor-pointer select-none transition-colors text-xs font-semibold ${
                      formData[day]
                        ? 'bg-blue-500 border-blue-500 text-white'
                        : 'bg-[#1F2937] border-gray-700 text-gray-500 hover:border-gray-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData[day]}
                      onChange={(e) => set({ [day]: e.target.checked })}
                      className="hidden"
                    />
                    {day.slice(0, 3).toUpperCase()}
                  </label>
                ))}
              </div>
            </div>
          </Section>

          {/* Configuration */}
          <Section title="Dialing Configuration">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Phonebook(s) <Required /></label>
                {phonebookError && (
                  <p className="text-xs text-red-400 mb-1.5 flex items-center gap-1">
                    <span className="w-3 h-3 inline-block rounded-full bg-red-400/20 text-center leading-3">!</span>
                    Failed to load phonebooks — check the console for details.
                  </p>
                )}
                <select
                  multiple
                  value={formData.phonebook}
                  onChange={(e) => set({ phonebook: Array.from(e.target.selectedOptions, (o) => o.value) })}
                  className={`${inputCls} h-28 ${phonebookError ? 'border-red-500/50' : ''}`}
                  required
                >
                  {phonebooks.length === 0
                    ? <option disabled value="">{phonebookError ? 'Failed to load' : 'No phonebooks available'}</option>
                    : phonebooks.map((pb: any) => (
                        <option key={pb.id} value={String(pb.id)}>{pb.name}</option>
                      ))
                  }
                </select>
                <p className="text-xs text-gray-600 mt-1">Hold Ctrl / Cmd to select multiple</p>
              </div>

              <div>
                <label className={labelCls}>Gateway</label>
                <select
                  value={formData.aleg_gateway}
                  onChange={(e) => set({ aleg_gateway: e.target.value })}
                  className={inputCls}
                >
                  <option value="">Select Gateway (optional)</option>
                  {gateways.map((gw: any) => (
                    <option key={gw.id} value={String(gw.id)}>{gw.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelCls}>Frequency (calls/min)</label>
                <input
                  type="number"
                  value={formData.frequency}
                  onChange={(e) => set({ frequency: Number(e.target.value) })}
                  className={inputCls}
                  min="1" max="200"
                />
              </div>

              {(formData.dial_mode === 1 || formData.dial_mode === 3) && (
                <div>
                  <label className={labelCls}>Lines per Agent</label>
                  <input
                    type="number"
                    value={formData.lines_per_agent}
                    onChange={(e) => set({ lines_per_agent: Number(e.target.value) })}
                    className={inputCls}
                    min="1" max="10"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Simultaneous calls dialed per available agent (1 = progressive, 2–3 = predictive over-dial)
                  </p>
                </div>
              )}

              <div>
                <label className={labelCls}>Call Timeout (seconds)</label>
                <input
                  type="number"
                  value={formData.calltimeout}
                  onChange={(e) => set({ calltimeout: Number(e.target.value) })}
                  className={inputCls}
                  min="5"
                />
              </div>

              <div>
                <label className={labelCls}>Max Retries</label>
                <input
                  type="number"
                  value={formData.maxretry}
                  onChange={(e) => set({ maxretry: Number(e.target.value) })}
                  className={inputCls}
                  min="0"
                />
              </div>

              <div>
                <label className={labelCls}>Retry Interval (seconds)</label>
                <input
                  type="number"
                  value={formData.intervalretry}
                  onChange={(e) => set({ intervalretry: Number(e.target.value) })}
                  className={inputCls}
                  min="0"
                />
              </div>
            </div>
          </Section>

          {/* DNC */}
          <Section title="Do-Not-Call (DNC)">
            <label className="flex items-center gap-3 cursor-pointer mb-3">
              <div
                onClick={() => set({ check_dnc: !formData.check_dnc })}
                className={`relative w-10 h-5 rounded-full transition-colors ${formData.check_dnc ? 'bg-blue-500' : 'bg-gray-700'}`}
              >
                <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${formData.check_dnc ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-sm text-gray-300">Enable DNC checking</span>
            </label>

            {formData.check_dnc && (
              <div>
                <label className={labelCls}>DNC List</label>
                <select
                  value={formData.dnc}
                  onChange={(e) => set({ dnc: e.target.value })}
                  className={inputCls}
                >
                  <option value="">Select DNC list</option>
                  {dncLists.map((d: any) => (
                    <option key={d.id} value={String(d.id)}>{d.name}</option>
                  ))}
                </select>
              </div>
            )}
          </Section>

          {/* Submit */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => navigate(isEdit ? `/campaigns/${id}` : '/campaigns')}
              className="px-6 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-colors text-sm font-medium shadow-lg shadow-blue-500/20"
            >
              <Save className="w-4 h-4" />
              {loading
                ? isEdit ? 'Saving...' : 'Creating...'
                : isEdit ? 'Save Changes' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6">
      <h3 className="text-sm font-semibold text-white mb-4 pb-3 border-b border-gray-800">{title}</h3>
      {children}
    </div>
  )
}

function Required() {
  return <span className="text-red-400 ml-0.5">*</span>
}
