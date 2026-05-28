import { useEffect, useState } from 'react'
import { Phone, Users, BarChart2, Activity } from 'lucide-react'
import api from '@/api/client'

export function Dashboard() {
  const [stats, setStats] = useState({
    totalCampaigns: 0,
    activeCampaigns: 0,
    totalCalls: 0,
    activeAgents: 0,
  })

  useEffect(() => {
    // Fetch dashboard stats
    const fetchStats = async () => {
      try {
        const [campaigns, agents] = await Promise.all([
          api.get('/dialer-campaign/campaigns/'),
          api.get('/callcenter/agents/available/'),
        ])

        setStats({
          totalCampaigns: campaigns.data.length,
          activeCampaigns: campaigns.data.filter((c: any) => c.status === 2).length,
          totalCalls: campaigns.data.reduce((sum: number, c: any) => sum + c.total_call, 0),
          activeAgents: agents.data.length,
        })
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      }
    }

    fetchStats()
  }, [])

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-gray-400">Welcome back! Here's your overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={<Phone className="w-6 h-6 text-blue-400" />}
          label="Total Campaigns"
          value={stats.totalCampaigns}
          bgColor="bg-blue-500/10"
          iconColor="text-blue-400"
        />
        <StatCard
          icon={<Activity className="w-6 h-6 text-green-400" />}
          label="Active Campaigns"
          value={stats.activeCampaigns}
          bgColor="bg-green-500/10"
          iconColor="text-green-400"
        />
        <StatCard
          icon={<BarChart2 className="w-6 h-6 text-purple-400" />}
          label="Total Calls"
          value={stats.totalCalls.toLocaleString()}
          bgColor="bg-purple-500/10"
          iconColor="text-purple-400"
        />
        <StatCard
          icon={<Users className="w-6 h-6 text-orange-400" />}
          label="Active Agents"
          value={stats.activeAgents}
          bgColor="bg-orange-500/10"
          iconColor="text-orange-400"
        />
      </div>

      {/* Charts Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#111827] border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Campaign Performance</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            Chart placeholder - Install recharts
          </div>
        </div>

        <div className="bg-[#111827] border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Call Volume</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            Chart placeholder - Install recharts
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  bgColor,
  iconColor,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  bgColor: string
  iconColor: string
}) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 ${bgColor} rounded-lg`}>{icon}</div>
        <div className="flex-1">
          <div className="text-sm text-gray-400 mb-1">{label}</div>
          <div className="text-2xl font-bold text-white">{value}</div>
        </div>
      </div>
    </div>
  )
}
