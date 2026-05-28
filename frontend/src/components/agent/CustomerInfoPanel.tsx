import { useState } from 'react'
import { Edit2, Phone, Mail, MapPin, Calendar, MessageSquare } from 'lucide-react'

type Tab = 'info' | 'history' | 'notes'

export function CustomerInfoPanel() {
  const [activeTab, setActiveTab] = useState<Tab>('info')

  const customer = {
    name: 'Neha Kapoor',
    phone: '+91 98765 43210',
    email: 'neha.kapoor@email.com',
    location: 'Bengaluru, Karnataka, India',
    id: 'CUST100245',
    since: '12 Jan 2023',
    lastContact: '06 May 2024',
    totalInteractions: 12,
    preferredChannel: 'Phone, Email',
  }

  const interactions = [
    {
      type: 'call',
      title: 'Outgoing Call',
      subtitle: 'Duration: 04:32',
      date: '06 May 2024',
      tag: 'Sales Inquiry',
    },
    {
      type: 'email',
      title: 'Email',
      subtitle: 'Product Information',
      date: '04 May 2024',
    },
    {
      type: 'chat',
      title: 'Chat',
      subtitle: 'Shipping Query',
      date: '02 May 2024',
    },
  ]

  return (
    <div className="bg-[#111827] border-l border-gray-800 flex flex-col">
      {/* Tabs */}
      <div className="border-b border-gray-800">
        <div className="flex">
          {[
            { id: 'info', label: 'Customer Info' },
            { id: 'history', label: 'History' },
            { id: 'notes', label: 'Notes' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'info' && (
          <div className="space-y-6">
            {/* Customer Header */}
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white text-2xl font-bold">
                NK
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-lg font-semibold text-white">
                    {customer.name}
                  </h3>
                  <button className="p-1 hover:bg-gray-700 rounded">
                    <Edit2 className="w-3.5 h-3.5 text-gray-400" />
                  </button>
                </div>
                <p className="text-sm text-gray-400 mb-2">{customer.phone}</p>
                <p className="text-sm text-gray-400">{customer.email}</p>
              </div>
            </div>

            <div className="h-px bg-gray-800" />

            {/* Customer Details */}
            <div className="space-y-3">
              <DetailRow
                icon={<MapPin className="w-4 h-4" />}
                label="Location"
                value={customer.location}
              />
            </div>

            <div className="h-px bg-gray-800" />

            <h4 className="text-sm font-semibold text-white mb-4">
              Customer Details
            </h4>

            <div className="space-y-3">
              <DetailRow label="Customer ID" value={customer.id} />
              <DetailRow label="Customer Since" value={customer.since} />
              <DetailRow label="Last Contact" value={customer.lastContact} />
              <DetailRow
                label="Total Interactions"
                value={customer.totalInteractions.toString()}
              />
              <DetailRow
                label="Preferred Channel"
                value={customer.preferredChannel}
              />
            </div>

            <button className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors mt-4">
              View More
            </button>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white mb-4">
              Recent Interactions
            </h4>

            {interactions.map((interaction, idx) => (
              <div
                key={idx}
                className="flex gap-3 p-3 bg-[#1F2937] border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
              >
                <div className="mt-1">
                  {interaction.type === 'call' && (
                    <Phone className="w-4 h-4 text-blue-400" />
                  )}
                  {interaction.type === 'email' && (
                    <Mail className="w-4 h-4 text-purple-400" />
                  )}
                  {interaction.type === 'chat' && (
                    <MessageSquare className="w-4 h-4 text-green-400" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-1">
                    <h5 className="text-sm font-medium text-white">
                      {interaction.title}
                    </h5>
                    <span className="text-xs text-gray-500">
                      {interaction.date}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mb-2">
                    {interaction.subtitle}
                  </p>
                  {interaction.tag && (
                    <span className="inline-block px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs rounded">
                      {interaction.tag}
                    </span>
                  )}
                </div>
              </div>
            ))}

            <button className="w-full px-4 py-2 border border-gray-700 text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors">
              View All
            </button>
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="space-y-4">
            <textarea
              placeholder="Add notes about this customer..."
              className="w-full h-40 bg-[#1F2937] border border-gray-700 rounded-lg p-3 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors">
              Save Note
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function DetailRow({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex items-center gap-2 text-sm text-gray-400">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-sm text-white text-right">{value}</div>
    </div>
  )
}
