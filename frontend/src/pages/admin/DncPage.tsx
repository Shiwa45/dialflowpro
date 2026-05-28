import { useEffect, useState } from 'react'
import { Plus, Upload, Download, Trash2 } from 'lucide-react'
import api from '@/api/client'

export function DncPage() {
  const [dncLists, setDncLists] = useState([])
  const [selectedList, setSelectedList] = useState<any>(null)
  const [numbers, setNumbers] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [showAddNumber, setShowAddNumber] = useState(false)

  useEffect(() => {
    fetchDncLists()
  }, [])

  useEffect(() => {
    if (selectedList) {
      fetchNumbers()
    }
  }, [selectedList])

  const fetchDncLists = async () => {
    try {
      const { data } = await api.get('/dnc/dnc/')
      setDncLists(data.results || data)
      if ((data.results || data).length > 0 && !selectedList) {
        setSelectedList((data.results || data)[0])
      }
    } catch (error) {
      console.error('Failed to fetch DNC lists:', error)
    }
  }

  const fetchNumbers = async () => {
    if (!selectedList) return
    try {
      const { data } = await api.get(`/dnc/contacts/?dnc=${selectedList.id}`)
      setNumbers(data.results || data)
    } catch (error) {
      console.error('Failed to fetch DNC numbers:', error)
    }
  }

  const handleAddNumber = async (phoneNumber: string) => {
    try {
      await api.post(`/dnc/dnc/${selectedList.id}/add_number/`, { phone_number: phoneNumber })
      fetchNumbers()
      setShowAddNumber(false)
    } catch (error) {
      console.error('Failed to add number:', error)
      alert('Failed to add number')
    }
  }

  const handleRemoveNumber = async (id: number) => {
    if (!confirm('Remove this number from DNC list?')) return
    try {
      await api.post(`/dnc/dnc/${selectedList.id}/remove_number/`, { contact_id: id })
      fetchNumbers()
    } catch (error) {
      console.error('Failed to remove number:', error)
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Do-Not-Call (DNC) Management</h1>
          <p className="text-gray-400">Manage blocked numbers and compliance</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
        >
          <Plus className="w-5 h-5" />
          New DNC List
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* DNC Lists Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-[#111827] border border-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-4">DNC Lists</h3>
            <div className="space-y-2">
              {dncLists.map((list: any) => (
                <button
                  key={list.id}
                  onClick={() => setSelectedList(list)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                    selectedList?.id === list.id
                      ? 'bg-blue-500 text-white'
                      : 'bg-[#1F2937] text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <div className="font-medium">{list.name}</div>
                  <div className="text-xs opacity-75 mt-1">{list.count || 0} numbers</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Numbers Table */}
        <div className="lg:col-span-3">
          {selectedList ? (
            <div className="bg-[#111827] border border-gray-800 rounded-lg">
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">{selectedList.name}</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowAddNumber(true)}
                    className="px-4 py-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-lg text-sm"
                  >
                    <Plus className="w-4 h-4 inline mr-1" />
                    Add Number
                  </button>
                  <button className="px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg text-sm">
                    <Upload className="w-4 h-4 inline mr-1" />
                    Import
                  </button>
                  <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">
                    <Download className="w-4 h-4 inline mr-1" />
                    Export
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-[#1F2937] border-b border-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Phone Number</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Added Date</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {numbers.length === 0 ? (
                      <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-500">No numbers in this list</td></tr>
                    ) : (
                      numbers.map((number: any) => (
                        <tr key={number.id} className="hover:bg-[#1F2937]">
                          <td className="px-4 py-3 text-white font-mono">{number.phone_number}</td>
                          <td className="px-4 py-3 text-sm text-gray-400">
                            {new Date(number.created_date).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleRemoveNumber(number.id)}
                              className="p-1 hover:bg-gray-700 rounded text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-8 text-center">
              <p className="text-gray-500">Select a DNC list to view numbers</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Number Modal */}
      {showAddNumber && (
        <AddNumberModal onClose={() => setShowAddNumber(false)} onAdd={handleAddNumber} />
      )}
    </div>
  )
}

function AddNumberModal({ onClose, onAdd }: any) {
  const [number, setNumber] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onAdd(number)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#111827] border border-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold text-white mb-4">Add Number to DNC</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Phone Number *</label>
            <input
              type="tel"
              value={number}
              onChange={(e) => setNumber(e.target.value)}
              placeholder="+15551234567"
              className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Enter in E.164 format</p>
          </div>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg">
              Add Number
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
