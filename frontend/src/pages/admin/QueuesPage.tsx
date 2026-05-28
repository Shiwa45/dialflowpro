import { useEffect, useState } from 'react'
import { Plus, Users, Phone } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '@/api/client'

export function QueuesPage() {
  const navigate = useNavigate()
  const [queues, setQueues] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)

  useEffect(() => {
    fetchQueues()
  }, [])

  const fetchQueues = async () => {
    try {
      const { data } = await api.get('/callcenter/queues/')
      setQueues(data.results || data)
    } catch (error) {
      console.error('Failed to fetch queues:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Call Center Queues</h1>
          <p className="text-gray-400">Manage call routing and distribution</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
        >
          <Plus className="w-5 h-5" />
          New Queue
        </button>
      </div>

      {/* Queue Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-3 text-center py-12 text-gray-500">Loading queues...</div>
        ) : queues.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-gray-500">No queues found</div>
        ) : (
          queues.map((queue: any) => (
            <QueueCard key={queue.id} queue={queue} />
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <CreateQueueModal onClose={() => setShowCreate(false)} onSuccess={fetchQueues} />
      )}
    </div>
  )
}

function QueueCard({ queue }: any) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">{queue.name}</h3>
          <p className="text-sm text-gray-400">{queue.strategy_display}</p>
        </div>
        <div className="p-2 bg-blue-500/10 rounded-lg">
          <Phone className="w-5 h-5 text-blue-400" />
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Active Agents</span>
          <span className="text-sm font-medium text-white">{queue.agent_count || 0}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Waiting Calls</span>
          <span className="text-sm font-medium text-white">{queue.waiting_calls || 0}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Active Calls</span>
          <span className="text-sm font-medium text-white">{queue.active_calls || 0}</span>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-800 flex items-center gap-2">
        <button className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors">
          Edit
        </button>
        <button className="flex-1 px-3 py-2 border border-gray-700 hover:bg-gray-800 text-gray-300 text-sm rounded transition-colors">
          View
        </button>
      </div>
    </div>
  )
}

function CreateQueueModal({ onClose, onSuccess }: any) {
  const [formData, setFormData] = useState({
    name: '',
    strategy: 1,
    description: '',
  })

  const strategies = [
    { value: 1, label: 'Ring All' },
    { value: 2, label: 'Longest Idle Agent' },
    { value: 3, label: 'Round Robin' },
    { value: 4, label: 'Top Down' },
    { value: 5, label: 'Agent with Least Talk Time' },
    { value: 6, label: 'Agent with Fewest Calls' },
    { value: 7, label: 'Sequentially by Agent Order' },
    { value: 8, label: 'Random' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/callcenter/queues/', formData)
      onSuccess()
      onClose()
    } catch (error) {
      console.error('Failed to create queue:', error)
      alert('Failed to create queue')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#111827] border border-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold text-white mb-4">Create Queue</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Queue Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Strategy *</label>
            <select
              value={formData.strategy}
              onChange={(e) => setFormData({ ...formData, strategy: Number(e.target.value) })}
              className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {strategies.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg">
              Create Queue
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
