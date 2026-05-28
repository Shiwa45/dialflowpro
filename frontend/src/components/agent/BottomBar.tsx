import { ChevronDown } from 'lucide-react'

export function BottomBar() {
  return (
    <div className="h-16 bg-[#111827] border-t border-gray-800 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-400">Queue:</label>
        <button className="flex items-center gap-2 px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white hover:bg-[#374151] transition-colors">
          <span>Sales Support</span>
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </button>
      </div>

      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-400">Wrap-up Time:</label>
        <button className="flex items-center gap-2 px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-lg text-white hover:bg-[#374151] transition-colors">
          <span>00:30</span>
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </button>
      </div>
    </div>
  )
}
