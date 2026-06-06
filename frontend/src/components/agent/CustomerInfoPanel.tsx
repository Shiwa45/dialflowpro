import { useState } from 'react'
import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { formatPhone, timeAgo, formatDuration } from '@/lib/utils'
import {
  User,
  Phone,
  Mail,
  MapPin,
  Building2,
  Tag,
  Clock,
  MessageSquare,
  Edit3,
  ChevronRight,
} from 'lucide-react'

type Tab = 'info' | 'history' | 'notes'

export function CustomerInfoPanel() {
  const { activeCall } = useAgentDesktopStore()
  const [activeTab, setActiveTab] = useState<Tab>('info')
  const [notes, setNotes] = useState('')

  const lead = activeCall?.lead || {}
  const displayName =
    lead.first_name || lead.last_name
      ? `${lead.first_name || ''} ${lead.last_name || ''}`.trim()
      : activeCall?.caller_name || 'Unknown'

  const tabs = [
    { id: 'info' as Tab, label: 'Contact' },
    { id: 'history' as Tab, label: 'History' },
    { id: 'notes' as Tab, label: 'Notes' },
  ]

  return (
    <div className="h-full bg-[#111827] border-l border-gray-800 flex flex-col">
      {/* ── Tab bar ── */}
      <div className="flex border-b border-gray-800">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-3 text-xs font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/5'
                : 'text-gray-500 hover:text-gray-300 border-b-2 border-transparent'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'info' && (
          <div className="p-4 space-y-4">
            {/* Contact header */}
            <div className="flex items-center gap-3 pb-4 border-b border-gray-800">
              <div className="w-12 h-12 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
                <User className="w-6 h-6 text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-white truncate">{displayName}</h3>
                {lead.company && (
                  <p className="text-xs text-gray-400 truncate">{lead.company}</p>
                )}
                {lead.id && (
                  <p className="text-[10px] text-gray-600">ID: {lead.id}</p>
                )}
              </div>
            </div>

            {/* Contact details */}
            <div className="space-y-3">
              <InfoRow
                icon={Phone}
                label="Phone"
                value={formatPhone(lead.phone || activeCall?.caller_number || '')}
              />
              {lead.email && (
                <InfoRow icon={Mail} label="Email" value={lead.email} />
              )}
              {lead.location && (
                <InfoRow icon={MapPin} label="Location" value={lead.location} />
              )}
              {lead.company && (
                <InfoRow icon={Building2} label="Company" value={lead.company} />
              )}
            </div>

            {/* Tags */}
            {lead.tags && lead.tags.length > 0 && (
              <div className="pt-3 border-t border-gray-800">
                <div className="flex items-center gap-1.5 mb-2">
                  <Tag className="w-3 h-3 text-gray-500" />
                  <span className="text-[10px] text-gray-500 uppercase font-medium">Tags</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {lead.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] rounded-full border border-blue-500/20"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Custom fields */}
            {lead.custom_fields && Object.keys(lead.custom_fields).length > 0 && (
              <div className="pt-3 border-t border-gray-800">
                <span className="text-[10px] text-gray-500 uppercase font-medium">
                  Additional Info
                </span>
                <div className="mt-2 space-y-2">
                  {Object.entries(lead.custom_fields).map(([key, val]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-xs text-gray-500 capitalize">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-gray-300">{val}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Campaign info */}
            {activeCall?.campaign_name && (
              <div className="pt-3 border-t border-gray-800">
                <span className="text-[10px] text-gray-500 uppercase font-medium">
                  Campaign
                </span>
                <p className="text-sm text-gray-300 mt-1">{activeCall.campaign_name}</p>
              </div>
            )}

            {/* If no data at all */}
            {!lead.phone && !lead.email && !lead.first_name && (
              <div className="text-center py-8">
                <User className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                <p className="text-xs text-gray-600">
                  No contact information available
                </p>
                <p className="text-[10px] text-gray-700 mt-1">
                  Calling {formatPhone(activeCall?.caller_number || '')}
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="p-4">
            {lead.history && lead.history.length > 0 ? (
              <div className="space-y-3">
                {lead.history.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3 bg-[#1F2937] rounded-lg border border-gray-700/50"
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        item.type === 'call'
                          ? 'bg-blue-500/10 text-blue-400'
                          : item.type === 'email'
                            ? 'bg-purple-500/10 text-purple-400'
                            : 'bg-green-500/10 text-green-400'
                      }`}
                    >
                      {item.type === 'call' ? (
                        <Phone className="w-3.5 h-3.5" />
                      ) : item.type === 'email' ? (
                        <Mail className="w-3.5 h-3.5" />
                      ) : (
                        <MessageSquare className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-white">{item.title}</span>
                        <span className="text-[10px] text-gray-600">{item.date}</span>
                      </div>
                      {item.subtitle && (
                        <p className="text-[11px] text-gray-400 mt-0.5">{item.subtitle}</p>
                      )}
                      {item.tag && (
                        <span className="inline-block mt-1 px-2 py-0.5 bg-gray-700 text-gray-400 text-[9px] rounded-full">
                          {item.tag}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Clock className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                <p className="text-xs text-gray-600">No interaction history</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="p-4 flex flex-col h-full">
            <div className="flex items-center gap-1.5 mb-3">
              <Edit3 className="w-3 h-3 text-gray-500" />
              <span className="text-[10px] text-gray-500 uppercase font-medium">
                Call Notes
              </span>
            </div>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Type notes about this call..."
              className="flex-1 w-full bg-[#1F2937] border border-gray-700 rounded-xl p-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50 resize-none min-h-[200px]"
            />
            <p className="text-[10px] text-gray-600 mt-2">
              Notes are saved with the call disposition
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: any
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-7 h-7 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
        <Icon className="w-3.5 h-3.5 text-gray-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-gray-600 uppercase">{label}</p>
        <p className="text-xs text-gray-200 truncate">{value}</p>
      </div>
    </div>
  )
}
