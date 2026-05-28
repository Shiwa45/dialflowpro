import { useEffect, useState, useCallback } from 'react'
import {
  Server, Users, Settings as SettingsIcon, FileAudio,
  Plus, Pencil, Trash2, X, AlertTriangle, RefreshCw,
  MessageSquare, Wifi, WifiOff, Eye, EyeOff,
} from 'lucide-react'
import api from '@/api/client'

/* ─── shared styles ─────────────────────────────── */
const inp = 'w-full px-4 py-2.5 bg-[#1F2937] border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 placeholder-gray-500'
const lbl = 'block text-sm font-medium text-gray-300 mb-1.5'

/* ─── generic building blocks ────────────────────── */
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0D1117] border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 sticky top-0 bg-[#0D1117]">
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

function DeleteModal({ label, onConfirm, onCancel }: { label: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <Modal title="Confirm Delete" onClose={onCancel}>
      <div className="flex items-start gap-4 mb-6">
        <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>
        <p className="text-sm text-gray-300 mt-1">
          Delete <span className="font-semibold text-white">"{label}"</span>? This cannot be undone.
        </p>
      </div>
      <div className="flex gap-3">
        <button onClick={onCancel}  className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">Cancel</button>
        <button onClick={onConfirm} className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors text-sm font-medium">Delete</button>
      </div>
    </Modal>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{title}</h4>
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className={lbl}>{label}</label>
      {children}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════ */
/*  VoIP Gateway modal                                    */
/* ═══════════════════════════════════════════════════════ */
const GW_STATUS = [{ value: 1, label: 'Active' }, { value: 2, label: 'Inactive' }]

const GW_DEFAULT = {
  name: '', gateways: '', description: '',
  // SIP connection (needed for auto-sync to FreeSWITCH)
  sip_host: '', sip_port: 5060 as number,
  register: false, sip_username: '', sip_password: '',
  caller_id_in_from: true,
  // dial config
  addprefix: '', removeprefix: '',
  gateway_codecs: '', gateway_timeouts: '', gateway_retries: '',
  originate_dial_string: '', addparameter: '',
  maximum_call: '', status: 1,
}
type GwForm = typeof GW_DEFAULT

function GatewayModal({ initial, onSave, onClose }: { initial?: any; onSave: () => void; onClose: () => void }) {
  const [form, setForm] = useState<GwForm>(initial ? {
    ...GW_DEFAULT,
    ...initial,
    maximum_call: initial.maximum_call ?? '',
  } : { ...GW_DEFAULT })
  const [busy, setBusy] = useState(false)
  const [err,  setErr]  = useState('')

  const set = (p: Partial<typeof form>) => setForm(f => ({ ...f, ...p }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr('')
    const payload = {
      ...form,
      maximum_call: form.maximum_call !== '' ? Number(form.maximum_call) : null,
    }
    try {
      if (initial) {
        await api.patch(`/dialer-gateway/gateways/${initial.id}/`, payload)
      } else {
        await api.post('/dialer-gateway/gateways/', payload)
      }
      onSave()
    } catch (e: any) {
      const d = e?.response?.data
      setErr(typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Failed to save gateway.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={initial ? 'Edit Gateway' : 'Add VoIP Gateway'} onClose={onClose}>
      <form onSubmit={submit}>
        {err && <p className="text-sm text-red-400 mb-4">{err}</p>}

        {/* ── SIP Connection (the most important section) ── */}
        <Section title="SIP Connection  ⚡ Required for FreeSWITCH sync">
          <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-3 mb-3 text-xs text-blue-300">
            Fill in the SIP host so DialFlow can auto-generate the FreeSWITCH XML and reload sofia.
            For an OpenVox / GSM gateway on your LAN, set <span className="font-mono bg-blue-500/10 px-1 rounded">register = OFF</span>.
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <Field label="SIP Host / IP *">
                <input
                  value={form.sip_host}
                  onChange={e => set({ sip_host: e.target.value })}
                  className={inp}
                  placeholder="192.168.1.113"
                  required
                />
              </Field>
            </div>
            <div>
              <Field label="SIP Port">
                <input
                  type="number"
                  value={form.sip_port}
                  onChange={e => set({ sip_port: Number(e.target.value) })}
                  className={inp}
                  placeholder="5060"
                  min="1" max="65535"
                />
              </Field>
            </div>
          </div>

          <div className="flex items-center gap-6 mt-1">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <div
                onClick={() => set({ register: !form.register })}
                className={`relative w-9 h-5 rounded-full transition-colors ${form.register ? 'bg-blue-500' : 'bg-gray-700'}`}
              >
                <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.register ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-sm text-gray-300">Register with gateway</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <div
                onClick={() => set({ caller_id_in_from: !form.caller_id_in_from })}
                className={`relative w-9 h-5 rounded-full transition-colors ${form.caller_id_in_from ? 'bg-blue-500' : 'bg-gray-700'}`}
              >
                <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.caller_id_in_from ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-sm text-gray-300">Caller-ID in From header</span>
            </label>
          </div>

          {form.register && (
            <div className="grid grid-cols-2 gap-3 mt-2">
              <Field label="SIP Username">
                <input value={form.sip_username} onChange={e => set({ sip_username: e.target.value })} className={inp} placeholder="myuser" />
              </Field>
              <Field label="SIP Password">
                <input type="password" value={form.sip_password} onChange={e => set({ sip_password: e.target.value })} className={inp} placeholder="secret" />
              </Field>
            </div>
          )}
        </Section>

        <Section title="Basic Info">
          <Field label="Gateway Name *">
            <input value={form.name} onChange={e => set({ name: e.target.value })} className={inp} placeholder="e.g. openvox-gsm" required />
          </Field>
          <Field label="Dial String">
            <input
              value={form.gateways}
              onChange={e => set({ gateways: e.target.value })}
              className={inp}
              placeholder={form.name ? `sofia/gateway/${form.name}/` : 'sofia/gateway/openvox-gsm/'}
            />
            <p className="text-xs text-gray-600 mt-1">Auto-filled from name if left blank</p>
          </Field>
          <Field label="Description">
            <textarea value={form.description} onChange={e => set({ description: e.target.value })} rows={2} className={inp} placeholder="e.g. OpenVox B800 32-port GSM" />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Status">
              <select value={form.status} onChange={e => set({ status: Number(e.target.value) })} className={inp}>
                {GW_STATUS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </Field>
            <Field label="Max Concurrent Calls">
              <input type="number" value={form.maximum_call} onChange={e => set({ maximum_call: e.target.value })} className={inp} placeholder="Unlimited" min="0" />
            </Field>
          </div>
        </Section>

        <Section title="Number Manipulation">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Add Prefix">
              <input value={form.addprefix} onChange={e => set({ addprefix: e.target.value })} className={inp} placeholder="e.g. 1" />
            </Field>
            <Field label="Remove Prefix">
              <input value={form.removeprefix} onChange={e => set({ removeprefix: e.target.value })} className={inp} placeholder="e.g. 0" />
            </Field>
          </div>
        </Section>

        <Section title="FreeSWITCH Advanced">
          <Field label="Codecs">
            <input value={form.gateway_codecs} onChange={e => set({ gateway_codecs: e.target.value })} className={inp} placeholder="PCMA,PCMU" />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Timeout (s)">
              <input value={form.gateway_timeouts} onChange={e => set({ gateway_timeouts: e.target.value })} className={inp} placeholder="10" />
            </Field>
            <Field label="Retries">
              <input value={form.gateway_retries} onChange={e => set({ gateway_retries: e.target.value })} className={inp} placeholder="2,1" />
            </Field>
          </div>
          <Field label="Originate Dial String">
            <input value={form.originate_dial_string} onChange={e => set({ originate_dial_string: e.target.value })} className={inp} placeholder="channel variables…" />
          </Field>
        </Section>

        <ModalFooter onClose={onClose} busy={busy} label={initial ? 'Save Changes' : 'Add Gateway'} />
      </form>
    </Modal>
  )
}

/* ═══════════════════════════════════════════════════════ */
/*  SMS Gateway modal                                     */
/* ═══════════════════════════════════════════════════════ */
const SMS_TYPES = [
  { value: 1, label: 'Twilio' },
  { value: 2, label: 'Plivo' },
  { value: 3, label: 'Clickatell' },
  { value: 4, label: 'Nexmo / Vonage' },
  { value: 99, label: 'Custom HTTP' },
]

const SMS_DEFAULT = {
  name: '', gateway_type: 1 as number,
  account_sid: '', auth_token: '', api_key: '', base_url: '',
  from_number: '', from_name: '', is_active: true,
}
type SmsForm = typeof SMS_DEFAULT

function SmsGatewayModal({ initial, onSave, onClose }: { initial?: any; onSave: () => void; onClose: () => void }) {
  const [form, setForm] = useState<SmsForm>(initial ? { ...SMS_DEFAULT, ...initial } : { ...SMS_DEFAULT })
  const [busy, setBusy]   = useState(false)
  const [err,  setErr]    = useState('')
  const [showToken, setShowToken] = useState(false)

  const set = (p: Partial<typeof form>) => setForm(f => ({ ...f, ...p }))
  const isCustom = form.gateway_type === 99

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      if (initial) {
        await api.patch(`/sms/gateways/${initial.id}/`, form)
      } else {
        await api.post('/sms/gateways/', form)
      }
      onSave()
    } catch (e: any) {
      const d = e?.response?.data
      setErr(typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Failed to save SMS gateway.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={initial ? 'Edit SMS Gateway' : 'Add SMS Gateway'} onClose={onClose}>
      <form onSubmit={submit}>
        {err && <p className="text-sm text-red-400 mb-4">{err}</p>}

        <Section title="Basic Info">
          <Field label="Gateway Name *">
            <input value={form.name} onChange={e => set({ name: e.target.value })} className={inp} placeholder="e.g. Twilio Main" required />
          </Field>
          <Field label="Provider *">
            <select value={form.gateway_type} onChange={e => set({ gateway_type: Number(e.target.value) })} className={inp}>
              {SMS_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </Field>
          <label className="flex items-center gap-3 cursor-pointer">
            <div
              onClick={() => set({ is_active: !form.is_active })}
              className={`relative w-10 h-5 rounded-full transition-colors ${form.is_active ? 'bg-blue-500' : 'bg-gray-700'}`}
            >
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.is_active ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </div>
            <span className="text-sm text-gray-300">Active</span>
          </label>
        </Section>

        <Section title="Credentials">
          {!isCustom && (
            <Field label="Account SID">
              <input value={form.account_sid} onChange={e => set({ account_sid: e.target.value })} className={inp} placeholder="AC…" />
            </Field>
          )}
          <Field label={isCustom ? 'API Key' : 'Auth Token'}>
            <div className="relative">
              <input
                type={showToken ? 'text' : 'password'}
                value={isCustom ? form.api_key : form.auth_token}
                onChange={e => set(isCustom ? { api_key: e.target.value } : { auth_token: e.target.value })}
                className={`${inp} pr-10`}
                placeholder={isCustom ? 'API key…' : 'Auth token…'}
              />
              <button
                type="button"
                onClick={() => setShowToken(s => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </Field>
          {isCustom && (
            <Field label="Base URL *">
              <input type="url" value={form.base_url} onChange={e => set({ base_url: e.target.value })} className={inp} placeholder="https://api.example.com/" />
            </Field>
          )}
        </Section>

        <Section title="Sender Identity">
          <div className="grid grid-cols-2 gap-3">
            <Field label="From Number">
              <input value={form.from_number} onChange={e => set({ from_number: e.target.value })} className={inp} placeholder="+15551234567" />
            </Field>
            <Field label="Sender Name">
              <input value={form.from_name} onChange={e => set({ from_name: e.target.value })} className={inp} placeholder="MyCompany" maxLength={15} />
              <p className="text-xs text-gray-600 mt-1">Max 11 chars for alphanumeric</p>
            </Field>
          </div>
        </Section>

        <ModalFooter onClose={onClose} busy={busy} label={initial ? 'Save Changes' : 'Add SMS Gateway'} />
      </form>
    </Modal>
  )
}

/* ═══════════════════════════════════════════════════════ */
/*  Gateways tab                                          */
/* ═══════════════════════════════════════════════════════ */
function GatewaysTab() {
  const [gateways,   setGateways]  = useState<any[]>([])
  const [smsGws,     setSmsGws]    = useState<any[]>([])
  const [loading,    setLoading]   = useState(true)
  const [gwModal,    setGwModal]   = useState<'create' | 'edit' | null>(null)
  const [smsModal,   setSmsModal]  = useState<'create' | 'edit' | null>(null)
  const [editGw,     setEditGw]    = useState<any>(null)
  const [editSms,    setEditSms]   = useState<any>(null)
  const [deleteGw,   setDeleteGw]  = useState<any>(null)
  const [deleteSms,  setDeleteSms] = useState<any>(null)
  // sync: id → 'syncing' | 'ok' | 'error:<msg>'
  const [syncState,  setSyncState] = useState<Record<number, string>>({})
  const [syncAllBusy, setSyncAllBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    const [gwRes, smsRes] = await Promise.allSettled([
      api.get('/dialer-gateway/gateways/'),
      api.get('/sms/gateways/'),
    ])
    if (gwRes.status  === 'fulfilled') setGateways(gwRes.value.data.results  ?? gwRes.value.data)
    if (smsRes.status === 'fulfilled') setSmsGws(smsRes.value.data.results   ?? smsRes.value.data)
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const handleDeleteGw = async () => {
    if (!deleteGw) return
    await api.delete(`/dialer-gateway/gateways/${deleteGw.id}/`)
    setDeleteGw(null); load()
  }

  const handleDeleteSms = async () => {
    if (!deleteSms) return
    await api.delete(`/sms/gateways/${deleteSms.id}/`)
    setDeleteSms(null); load()
  }

  const handleSync = async (gw: any) => {
    setSyncState(s => ({ ...s, [gw.id]: 'syncing' }))
    try {
      const { data } = await api.post(`/dialer-gateway/gateways/${gw.id}/sync/`)
      if (!data.success) {
        setSyncState(s => ({ ...s, [gw.id]: `error:${data.message}` }))
      } else if (data.esl_reloaded) {
        setSyncState(s => ({ ...s, [gw.id]: 'ok' }))
      } else {
        // XML written but ESL couldn't reload — partial success
        setSyncState(s => ({ ...s, [gw.id]: `warn:${data.manual_cmd}` }))
      }
    } catch (e: any) {
      const msg = e?.response?.data?.message ?? 'Sync failed'
      setSyncState(s => ({ ...s, [gw.id]: `error:${msg}` }))
    }
  }

  const handleSyncAll = async () => {
    setSyncAllBusy(true)
    try {
      const { data } = await api.post('/dialer-gateway/gateways/sync_all/')
      const newState: Record<number, string> = {}
      for (const r of data.results ?? []) {
        newState[r.id] = r.success ? 'ok' : `error:${r.message}`
      }
      setSyncState(s => ({ ...s, ...newState }))
    } catch {
      // silent
    } finally {
      setSyncAllBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* ── modals ── */}
      {gwModal && (
        <GatewayModal
          initial={gwModal === 'edit' ? editGw : undefined}
          onSave={() => { setGwModal(null); setEditGw(null); load() }}
          onClose={() => { setGwModal(null); setEditGw(null) }}
        />
      )}
      {smsModal && (
        <SmsGatewayModal
          initial={smsModal === 'edit' ? editSms : undefined}
          onSave={() => { setSmsModal(null); setEditSms(null); load() }}
          onClose={() => { setSmsModal(null); setEditSms(null) }}
        />
      )}
      {deleteGw  && <DeleteModal label={deleteGw.name}  onConfirm={handleDeleteGw}  onCancel={() => setDeleteGw(null)}  />}
      {deleteSms && <DeleteModal label={deleteSms.name} onConfirm={handleDeleteSms} onCancel={() => setDeleteSms(null)} />}

      {/* ── VoIP Gateways ── */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg"><Server className="w-4 h-4 text-blue-400" /></div>
            <div>
              <h3 className="text-sm font-semibold text-white">VoIP / SIP Gateways</h3>
              <p className="text-xs text-gray-500 mt-0.5">FreeSWITCH trunks for outbound calling</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={load} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors" title="Refresh">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleSyncAll}
              disabled={syncAllBusy || gateways.length === 0}
              title="Write all gateway XMLs to FreeSWITCH and rescan"
              className="flex items-center gap-1.5 px-3 py-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 rounded-xl text-sm transition-colors disabled:opacity-40"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncAllBusy ? 'animate-spin' : ''}`} />
              Sync All to FS
            </button>
            <button
              onClick={() => { setEditGw(null); setGwModal('create') }}
              className="flex items-center gap-2 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium transition-colors"
            >
              <Plus className="w-4 h-4" /> Add Gateway
            </button>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-gray-500 text-sm">Loading…</div>
        ) : gateways.length === 0 ? (
          <div className="py-14 text-center">
            <Server className="w-10 h-10 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm mb-4">No VoIP gateways configured</p>
            <button onClick={() => { setEditGw(null); setGwModal('create') }} className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm">
              <Plus className="w-4 h-4" /> Add First Gateway
            </button>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-[#0D1117]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name / SIP Host</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Dial String</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">FS Sync</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {gateways.map((gw: any) => {
                const ss = syncState[gw.id]
                const isSyncing = ss === 'syncing'
                const isOk      = ss === 'ok'
                const errMsg    = ss?.startsWith('error:') ? ss.slice(6) : null
                return (
                  <tr key={gw.id} className="hover:bg-white/[0.02] transition-colors">
                    {/* Name + SIP host */}
                    <td className="px-6 py-3.5">
                      <div className="text-sm font-medium text-white">{gw.name}</div>
                      {gw.sip_host
                        ? <div className="text-xs text-blue-400 font-mono mt-0.5">{gw.sip_host}:{gw.sip_port ?? 5060}</div>
                        : <div className="text-xs text-amber-500 mt-0.5">⚠ SIP host not set — edit to enable sync</div>
                      }
                    </td>

                    {/* Dial string */}
                    <td className="px-6 py-3.5 text-xs text-gray-400 font-mono max-w-[180px] truncate">
                      {gw.fs_dial_string_prefix || gw.gateways}
                    </td>

                    {/* Gateway status */}
                    <td className="px-6 py-3.5">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                        gw.status === 1
                          ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                          : 'bg-gray-500/10 text-gray-400 border border-gray-700'
                      }`}>
                        {gw.status === 1 ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                        {gw.status === 1 ? 'Active' : 'Inactive'}
                      </span>
                    </td>

                    {/* FS Sync status */}
                    {(() => {
                      const warnCmd = ss?.startsWith('warn:') ? ss.slice(5) : null
                      return (
                        <td className="px-6 py-3.5">
                          {isOk && (
                            <span className="inline-flex items-center gap-1 text-xs text-green-400">
                              <span className="w-1.5 h-1.5 rounded-full bg-green-400" /> Synced
                            </span>
                          )}
                          {warnCmd && (
                            <span className="inline-flex flex-col gap-0.5 text-xs text-yellow-400 max-w-[160px]" title={`Run in FS CLI: ${warnCmd}`}>
                              <span className="flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 flex-shrink-0" />
                                XML written
                              </span>
                              <span className="font-mono text-[10px] text-yellow-500 truncate">
                                Run: {warnCmd}
                              </span>
                            </span>
                          )}
                          {errMsg && (
                            <span className="inline-flex items-start gap-1 text-xs text-red-400 max-w-[140px]" title={errMsg}>
                              <span className="w-1.5 h-1.5 rounded-full bg-red-400 flex-shrink-0 mt-0.5" />
                              <span className="truncate">{errMsg}</span>
                            </span>
                          )}
                          {!ss && <span className="text-xs text-gray-600">—</span>}
                        </td>
                      )
                    })()}

                    {/* Actions */}
                    <td className="px-6 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {/* Sync to FreeSWITCH */}
                        <button
                          title={gw.sip_host ? 'Sync to FreeSWITCH' : 'Set SIP host first'}
                          disabled={isSyncing || !gw.sip_host}
                          onClick={() => handleSync(gw)}
                          className="flex items-center gap-1 px-2 py-1.5 text-xs font-medium rounded-lg transition-colors disabled:opacity-40
                            bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20"
                        >
                          <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin' : ''}`} />
                          {isSyncing ? 'Syncing…' : 'Sync FS'}
                        </button>

                        <div className="w-px h-4 bg-gray-700 mx-0.5" />

                        <ActionBtn title="Edit" cls="hover:bg-blue-500/10 hover:text-blue-400" onClick={() => { setEditGw(gw); setGwModal('edit') }}>
                          <Pencil className="w-4 h-4" />
                        </ActionBtn>
                        <ActionBtn title="Delete" cls="hover:bg-red-500/10 hover:text-red-400" onClick={() => setDeleteGw(gw)}>
                          <Trash2 className="w-4 h-4" />
                        </ActionBtn>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* ── SMS Gateways ── */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 rounded-lg"><MessageSquare className="w-4 h-4 text-purple-400" /></div>
            <div>
              <h3 className="text-sm font-semibold text-white">SMS Gateways</h3>
              <p className="text-xs text-gray-500 mt-0.5">Twilio, Plivo, Nexmo, and custom HTTP providers</p>
            </div>
          </div>
          <button
            onClick={() => { setEditSms(null); setSmsModal('create') }}
            className="flex items-center gap-2 px-3 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-xl text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" /> Add SMS Gateway
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-gray-500 text-sm">Loading…</div>
        ) : smsGws.length === 0 ? (
          <div className="py-14 text-center">
            <MessageSquare className="w-10 h-10 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm mb-4">No SMS gateways configured</p>
            <button onClick={() => { setEditSms(null); setSmsModal('create') }} className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-xl text-sm">
              <Plus className="w-4 h-4" /> Add First SMS Gateway
            </button>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-[#0D1117]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Provider</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">From</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {smsGws.map((sg: any) => (
                <tr key={sg.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-3.5 text-sm font-medium text-white">{sg.name}</td>
                  <td className="px-6 py-3.5">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-lg bg-gray-800 text-gray-300 text-xs font-medium border border-gray-700">
                      {sg.gateway_type_display ?? SMS_TYPES.find(t => t.value === sg.gateway_type)?.label ?? '—'}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-sm text-gray-400 font-mono">
                    {sg.from_name || sg.from_number || '—'}
                  </td>
                  <td className="px-6 py-3.5">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                      sg.is_active
                        ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                        : 'bg-gray-500/10 text-gray-400 border border-gray-700'
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${sg.is_active ? 'bg-green-400' : 'bg-gray-500'}`} />
                      {sg.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <ActionBtn title="Edit" cls="hover:bg-blue-500/10 hover:text-blue-400" onClick={() => { setEditSms(sg); setSmsModal('edit') }}>
                        <Pencil className="w-4 h-4" />
                      </ActionBtn>
                      <ActionBtn title="Delete" cls="hover:bg-red-500/10 hover:text-red-400" onClick={() => setDeleteSms(sg)}>
                        <Trash2 className="w-4 h-4" />
                      </ActionBtn>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function ActionBtn({ children, title, onClick, cls }: { children: React.ReactNode; title: string; onClick: () => void; cls: string }) {
  return (
    <button title={title} onClick={onClick} className={`p-1.5 text-gray-400 rounded-lg transition-colors ${cls}`}>
      {children}
    </button>
  )
}

/* ═══════════════════════════════════════════════════════ */
/*  Placeholder tabs                                      */
/* ═══════════════════════════════════════════════════════ */
function UsersTab() {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-sm font-semibold text-white">User Management</h3>
        <button className="flex items-center gap-2 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" /> Add User
        </button>
      </div>
      <p className="text-xs text-gray-500 mb-8">Manage users and role assignments</p>
      <div className="text-center py-8 border border-dashed border-gray-700 rounded-xl text-gray-600 text-sm">
        User management coming soon
      </div>
    </div>
  )
}

function SystemTab() {
  return (
    <div className="space-y-5">
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 pb-3 border-b border-gray-800">General Settings</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={lbl}>Time Zone</label>
            <select className={inp}>
              <option>UTC</option>
              <option>America/New_York</option>
              <option>America/Los_Angeles</option>
              <option>Asia/Kolkata</option>
            </select>
          </div>
          <div>
            <label className={lbl}>Date Format</label>
            <select className={inp}>
              <option>MM/DD/YYYY</option>
              <option>DD/MM/YYYY</option>
              <option>YYYY-MM-DD</option>
            </select>
          </div>
        </div>
      </div>
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 pb-3 border-b border-gray-800">Dialer Defaults</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={lbl}>Default Call Timeout (s)</label>
            <input type="number" defaultValue={30} className={inp} />
          </div>
          <div>
            <label className={lbl}>Max Concurrent Calls</label>
            <input type="number" defaultValue={100} className={inp} />
          </div>
        </div>
      </div>
    </div>
  )
}

function AudioTab() {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-sm font-semibold text-white">Audio Files</h3>
        <button className="flex items-center gap-2 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" /> Upload Audio
        </button>
      </div>
      <p className="text-xs text-gray-500 mb-8">IVR audio and voicemail files (.wav, .mp3)</p>
      <div className="text-center py-8 border border-dashed border-gray-700 rounded-xl text-gray-600 text-sm">
        Audio file library coming soon
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════ */
/*  Main page                                             */
/* ═══════════════════════════════════════════════════════ */
export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('gateways')

  const tabs = [
    { id: 'gateways', label: 'Gateways',    icon: Server       },
    { id: 'users',    label: 'Users',        icon: Users        },
    { id: 'system',   label: 'System',       icon: SettingsIcon },
    { id: 'audio',    label: 'Audio Files',  icon: FileAudio    },
  ]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-1">Settings</h1>
        <p className="text-gray-400 text-sm">Configure gateways, users, and system preferences</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-gray-800">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors text-sm ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'gateways' && <GatewaysTab />}
      {activeTab === 'users'    && <UsersTab />}
      {activeTab === 'system'   && <SystemTab />}
      {activeTab === 'audio'    && <AudioTab />}
    </div>
  )
}
