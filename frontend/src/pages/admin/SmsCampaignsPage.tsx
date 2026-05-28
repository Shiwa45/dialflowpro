import { useEffect, useState } from 'react'
import { Plus, Play, Pause, MessageSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '@/api/client'

export function SmsCampaignsPage() {
  const navigate = useNavigate()
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    try {
      const { data } = await api.get('/sms/campaigns/')
      setCampaigns(data.results || data)
    } catch (error) {
      console.error('Failed to fetch SMS campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async (id: number) => {
    try {
      await api.post(`/sms/campaigns/${id}/start/`)
      fetchCampaigns()
    } catch (error) {
      console.error('Failed to start campaign:', error)
    }
  }

  const handlePause = async (id: number) => {
    try {
      await api.post(`/sms/campaigns/${id}/pause/`)
      fetchCampaigns()
    } catch (error) {
      console.error('Failed to pause campaign:', error)
    }
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">SMS Campaigns</h1>
          <p className="text-gray-400">Manage your SMS marketing campaigns</p>
        </div>
        <button
          onClick={() => navigate('/sms-campaigns/create')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5" />
          New SMS Campaign
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Campaigns" value={campaigns.length} icon={<MessageSquare className="w-5 h-5 text-blue-400" />} />
        <StatCard label="Active" value={campaigns.filter((c: any) => c.status === 2).length} icon={<Play className="w-5 h-5 text-green-400" />} />
        <StatCard label="Total Sent" value={campaigns.reduce((sum: number, c: any) => sum + (c.total_sent || 0), 0).toLocaleString()} icon={<MessageSquare className="w-5 h-5 text-purple-400" />} />
        <StatCard label="Delivered" value={campaigns.reduce((sum: number, c: any) => sum + (c.total_delivered || 0), 0).toLocaleString()} icon={<MessageSquare className="w-5 h-5 text-green-400" />} />
      </div>

      {/* Campaigns Table */}
      <div className="bg-[#111827] border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#1F2937] border-b border-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Campaign</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Gateway</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Sent</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Delivered</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Failed</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {loading ? (
              <tr><td colSpan={7} className="px-6 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : campaigns.length === 0 ? (
              <tr><td colSpan={7} className="px-6 py-8 text-center text-gray-500">No SMS campaigns found</td></tr>
            ) : (
              campaigns.map((campaign: any) => (
                <tr key={campaign.id} className="hover:bg-[#1F2937]">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-white">{campaign.name}</div>
                    <div className="text-xs text-gray-400 mt-1">{campaign.message_text?.substring(0, 50)}...</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">{campaign.gateway_name || '-'}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      campaign.status === 2 ? 'bg-green-500/10 text-green-400' :
                      campaign.status === 3 ? 'bg-yellow-500/10 text-yellow-400' :
                      'bg-gray-500/10 text-gray-400'
                    }`}>
                      {campaign.status === 2 ? 'Running' : campaign.status === 3 ? 'Paused' : 'Stopped'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">{campaign.total_sent || 0}</td>
                  <td className="px-6 py-4 text-sm text-green-400">{campaign.total_delivered || 0}</td>
                  <td className="px-6 py-4 text-sm text-red-400">{campaign.total_failed || 0}</td>
                  <td className="px-6 py-4 text-right">
                    {campaign.status === 2 ? (
                      <button
                        onClick={() => handlePause(campaign.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 text-sm font-medium rounded transition-colors"
                      >
                        <Pause className="w-4 h-4" />
                        Pause
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStart(campaign.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-400 text-sm font-medium rounded transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        Start
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StatCard({ label, value, icon }: any) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-lg p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-gray-800 rounded">{icon}</div>
        <div className="text-sm text-gray-400">{label}</div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}
