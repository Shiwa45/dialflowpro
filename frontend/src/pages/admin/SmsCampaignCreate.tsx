import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Save, X } from 'lucide-react'
import api from '@/api/client'

export function SmsCampaignCreate() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [phonebooks, setPhonebooks] = useState([])
  const [gateways, setGateways] = useState([])

  const [formData, setFormData] = useState({
    name: '',
    message_text: '',
    gateway: '',
    phonebook: [],
    startingdate: '',
    expirationdate: '',
    frequency: 10,
  })

  useEffect(() => {
    fetchOptions()
  }, [])

  const fetchOptions = async () => {
    try {
      const [pb, gw] = await Promise.all([
        api.get('/dialer-contact/phonebooks/'),
        api.get('/sms/gateways/'),
      ])
      setPhonebooks(pb.data.results || pb.data)
      setGateways(gw.data.results || gw.data)
    } catch (error) {
      console.error('Failed to fetch options:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await api.post('/sms/campaigns/', formData)
      navigate('/sms-campaigns')
    } catch (error) {
      console.error('Failed to create SMS campaign:', error)
      alert('Failed to create SMS campaign')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Create SMS Campaign</h1>
            <p className="text-gray-400">Set up a new SMS marketing campaign</p>
          </div>
          <button onClick={() => navigate('/sms-campaigns')} className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
            Cancel
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="bg-[#111827] border border-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Campaign Details</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Campaign Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Message Text *</label>
                <textarea
                  value={formData.message_text}
                  onChange={(e) => setFormData({ ...formData, message_text: e.target.value })}
                  rows={4}
                  maxLength={160}
                  className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">{formData.message_text.length}/160 characters</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">SMS Gateway *</label>
                <select
                  value={formData.gateway}
                  onChange={(e) => setFormData({ ...formData, gateway: e.target.value })}
                  className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Gateway</option>
                  {gateways.map((gw: any) => (
                    <option key={gw.id} value={gw.id}>{gw.name} ({gw.gateway_type_display})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Phonebook(s) *</label>
                <select
                  multiple
                  value={formData.phonebook}
                  onChange={(e) => {
                    const values = Array.from(e.target.selectedOptions, option => Number(option.value))
                    setFormData({ ...formData, phonebook: values })
                  }}
                  className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
                  required
                >
                  {phonebooks.map((pb: any) => (
                    <option key={pb.id} value={pb.id}>{pb.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Schedule */}
          <div className="bg-[#111827] border border-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Schedule</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Start Date *</label>
                <input
                  type="datetime-local"
                  value={formData.startingdate}
                  onChange={(e) => setFormData({ ...formData, startingdate: e.target.value })}
                  className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">End Date *</label>
                <input
                  type="datetime-local"
                  value={formData.expirationdate}
                  onChange={(e) => setFormData({ ...formData, expirationdate: e.target.value })}
                  className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Frequency (messages/min)</label>
                <input
                  type="number"
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: Number(e.target.value) })}
                  className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="100"
                />
              </div>
            </div>
          </div>

          {/* Submit */}
          <div className="flex items-center justify-end gap-4">
            <button type="button" onClick={() => navigate('/sms-campaigns')} className="px-6 py-2 border border-gray-700 text-gray-300 rounded-lg hover:bg-gray-800">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 text-white rounded-lg"
            >
              <Save className="w-5 h-5" />
              {loading ? 'Creating...' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
