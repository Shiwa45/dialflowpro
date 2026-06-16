import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bot, Plus, Sparkles, Play, Pause, Trash2, Languages, Cpu, Lock,
} from 'lucide-react'
import { useAIAgents, useAISubscription } from '@/hooks/useAIAgents'
import { AIAgent, AIAgentStatus } from '@/types/aiAgent'

const STATUS_META: Record<number, { label: string; cls: string }> = {
  [AIAgentStatus.DRAFT]: { label: 'Draft', cls: 'bg-gray-500/10 text-gray-400 border-gray-700' },
  [AIAgentStatus.ACTIVE]: { label: 'Active', cls: 'bg-green-500/10 text-green-400 border-green-500/20' },
  [AIAgentStatus.PAUSED]: { label: 'Paused', cls: 'bg-orange-500/10 text-orange-400 border-orange-500/20' },
  [AIAgentStatus.TRAINING]: { label: 'Training', cls: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
}

export function AIAgentsPage() {
  const { sub, loading: subLoading } = useAISubscription()
  const { agents, loading, error, refresh, remove, activate, pause } = useAIAgents()
  const [busy, setBusy] = useState<number | null>(null)

  const act = async (id: number, fn: () => Promise<any>) => {
    setBusy(id)
    try { await fn(); await refresh() } finally { setBusy(null) }
  }

  if (subLoading) return <div className="p-8 text-gray-500 text-sm">Loading…</div>

  if (!sub?.is_active) {
    return (
      <div className="p-8">
        <div className="max-w-lg mx-auto mt-16 bg-[#111827] border border-gray-800 rounded-2xl p-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
            <Lock className="w-7 h-7 text-blue-400" />
          </div>
          <h1 className="text-xl font-bold text-white mb-2">AI Agents requires a subscription</h1>
          <p className="text-gray-400 text-sm mb-6">
            Your tenant doesn't have an active AI agent plan yet. Contact your
            administrator to enable AI voice agents with Indian-language support.
          </p>
          <a href="mailto:sales@yourcompany.com"
             className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm">
            <Sparkles className="w-4 h-4" /> Request access
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1 flex items-center gap-2">
            <Bot className="w-7 h-7 text-blue-400" /> AI Agents
          </h1>
          <p className="text-gray-400">
            Voice agents that answer calls in Hindi & Indian languages
            {typeof sub.minutes_remaining === 'number' &&
              ` · ${sub.minutes_remaining} AI minutes left`}
          </p>
        </div>
        <Link to="/ai-agents/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium">
          <Plus className="w-4 h-4" /> Create AI Agent
        </Link>
      </div>

      {error && (
        <div className="px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">{error}</div>
      )}

      {loading ? (
        <div className="py-16 text-center text-gray-500 text-sm">Loading agents…</div>
      ) : agents.length === 0 ? (
        <div className="py-20 text-center">
          <Bot className="w-12 h-12 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500 text-sm mb-5">No AI agents yet</p>
          <Link to="/ai-agents/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm">
            <Plus className="w-4 h-4" /> Create your first agent
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {agents.map((a: AIAgent) => {
            const meta = STATUS_META[a.status]
            return (
              <div key={a.id} className="bg-[#111827] border border-gray-800 rounded-2xl p-5 flex flex-col">
                <div className="flex items-start justify-between mb-3">
                  <Link to={`/ai-agents/${a.id}`} className="group">
                    <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">{a.name}</h3>
                    <p className="text-xs text-gray-500">
                      {a.persona_name} · <span className="font-mono text-gray-400">ID {a.id}</span>
                    </p>
                  </Link>
                  <span className={`text-xs px-2 py-1 rounded-full border ${meta.cls}`}>{meta.label}</span>
                </div>
                <p className="text-sm text-gray-400 line-clamp-2 mb-4 flex-1">{a.description || 'No description'}</p>

                <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-4">
                  <span className="inline-flex items-center gap-1"><Languages className="w-3.5 h-3.5" />{a.primary_language}</span>
                  <span className="inline-flex items-center gap-1"><Cpu className="w-3.5 h-3.5" />{a.active_llm_model}</span>
                  <span className="inline-flex items-center gap-1"><Sparkles className="w-3.5 h-3.5" />{a.knowledge_count} KB items</span>
                </div>

                <div className="flex items-center gap-2 pt-3 border-t border-gray-800/60">
                  {a.status === AIAgentStatus.ACTIVE ? (
                    <button onClick={() => act(a.id, () => pause(a.id))} disabled={busy === a.id}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 text-sm text-orange-400 bg-orange-500/10 hover:bg-orange-500/20 rounded-lg disabled:opacity-40">
                      <Pause className="w-3.5 h-3.5" /> Pause
                    </button>
                  ) : (
                    <button onClick={() => act(a.id, () => activate(a.id))} disabled={busy === a.id}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 text-sm text-green-400 bg-green-500/10 hover:bg-green-500/20 rounded-lg disabled:opacity-40">
                      <Play className="w-3.5 h-3.5" /> Activate
                    </button>
                  )}
                  <Link to={`/ai-agents/${a.id}`}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 text-sm text-gray-300 bg-[#1F2937] hover:bg-gray-700 rounded-lg">
                    Configure
                  </Link>
                  <button onClick={() => { if (confirm(`Delete "${a.name}"?`)) act(a.id, () => remove(a.id)) }}
                    className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
