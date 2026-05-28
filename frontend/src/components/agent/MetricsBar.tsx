import { Users, Clock, PhoneIncoming, Timer, TrendingUp } from 'lucide-react'

export function MetricsBar() {
  return (
    <div className="bg-[#111827] border-b border-gray-800 px-6 py-4">
      <div className="grid grid-cols-5 gap-4">
        <MetricCard
          icon={<Users className="w-5 h-5 text-blue-400" />}
          label="Calls in Queue"
          value="05"
        />
        <MetricCard
          icon={<Clock className="w-5 h-5 text-gray-400" />}
          label="Longest Wait Time"
          value="02:15"
        />
        <MetricCard
          icon={<PhoneIncoming className="w-5 h-5 text-blue-400" />}
          label="Answered Today"
          value="18"
        />
        <MetricCard
          icon={<Timer className="w-5 h-5 text-gray-400" />}
          label="Average Handle Time"
          value="06:42"
        />
        <MetricCard
          icon={<TrendingUp className="w-5 h-5 text-green-500" />}
          label="Service Level"
          value="88%"
          valueColor="text-green-500"
        />
      </div>
    </div>
  )
}

function MetricCard({
  icon,
  label,
  value,
  valueColor = 'text-white',
}: {
  icon: React.ReactNode
  label: string
  value: string
  valueColor?: string
}) {
  return (
    <div className="bg-[#1F2937] border border-gray-700 rounded-lg p-4">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gray-800/50 rounded">
          {icon}
        </div>
        <div className="flex-1">
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
            {label}
          </div>
          <div className={`text-2xl font-bold ${valueColor}`}>
            {value}
          </div>
        </div>
      </div>
    </div>
  )
}
