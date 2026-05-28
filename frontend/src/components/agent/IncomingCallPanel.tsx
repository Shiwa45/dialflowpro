import { Phone, PhoneOff, Tag } from 'lucide-react'
import { useState } from 'react'

export function IncomingCallPanel() {
  const [incomingCall, setIncomingCall] = useState({
    caller_number: '+91 98765 43210',
    location: 'India',
    campaign_type: 'Sales Inquiry',
  })
  const [autoAnswer, setAutoAnswer] = useState(false)

  const handleAnswer = () => {
    console.log('Answering call...')
  }

  const handleDecline = () => {
    console.log('Declining call...')
    setIncomingCall(null as any)
  }

  if (!incomingCall) {
    return (
      <div className="bg-[#111827] flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
            <Phone className="w-12 h-12 text-gray-600" />
          </div>
          <p className="text-gray-500">Waiting for calls...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#111827] flex flex-col items-center justify-center gap-8 p-8">
      {/* Call Status */}
      <div className="text-center w-full max-w-md">
        <p className="text-blue-400 text-sm font-medium tracking-wider mb-6">
          INCOMING CALL
        </p>

        {/* Avatar */}
        <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <div className="w-28 h-28 rounded-full bg-[#1F2937] flex items-center justify-center">
            <svg className="w-16 h-16 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
        </div>

        {/* Phone Number */}
        <h2 className="text-4xl font-light text-white mb-2">
          {incomingCall.caller_number}
        </h2>

        {/* Location */}
        <p className="text-gray-400 mb-4">{incomingCall.location}</p>

        {/* Campaign Type Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full">
          <Tag className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-sm text-blue-400">{incomingCall.campaign_type}</span>
        </div>
      </div>

      {/* Answer/Decline Buttons */}
      <div className="flex items-center gap-8">
        {/* Answer Button */}
        <button
          onClick={handleAnswer}
          className="group relative w-20 h-20 rounded-full bg-green-500 hover:bg-green-600 transition-all duration-200 shadow-lg shadow-green-500/50 hover:shadow-green-500/70 hover:scale-110"
        >
          <Phone className="absolute inset-0 m-auto w-8 h-8 text-white" />
          <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
            Answer
          </div>
        </button>

        {/* Decline Button */}
        <button
          onClick={handleDecline}
          className="group relative w-20 h-20 rounded-full bg-red-500 hover:bg-red-600 transition-all duration-200 shadow-lg shadow-red-500/50 hover:shadow-red-500/70 hover:scale-110"
        >
          <PhoneOff className="absolute inset-0 m-auto w-8 h-8 text-white" />
          <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
            Decline
          </div>
        </button>
      </div>

      {/* Auto Answer Toggle */}
      <div className="flex items-center gap-3 mt-4">
        <span className="text-sm text-gray-400">Auto Answer</span>
        <button
          onClick={() => setAutoAnswer(!autoAnswer)}
          className={`relative w-11 h-6 rounded-full transition-colors ${
            autoAnswer ? 'bg-blue-500' : 'bg-gray-700'
          }`}
        >
          <div
            className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
              autoAnswer ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      </div>
    </div>
  )
}
