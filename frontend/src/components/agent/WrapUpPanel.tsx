import { useState } from 'react'
import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { useAgentCommands } from '@/hooks/useAgentCommands'
import { formatTime, formatPhone } from '@/lib/utils'
import {
  CheckCircle2,
  Clock,
  FileText,
  Send,
} from 'lucide-react'

export function WrapUpPanel() {
  const { activeCall, wrapUpTime, callDuration, dispositions } = useAgentDesktopStore()
  const { setDisposition } = useAgentCommands()

  const [selectedDisp, setSelectedDisp] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [submitted, setSubmitted] = useState(false)

  if (!activeCall) return null

  const handleSubmit = () => {
    if (selectedDisp && activeCall.call_id) {
      setDisposition(activeCall.call_id, selectedDisp, notes)
      setSubmitted(true)
    }
  }

  if (submitted) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#0A0E1A]">
        <div className="text-center">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-1">Disposition Saved</h2>
          <p className="text-sm text-gray-400">
            {selectedDisp} — ready for next call
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex items-center justify-center bg-[#0A0E1A]">
      <div className="max-w-lg w-full px-6">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-xl font-bold text-white mb-1">Call Completed</h2>
          <p className="text-sm text-gray-400">
            {formatPhone(activeCall.caller_number)} · {formatTime(callDuration)}
          </p>

          {/* Wrap-up countdown */}
          {wrapUpTime > 0 && (
            <div className="mt-3 flex items-center justify-center gap-2">
              <Clock className="w-4 h-4 text-orange-400" />
              <span className="text-sm text-orange-400 font-mono">
                Wrap-up: {formatTime(wrapUpTime)}
              </span>
            </div>
          )}
        </div>

        {/* Disposition selection */}
        <div className="mb-6">
          <label className="text-xs text-gray-500 uppercase font-medium mb-3 block">
            Select Disposition
          </label>
          <div className="grid grid-cols-3 gap-2">
            {dispositions.map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDisp(d)}
                className={`px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  selectedDisp === d
                    ? 'bg-blue-600 text-white ring-1 ring-blue-400'
                    : 'bg-[#1F2937] text-gray-400 border border-gray-700 hover:border-gray-600 hover:text-white'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div className="mb-6">
          <label className="text-xs text-gray-500 uppercase font-medium mb-2 flex items-center gap-1.5">
            <FileText className="w-3 h-3" />
            Notes (optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add any notes about this call..."
            rows={3}
            className="w-full bg-[#1F2937] border border-gray-700 rounded-xl p-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50 resize-none"
          />
        </div>

        {/* Action — disposition is mandatory; no skipping to the next call */}
        <div className="flex flex-col gap-2">
          <button
            onClick={handleSubmit}
            disabled={!selectedDisp}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl text-sm font-medium transition-colors"
          >
            <Send className="w-4 h-4" />
            Save Disposition &amp; Continue
          </button>
          <p className="text-center text-xs text-gray-600">
            You must select a disposition to take the next call.
          </p>
        </div>
      </div>
    </div>
  )
}
