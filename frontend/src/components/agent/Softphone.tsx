import { useAgentDesktopStore } from '@/store/agentDesktopStore'
import { useAgentCommands } from '@/hooks/useAgentCommands'
import { AgentStatus } from '@/types'
import {
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  Search,
  Trash2,
  Coffee,
  CircleDot,
  LogOut,
} from 'lucide-react'

const DIALPAD: [string, string][] = [
  ['1', ''],
  ['2', 'ABC'],
  ['3', 'DEF'],
  ['4', 'GHI'],
  ['5', 'JKL'],
  ['6', 'MNO'],
  ['7', 'PQRS'],
  ['8', 'TUV'],
  ['9', 'WXYZ'],
  ['*', ''],
  ['0', '+'],
  ['#', ''],
]

export function Softphone() {
  const {
    agent,
    activeCall,
    dialInput,
    volume,
    isMuted,
  } = useAgentDesktopStore()

  const {
    setStatus,
    logout,
    sendDtmf,
    hangupCall,
    makeCall,
  } = useAgentCommands()

  const store = useAgentDesktopStore()

  const handleDial = (digit: string) => {
    // Play DTMF tone feedback
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      const freqs: Record<string, number> = {
        '1': 697, '2': 697, '3': 697,
        '4': 770, '5': 770, '6': 770,
        '7': 852, '8': 852, '9': 852,
        '*': 941, '0': 941, '#': 941,
      }
      osc.frequency.value = freqs[digit] || 800
      gain.gain.value = 0.1
      osc.start()
      osc.stop(ctx.currentTime + 0.08)
    } catch { /* silent */ }

    if (activeCall && activeCall.state === 'active') {
      // Send DTMF to active call
      sendDtmf(activeCall.call_id, digit)
    } else {
      store.appendDialDigit(digit)
    }
  }

  const handleMakeCall = () => {
    if (!dialInput.trim()) return
    makeCall(dialInput.trim())
    store.clearDialInput()
  }

  const statusOptions = [
    {
      label: 'Available',
      icon: CircleDot,
      color: 'bg-green-500',
      active: agent?.status === AgentStatus.AVAILABLE,
      onClick: () => setStatus('available'),
    },
    {
      label: 'On Break',
      icon: Coffee,
      color: 'bg-yellow-500',
      active: agent?.status === AgentStatus.ON_BREAK,
      onClick: () => setStatus('on_break'),
    },
    {
      label: 'Log Out',
      icon: LogOut,
      color: 'bg-gray-500',
      active: false,
      onClick: () => logout(),
    },
  ]

  return (
    <div className="h-full bg-[#111827] border-r border-gray-800 flex flex-col">
      {/* ── Status selector ── */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex gap-1">
          {statusOptions.map((opt) => (
            <button
              key={opt.label}
              onClick={opt.onClick}
              className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium transition-all ${
                opt.active
                  ? 'bg-gray-700/80 text-white ring-1 ring-gray-600'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800'
              }`}
            >
              <div className={`w-1.5 h-1.5 rounded-full ${opt.color}`} />
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Search / dial input ── */}
      <div className="px-4 pt-4 pb-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={dialInput}
            onChange={(e) => store.setDialInput(e.target.value)}
            placeholder="Search or dial"
            className="w-full bg-[#1F2937] border border-gray-700 rounded-xl pl-10 pr-10 py-2.5 text-white text-sm placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 transition-colors"
          />
          {dialInput && (
            <button
              onClick={() => store.clearDialInput()}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* ── Dialpad ── */}
      <div className="px-4 py-2 flex-1">
        <div className="grid grid-cols-3 gap-2">
          {DIALPAD.map(([digit, letters]) => (
            <button
              key={digit}
              onClick={() => handleDial(digit)}
              className="bg-[#1F2937] hover:bg-[#374151] active:bg-[#4B5563] text-white rounded-xl h-14 flex flex-col items-center justify-center border border-gray-700/50 transition-all active:scale-95"
            >
              <span className="text-xl font-light leading-none">{digit}</span>
              {letters && (
                <span className="text-[9px] text-gray-500 tracking-widest mt-0.5">
                  {letters}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── Call / hangup button ── */}
        <div className="mt-3">
          {activeCall && activeCall.state === 'active' ? (
            <button
              onClick={() => hangupCall(activeCall.call_id)}
              className="w-full bg-red-600 hover:bg-red-500 active:bg-red-700 text-white rounded-xl h-12 flex items-center justify-center gap-2 font-medium transition-all active:scale-[0.98]"
            >
              <PhoneOff className="w-5 h-5" />
              End Call
            </button>
          ) : (
            <button
              onClick={handleMakeCall}
              disabled={!dialInput.trim()}
              className="w-full bg-green-600 hover:bg-green-500 active:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl h-12 flex items-center justify-center gap-2 font-medium transition-all active:scale-[0.98]"
            >
              <Phone className="w-5 h-5" />
              Call
            </button>
          )}
        </div>
      </div>

      {/* ── Volume control ── */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center gap-3">
          <button
            onClick={() => store.toggleMute()}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isMuted ? (
              <VolumeX className="w-4 h-4 text-red-400" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </button>
          <div className="flex-1">
            <input
              type="range"
              min="0"
              max="100"
              value={isMuted ? 0 : volume}
              onChange={(e) => store.setVolume(Number(e.target.value))}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500"
            />
          </div>
          <span className="text-xs text-gray-600 w-7 text-right">
            {isMuted ? '0' : volume}%
          </span>
        </div>
      </div>
    </div>
  )
}
