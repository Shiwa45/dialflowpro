import { useEffect, useState } from 'react'
import { Calendar, Download, Filter } from 'lucide-react'
import api from '@/api/client'

export function ReportsPage() {
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  })
  const [cdrs, setCdrs] = useState([])
  const [stats, setStats] = useState({
    totalCalls: 0,
    answeredCalls: 0,
    missedCalls: 0,
    avgDuration: 0,
    totalDuration: 0,
  })

  useEffect(() => {
    fetchReports()
  }, [dateRange])

  const fetchReports = async () => {
    try {
      const { data } = await api.get(`/dialer-cdr/calls/?start_date=${dateRange.start}&end_date=${dateRange.end}`)
      const calls = data.results || data
      setCdrs(calls)

      // Calculate stats
      const answered = calls.filter((c: any) => c.disposition === 'ANSWERED')
      const totalDur = calls.reduce((sum: number, c: any) => sum + (c.duration || 0), 0)
      
      setStats({
        totalCalls: calls.length,
        answeredCalls: answered.length,
        missedCalls: calls.length - answered.length,
        avgDuration: calls.length > 0 ? Math.floor(totalDur / calls.length) : 0,
        totalDuration: totalDur,
      })
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    }
  }

  const formatDuration = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Reports & Analytics</h1>
          <p className="text-gray-400">Call detail records and performance metrics</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg">
          <Download className="w-5 h-5" />
          Export CSV
        </button>
      </div>

      {/* Date Range Filter */}
      <div className="bg-[#111827] border border-gray-800 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-400" />
            <span className="text-sm text-gray-400">Date Range:</span>
          </div>
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
            className="px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-gray-500">to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
            className="px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg">
            <Filter className="w-5 h-5 inline mr-2" />
            More Filters
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <StatCard label="Total Calls" value={stats.totalCalls} color="blue" />
        <StatCard label="Answered" value={stats.answeredCalls} color="green" />
        <StatCard label="Missed" value={stats.missedCalls} color="red" />
        <StatCard label="Avg Duration" value={formatDuration(stats.avgDuration)} color="purple" />
        <StatCard label="Total Duration" value={formatDuration(stats.totalDuration)} color="orange" />
      </div>

      {/* Chart Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-[#111827] border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Call Volume by Hour</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            Chart: Call distribution throughout the day
            <br />
            (Install recharts for real charts)
          </div>
        </div>

        <div className="bg-[#111827] border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Answer Rate</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            Chart: Answered vs Missed calls
            <br />
            (Install recharts for real charts)
          </div>
        </div>
      </div>

      {/* CDR Table */}
      <div className="bg-[#111827] border border-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">Call Detail Records</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#1F2937] border-b border-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Date/Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Caller</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Called</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Campaign</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Disposition</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {cdrs.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No call records found</td></tr>
              ) : (
                cdrs.slice(0, 50).map((cdr: any) => (
                  <tr key={cdr.id} className="hover:bg-[#1F2937]">
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {new Date(cdr.starting_date).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-white font-mono">{cdr.callerid || '-'}</td>
                    <td className="px-4 py-3 text-sm text-white font-mono">{cdr.phone_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-400">{cdr.campaign_name || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        cdr.disposition === 'ANSWERED' ? 'bg-green-500/10 text-green-400' :
                        cdr.disposition === 'BUSY' ? 'bg-yellow-500/10 text-yellow-400' :
                        'bg-gray-500/10 text-gray-400'
                      }`}>
                        {cdr.disposition}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {cdr.duration ? formatDuration(cdr.duration) : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: any) {
  const colors = {
    blue: 'bg-blue-500/10 text-blue-400',
    green: 'bg-green-500/10 text-green-400',
    red: 'bg-red-500/10 text-red-400',
    purple: 'bg-purple-500/10 text-purple-400',
    orange: 'bg-orange-500/10 text-orange-400',
  }

  return (
    <div className="bg-[#111827] border border-gray-800 rounded-lg p-4">
      <div className="text-sm text-gray-400 mb-2">{label}</div>
      <div className={`text-2xl font-bold ${colors[color as keyof typeof colors]}`}>{value}</div>
    </div>
  )
}
