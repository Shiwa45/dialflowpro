import { useState } from 'react'
import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { useAgentCommands } from '@/hooks/useAgentCommands'
import { formatTime, formatPhone } from '@/lib/utils'
import {
  Phone,
  PhoneOff,
  Pause,
  Play,
  ArrowRightLeft,
  Mic,
  MicOff,
  Hash,
  Users,
  MoreHorizontal,
  User,
  X,
} from 'lucide-react'

export function ActiveCallPanel() {
  const { activeCall, callDuration, isMuted } = useAgentDesktopStore()
  const {
    hangupCall,
    holdCall,
    resumeCall,
    transferCall,
    sendDtmf,
  } = useAgentCommands()
  const store = useAgentDesktopStore()

  const [showTransfer, setShowTransfer] = useState(false)
  const [transferTarget, setTransferTarget] = useState('')
  const [showKeypad, setShowKeypad] = useState(false)

  if (!activeCall) return null

  const isHeld = activeCall.state === 'held'
  const displayNumber = formatPhone(activeCall.caller_number)
  const displayName = activeCall.caller_name ||
    (activeCall.lead?.first_name
      ? `${activeCall.lead.first_name} ${activeCall.lead.last_name || ''}`.trim()
      : 'Unknown Caller')

  const controls = [
    {
      icon: isHeld ? Play : Pause,
      label: isHeld ? 'Resume' : 'Hold',
      active: isHeld,
      color: isHeld ? 'text-yellow-400' : 'text-gray-300',
      onClick: () =>
        isHeld ? resumeCall(activeCall.call_id) : holdCall(activeCall.call_id),
    },
    {
      icon: isMuted ? MicOff : Mic,
      label: isMuted ? 'Unmute' : 'Mute',
      active: isMuted,
      color: isMuted ? 'text-red-400' : 'text-gray-300',
      onClick: () => store.toggleMute(),
    },
    {
      icon: Hash,
      label: 'Keypad',
      active: showKeypad,
      color: showKeypad ? 'text-blue-400' : 'text-gray-300',
      onClick: () => { setShowKeypad(!showKeypad); setShowTransfer(false) },
    },
    {
      icon: ArrowRightLeft,
      label: 'Transfer',
      active: showTransfer,
      color: showTransfer ? 'text-purple-400' : 'text-gray-300',
      onClick: () => { setShowTransfer(!showTransfer); setShowKeypad(false) },
    },
    {
      icon: Users,
      label: 'Conference',
      active: false,
      color: 'text-gray-300',
      onClick: () => {},
    },
  ]

  const handleTransfer = () => {
    if (transferTarget.trim()) {
      transferCall(activeCall.call_id, transferTarget.trim())
      setTransferTarget('')
      setShowTransfer(false)
    }
  }

  const keypadDigits = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#'],
  ]

  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-[#0A0E1A] relative">
      {/* Call state indicator */}
      {isHeld && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-full">
          <span className="text-xs text-yellow-400 font-medium animate-pulse">
            ⏸ Call on hold
          </span>
        </div>
      )}

      <div className="flex flex-col items-center gap-6 max-w-lg w-full px-8">
        {/* Caller avatar */}
        <div className="relative">
          <div
            className={`w-24 h-24 rounded-full flex items-center justify-center border-2 transition-colors ${
              isHeld
                ? 'bg-yellow-500/10 border-yellow-500/30'
                : 'bg-green-500/10 border-green-500/30'
            }`}
          >
            <User className={`w-12 h-12 ${isHeld ? 'text-yellow-400' : 'text-green-400'}`} />
          </div>
          {/* Active indicator */}
          {!isHeld && (
            <div className="absolute bottom-0 right-0 w-5 h-5 bg-green-500 rounded-full border-2 border-[#0A0E1A] flex items-center justify-center">
              <Phone className="w-2.5 h-2.5 text-white" />
            </div>
          )}
        </div>

        {/* Caller info */}
        <div className="text-center">
          <h2 className="text-xl font-bold text-white mb-1">{displayName}</h2>
          <p className="text-sm text-gray-400 font-mono">{displayNumber}</p>
          {activeCall.queue_name && (
            <p className="text-xs text-gray-600 mt-1">
              Queue: {activeCall.queue_name}
            </p>
          )}
        </div>

        {/* Duration timer */}
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isHeld ? 'bg-yellow-500' : 'bg-green-500 animate-pulse'
            }`}
          />
          <span className="text-3xl font-mono text-white font-light tracking-wider">
            {formatTime(callDuration)}
          </span>
        </div>

        {/* Call controls */}
        <div className="flex items-center gap-4 mt-4">
          {controls.map((ctrl) => (
            <button
              key={ctrl.label}
              onClick={ctrl.onClick}
              className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all hover:bg-gray-800 active:scale-95 ${
                ctrl.active ? 'bg-gray-800' : ''
              }`}
            >
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center border transition-colors ${
                  ctrl.active
                    ? 'bg-gray-700 border-gray-600'
                    : 'bg-[#1F2937] border-gray-700 hover:border-gray-600'
                }`}
              >
                <ctrl.icon className={`w-5 h-5 ${ctrl.color}`} />
              </div>
              <span className="text-[10px] text-gray-500">{ctrl.label}</span>
            </button>
          ))}
        </div>

        {/* ── Transfer panel ── */}
        {showTransfer && (
          <div className="w-full bg-[#1F2937] border border-gray-700 rounded-xl p-4 animate-[slideDown_0.2s_ease]">
            <div className="flex items-center gap-2 mb-3">
              <ArrowRightLeft className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-white font-medium">Transfer call</span>
              <button
                onClick={() => setShowTransfer(false)}
                className="ml-auto text-gray-500 hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={transferTarget}
                onChange={(e) => setTransferTarget(e.target.value)}
                placeholder="Extension or number"
                className="flex-1 bg-[#111827] border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleTransfer()}
              />
              <button
                onClick={handleTransfer}
                disabled={!transferTarget.trim()}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg font-medium transition-colors"
              >
                Transfer
              </button>
            </div>
          </div>
        )}

        {/* ── In-call keypad ── */}
        {showKeypad && (
          <div className="w-64 bg-[#1F2937] border border-gray-700 rounded-xl p-4 animate-[slideDown_0.2s_ease]">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-white font-medium">DTMF Keypad</span>
              <button
                onClick={() => setShowKeypad(false)}
                className="text-gray-500 hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {keypadDigits.flat().map((digit) => (
                <button
                  key={digit}
                  onClick={() => sendDtmf(activeCall.call_id, digit)}
                  className="bg-[#111827] hover:bg-gray-700 active:bg-gray-600 text-white rounded-lg h-11 text-lg font-light border border-gray-700/50 transition-all active:scale-95"
                >
                  {digit}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Hangup button */}
        <button
          onClick={() => hangupCall(activeCall.call_id)}
          className="mt-4 w-16 h-16 rounded-full bg-red-600 hover:bg-red-500 active:bg-red-700 flex items-center justify-center transition-all active:scale-90 shadow-lg shadow-red-500/20"
        >
          <PhoneOff className="w-7 h-7 text-white" />
        </button>
      </div>

      <style>{`
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
