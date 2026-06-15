import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Save, ArrowLeft, Cpu, Mic2, GitBranch, BookOpen, Eye, Sparkles, Plus, Trash2, X,
} from 'lucide-react'
import api from '@/api/client'
import { useAIAgents, useKnowledge } from '@/hooks/useAIAgents'
import {
  AIAgent, LANGUAGES, V3_SPEAKERS, SARVAM_MODELS, GEMINI_MODELS, AIKnowledgeItem,
} from '@/types/aiAgent'

const inp = 'w-full bg-[#0D1117] border border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-100 focus:border-blue-500 outline-none'
const lbl = 'block text-xs font-medium text-gray-400 mb-1.5'

const DEFAULTS: Partial<AIAgent> = {
  name: '', description: '', persona_name: 'Assistant',
  call_direction: 'outbound',
  greeting: 'Namaste! Main aapki kaise madad kar sakta hoon?',
  system_prompt: '', temperature: 0.6, max_response_tokens: 300,
  llm_provider: 'sarvam', sarvam_llm_model: 'sarvam-30b',
  gemini_model: 'gemini-2.0-flash', enable_thinking: false,
  primary_language: 'hi-IN', auto_detect_language: true,
  stt_model: 'saaras:v3', stt_mode: 'transcribe',
  tts_model: 'bulbul:v3', tts_speaker: 'manan', tts_pace: 1.0, tts_temperature: 0.6,
  allow_human_transfer: true, allow_callback: true,
  confidence_transfer_threshold: 0.4, max_call_duration_seconds: 600,
}

type Tab = 'brain' | 'voice' | 'escalation' | 'knowledge'

export function AIAgentBuilder() {
  const { id } = useParams()
  const isNew = id === 'new' || !id
  const nav = useNavigate()
  const { create, update, train, previewPrompt } = useAIAgents()
  const [form, setForm] = useState<Partial<AIAgent>>(DEFAULTS)
  const [tab, setTab] = useState<Tab>('brain')
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState('')
  const [preview, setPreview] = useState<string | null>(null)
  const [queues, setQueues] = useState<any[]>([])

  const set = (patch: Partial<AIAgent>) => setForm(f => ({ ...f, ...patch }))

  useEffect(() => {
    api.get('/callcenter/queues/').then(({ data }) => setQueues(data.results ?? data)).catch(() => {})
    if (!isNew) {
      api.get(`/ai/agents/${id}/`).then(({ data }) => setForm(data)).catch(() => setErr('Failed to load'))
    }
  }, [id, isNew])

  const save = async () => {
    setSaving(true); setErr('')
    try {
      if (isNew) {
        const created = await create(form)
        nav(`/ai-agents/${created.id}`, { replace: true })
      } else {
        const updated = await update(Number(id), form)
        setForm(updated)
      }
    } catch (e: any) {
      const d = e?.response?.data
      setErr(typeof d === 'object' ? Object.entries(d).map(([k, v]) => `${k}: ${v}`).join(' · ') : 'Save failed')
    } finally { setSaving(false) }
  }

  const doPreview = async () => {
    if (isNew) return
    try { setPreview(await previewPrompt(Number(id))) } catch { setErr('Preview failed') }
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'brain', label: 'Brain', icon: Cpu },
    { key: 'voice', label: 'Voice', icon: Mic2 },
    { key: 'escalation', label: 'Escalation', icon: GitBranch },
    { key: 'knowledge', label: 'Knowledge', icon: BookOpen },
  ]

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => nav('/ai-agents')} className="p-2 text-gray-400 hover:text-white hover:bg-[#1F2937] rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">{isNew ? 'Create AI Agent' : form.name}</h1>
            <p className="text-sm text-gray-500">{isNew ? 'Configure a new voice agent' : `${form.status_display} · ${form.knowledge_count ?? 0} knowledge items`}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isNew && (
            <button onClick={doPreview} className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-gray-300 bg-[#1F2937] hover:bg-gray-700 rounded-xl">
              <Eye className="w-4 h-4" /> Preview prompt
            </button>
          )}
          <button onClick={save} disabled={saving || !form.name}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-xl disabled:opacity-40">
            <Save className="w-4 h-4" /> {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      {err && <div className="px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">{err}</div>}

      {/* basic fields */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>Agent Name *</label>
          <input className={inp} value={form.name || ''} onChange={e => set({ name: e.target.value })} placeholder="Sales Assistant" />
        </div>
        <div>
          <label className={lbl}>Persona Name (introduces itself as)</label>
          <input className={inp} value={form.persona_name || ''} onChange={e => set({ persona_name: e.target.value })} placeholder="Priya" />
        </div>
        <div className="col-span-2">
          <label className={lbl}>Description</label>
          <input className={inp} value={form.description || ''} onChange={e => set({ description: e.target.value })} placeholder="Handles product enquiries for…" />
        </div>
        <div className="col-span-2">
          <label className={lbl}>Role / Call Direction</label>
          <select className={inp} value={form.call_direction || 'outbound'}
            onChange={e => set({ call_direction: e.target.value as 'inbound' | 'outbound' })}>
            <option value="outbound">Outbound — sales executive who CALLS customers and pitches</option>
            <option value="inbound">Inbound — assistant who ANSWERS customer calls</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Outbound agents lead the conversation: introduce, pitch from the knowledge base, handle objections, close or schedule a callback.
          </p>
        </div>
      </div>

      {/* tabs */}
      <div className="flex gap-1 bg-[#111827] border border-gray-800 rounded-xl p-1 w-fit">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm transition-colors ${
              tab === t.key ? 'bg-blue-500 text-white' : 'text-gray-400 hover:text-white'}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6">
        {tab === 'brain' && <BrainTab form={form} set={set} />}
        {tab === 'voice' && <VoiceTab form={form} set={set} />}
        {tab === 'escalation' && <EscalationTab form={form} set={set} queues={queues} />}
        {tab === 'knowledge' && (
          isNew ? <p className="text-sm text-gray-500">Save the agent first, then add knowledge.</p>
            : <KnowledgeTab agentId={Number(id)} onTrained={() => train(Number(id))} />
        )}
      </div>

      {preview !== null && (
        <PreviewModal text={preview} onClose={() => setPreview(null)} />
      )}
    </div>
  )
}

function BrainTab({ form, set }: any) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>LLM Provider (the "brain")</label>
          <select className={inp} value={form.llm_provider} onChange={e => set({ llm_provider: e.target.value })}>
            <option value="sarvam">Sarvam (Indic-native)</option>
            <option value="gemini">Google Gemini</option>
          </select>
        </div>
        <div>
          <label className={lbl}>Model</label>
          {form.llm_provider === 'gemini' ? (
            <select className={inp} value={form.gemini_model} onChange={e => set({ gemini_model: e.target.value })}>
              {GEMINI_MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          ) : (
            <select className={inp} value={form.sarvam_llm_model} onChange={e => set({ sarvam_llm_model: e.target.value })}>
              {SARVAM_MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          )}
        </div>
      </div>
      <div>
        <label className={lbl}>Greeting (first words spoken)</label>
        <textarea className={inp} rows={2} value={form.greeting || ''} onChange={e => set({ greeting: e.target.value })} />
      </div>
      <div>
        <label className={lbl}>System Prompt (knowledge base is appended automatically)</label>
        <textarea className={inp} rows={5} value={form.system_prompt || ''} onChange={e => set({ system_prompt: e.target.value })}
          placeholder="You are a polite sales assistant for ACME Electronics…" />
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className={lbl}>Temperature ({form.temperature})</label>
          <input type="range" min={0} max={2} step={0.1} value={form.temperature}
            onChange={e => set({ temperature: Number(e.target.value) })} className="w-full" />
        </div>
        <div>
          <label className={lbl}>Max response tokens</label>
          <input type="number" className={inp} value={form.max_response_tokens} onChange={e => set({ max_response_tokens: Number(e.target.value) })} />
        </div>
        <label className="flex items-center gap-2 mt-6 text-sm text-gray-300">
          <input type="checkbox" checked={form.enable_thinking} onChange={e => set({ enable_thinking: e.target.checked })} />
          Enable thinking mode
        </label>
      </div>
    </div>
  )
}

function VoiceTab({ form, set }: any) {
  const speakers = form.tts_model === 'bulbul:v3' ? V3_SPEAKERS : { Male: ['abhilash', 'karun', 'hitesh'], Female: ['anushka', 'manisha', 'vidya', 'arya'] }
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>Primary Language</label>
          <select className={inp} value={form.primary_language} onChange={e => set({ primary_language: e.target.value })}>
            {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
        </div>
        <label className="flex items-center gap-2 mt-6 text-sm text-gray-300">
          <input type="checkbox" checked={form.auto_detect_language} onChange={e => set({ auto_detect_language: e.target.checked })} />
          Auto-detect caller language (code-mix supported)
        </label>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>STT Model</label>
          <select className={inp} value={form.stt_model} onChange={e => set({ stt_model: e.target.value })}>
            <option value="saaras:v3">Saaras v3 (recommended)</option>
            <option value="saarika:v2.5">Saarika v2.5 (legacy)</option>
          </select>
        </div>
        <div>
          <label className={lbl}>STT Mode</label>
          <select className={inp} value={form.stt_mode} onChange={e => set({ stt_mode: e.target.value })}>
            <option value="transcribe">Transcribe (same language)</option>
            <option value="translate">Translate to English</option>
            <option value="codemix">Code-mixed</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>TTS Model</label>
          <select className={inp} value={form.tts_model} onChange={e => set({ tts_model: e.target.value })}>
            <option value="bulbul:v3">Bulbul v3 (recommended)</option>
            <option value="bulbul:v2">Bulbul v2 (legacy)</option>
          </select>
        </div>
        <div>
          <label className={lbl}>Speaker Voice</label>
          <select className={inp} value={form.tts_speaker} onChange={e => set({ tts_speaker: e.target.value })}>
            {Object.entries(speakers).map(([group, names]) => (
              <optgroup key={group} label={group}>
                {(names as string[]).map(n => <option key={n} value={n}>{n}</option>)}
              </optgroup>
            ))}
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>Pace ({form.tts_pace})</label>
          <input type="range" min={0.5} max={2} step={0.1} value={form.tts_pace}
            onChange={e => set({ tts_pace: Number(e.target.value) })} className="w-full" />
        </div>
        {form.tts_model === 'bulbul:v3' && (
          <div>
            <label className={lbl}>Voice expressiveness ({form.tts_temperature})</label>
            <input type="range" min={0.01} max={2} step={0.05} value={form.tts_temperature}
              onChange={e => set({ tts_temperature: Number(e.target.value) })} className="w-full" />
          </div>
        )}
      </div>
    </div>
  )
}

function EscalationTab({ form, set, queues }: any) {
  return (
    <div className="space-y-4">
      <label className="flex items-center gap-2 text-sm text-gray-300">
        <input type="checkbox" checked={form.allow_human_transfer} onChange={e => set({ allow_human_transfer: e.target.checked })} />
        Allow transfer to a human agent
      </label>
      {form.allow_human_transfer && (
        <div>
          <label className={lbl}>Transfer to queue</label>
          <select className={inp} value={form.transfer_queue || ''} onChange={e => set({ transfer_queue: e.target.value ? Number(e.target.value) : null })}>
            <option value="">— Select queue —</option>
            {queues.map((q: any) => <option key={q.id} value={q.id}>{q.name}</option>)}
          </select>
        </div>
      )}
      <label className="flex items-center gap-2 text-sm text-gray-300">
        <input type="checkbox" checked={form.allow_callback} onChange={e => set({ allow_callback: e.target.checked })} />
        Offer callback when no human is available
      </label>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>Transfer if confidence below ({form.confidence_transfer_threshold})</label>
          <input type="range" min={0} max={1} step={0.05} value={form.confidence_transfer_threshold}
            onChange={e => set({ confidence_transfer_threshold: Number(e.target.value) })} className="w-full" />
        </div>
        <div>
          <label className={lbl}>Max call duration (seconds)</label>
          <input type="number" className={inp} value={form.max_call_duration_seconds} onChange={e => set({ max_call_duration_seconds: Number(e.target.value) })} />
        </div>
      </div>
    </div>
  )
}

function KnowledgeTab({ agentId, onTrained }: { agentId: number; onTrained: () => void }) {
  const { items, loading, refresh, add, remove } = useKnowledge(agentId)
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState<Partial<AIKnowledgeItem>>({ source_type: 'product', title: '', content: '', product_name: '', product_price: '' })
  const [training, setTraining] = useState(false)

  const submit = async () => {
    await add(draft)
    setDraft({ source_type: 'product', title: '', content: '', product_name: '', product_price: '' })
    setAdding(false)
    await refresh()
  }
  const reindex = async () => { setTraining(true); try { await onTrained(); await refresh() } finally { setTraining(false) } }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">Add product details, FAQs and notes. The AI uses these to answer callers.</p>
        <div className="flex gap-2">
          <button onClick={reindex} disabled={training}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 rounded-xl disabled:opacity-40">
            <Sparkles className="w-4 h-4" /> {training ? 'Indexing…' : 'Train / Re-index'}
          </button>
          <button onClick={() => setAdding(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm bg-[#1F2937] hover:bg-gray-700 text-gray-200 rounded-xl">
            <Plus className="w-4 h-4" /> Add item
          </button>
        </div>
      </div>

      {adding && (
        <div className="bg-[#0D1117] border border-gray-700 rounded-xl p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <select className={inp} value={draft.source_type} onChange={e => setDraft(d => ({ ...d, source_type: e.target.value as any }))}>
              <option value="product">Product</option>
              <option value="faq">FAQ</option>
              <option value="freeform">Note</option>
            </select>
            <input className={inp} placeholder="Title" value={draft.title} onChange={e => setDraft(d => ({ ...d, title: e.target.value }))} />
          </div>
          {draft.source_type === 'product' && (
            <div className="grid grid-cols-2 gap-3">
              <input className={inp} placeholder="Product name" value={draft.product_name} onChange={e => setDraft(d => ({ ...d, product_name: e.target.value }))} />
              <input className={inp} placeholder="Price (e.g. ₹4,999)" value={draft.product_price} onChange={e => setDraft(d => ({ ...d, product_price: e.target.value }))} />
            </div>
          )}
          <textarea className={inp} rows={3} placeholder="Details the AI can use to answer…" value={draft.content} onChange={e => setDraft(d => ({ ...d, content: e.target.value }))} />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setAdding(false)} className="px-3 py-1.5 text-sm text-gray-400">Cancel</button>
            <button onClick={submit} disabled={!draft.title || !draft.content} className="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg disabled:opacity-40">Add</button>
          </div>
        </div>
      )}

      {loading ? <p className="text-sm text-gray-500 py-6 text-center">Loading…</p>
        : items.length === 0 ? <p className="text-sm text-gray-600 py-6 text-center">No knowledge items yet</p>
        : (
          <div className="space-y-2">
            {items.map(it => (
              <div key={it.id} className="flex items-start gap-3 bg-[#0D1117] border border-gray-800 rounded-xl p-3">
                <span className="text-[10px] uppercase tracking-wide text-gray-500 bg-[#1F2937] px-2 py-1 rounded mt-0.5">{it.source_type_display}</span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-gray-200">
                    {it.title}{it.product_price && <span className="text-gray-500"> · {it.product_price}</span>}
                  </div>
                  <div className="text-xs text-gray-500 line-clamp-2">{it.content}</div>
                </div>
                <button onClick={async () => { await remove(it.id); await refresh() }} className="p-1.5 text-gray-600 hover:text-red-400">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
    </div>
  )
}

function PreviewModal({ text, onClose }: { text: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-6" onClick={onClose}>
      <div className="bg-[#111827] border border-gray-800 rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <h3 className="font-semibold text-white">Assembled System Prompt</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <pre className="p-4 text-xs text-gray-300 whitespace-pre-wrap overflow-y-auto font-mono">{text}</pre>
      </div>
    </div>
  )
}
