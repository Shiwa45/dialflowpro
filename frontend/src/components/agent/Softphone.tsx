import { useState } from 'react'
import { Phone, Volume2, Search } from 'lucide-react'

export function Softphone() {
  const [phoneNumber, setPhoneNumber] = useState('')
  const [volume, setVolume] = useState(50)
  const [activeCall, setActiveCall] = useState(false)

  const dialpadButtons = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#'],
  ]

  const handleDial = (digit: string) => {
    setPhoneNumber(prev => prev + digit)
  }

  const makeCall = () => {
    console.log('Making call to:', phoneNumber)
    setActiveCall(true)
  }

  return (
    <div className="bg-[#111827] border-r border-gray-800 p-6 flex flex-col">
      {/* Status */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-sm text-green-500">Connected</span>
        </div>
        
        <h3 className="text-white font-semibold mb-1">Softphone</h3>
      </div>

      {/* Search or Dial Input */}
      <div className="mb-6 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          placeholder="Search or Dial"
          className="w-full bg-[#1F2937] border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Dialpad */}
      <div className="mb-6">
        <div className="grid grid-cols-3 gap-2">
          {dialpadButtons.map((row, rowIdx) => (
            row.map((digit) => (
              <button
                key={`${rowIdx}-${digit}`}
                onClick={() => handleDial(digit)}
                className="bg-[#1F2937] hover:bg-[#374151] text-white rounded-lg h-14 flex flex-col items-center justify-center border border-gray-700 transition-colors"
              >
                <span className="text-2xl font-light">{digit}</span>
                {digit !== '*' && digit !== '#' && (
                  <span className="text-[10px] text-gray-500 uppercase">
                    {getLetters(digit)}
                  </span>
                )}
              </button>
            ))
          ))}
        </div>
      </div>

      {/* Call Button */}
      <button
        onClick={makeCall}
        disabled={!phoneNumber}
        className="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg h-12 flex items-center justify-center gap-2 font-medium transition-colors mb-6"
      >
        <Phone className="w-5 h-5" />
        <span>Call</span>
      </button>

      {/* Volume Control */}
      <div className="mt-auto">
        <div className="flex items-center gap-3">
          <Volume2 className="w-4 h-4 text-gray-400" />
          <div className="flex-1">
            <input
              type="range"
              min="0"
              max="100"
              value={volume}
              onChange={(e) => setVolume(Number(e.target.value))}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500"
            />
          </div>
          <span className="text-xs text-gray-500 w-8">{volume}%</span>
        </div>
      </div>

      {/* Active Call Indicator */}
      {activeCall && (
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <div className="text-sm text-blue-400">Active Call</div>
          <div className="text-xs text-gray-400 mt-1">00:00:00</div>
        </div>
      )}

      {/* Call Controls (when active) */}
      {activeCall && (
        <div className="mt-4 grid grid-cols-4 gap-2">
          {[
            { icon: '⏸', label: 'Hold' },
            { icon: '🔇', label: 'Mute' },
            { icon: '#️⃣', label: 'Keypad' },
            { icon: '↗️', label: 'Transfer' },
            { icon: '👥', label: 'Conference' },
            { icon: '⋯', label: 'More' },
          ].map((control, idx) => (
            <button
              key={idx}
              className="flex flex-col items-center gap-1 p-2 hover:bg-gray-700 rounded"
            >
              <span className="text-lg">{control.icon}</span>
              <span className="text-[10px] text-gray-400">{control.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function getLetters(digit: string): string {
  const mapping: Record<string, string> = {
    '2': 'ABC',
    '3': 'DEF',
    '4': 'GHI',
    '5': 'JKL',
    '6': 'MNO',
    '7': 'PQRS',
    '8': 'TUV',
    '9': 'WXYZ',
  }
  return mapping[digit] || ''
}
