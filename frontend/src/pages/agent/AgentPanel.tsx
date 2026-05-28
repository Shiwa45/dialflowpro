import { useEffect, useState } from 'react'
import { useAgent } from '@/hooks/useAgent'
import { Softphone } from '@/components/agent/Softphone'
import { IncomingCallPanel } from '@/components/agent/IncomingCallPanel'
import { CustomerInfoPanel } from '@/components/agent/CustomerInfoPanel'
import { MetricsBar } from '@/components/agent/MetricsBar'
import { BottomBar } from '@/components/agent/BottomBar'
import { Phone, Clock, PhoneIncoming, Timer, TrendingUp } from 'lucide-react'

export function AgentPanel() {
  const { agent, loading } = useAgent()
  const [callDuration, setCallDuration] = useState(0)

  // Timer for active call
  useEffect(() => {
    const interval = setInterval(() => {
      if (agent?.state === 'In a queue call') {
        setCallDuration(prev => prev + 1)
      } else {
        setCallDuration(0)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [agent?.state])

  if (loading) {
    return (
      <div className="h-screen bg-[#0A0E1A] flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  return (
    <div className="h-screen bg-[#0A0E1A] flex flex-col">
      {/* Top Header */}
      <header className="h-16 bg-[#111827] border-b border-gray-800 px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-blue-500" />
            <span className="text-white font-semibold">Agent Desktop</span>
          </div>
          
          <div className="h-6 w-px bg-gray-700" />
          
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              agent?.status === 1 ? 'bg-green-500' : 'bg-gray-500'
            }`} />
            <span className="text-sm text-gray-300">
              {agent?.status === 1 ? 'Available' : 'Unavailable'}
            </span>
          </div>
          
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Clock className="w-4 h-4" />
            <span>{formatTime(callDuration)}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-gray-700 rounded">
            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
          <button className="p-2 hover:bg-gray-700 rounded">
            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </header>

      {/* Metrics Bar */}
      <MetricsBar />

      {/* Main 3-Column Layout */}
      <div className="flex-1 grid grid-cols-[400px_1fr_450px] min-h-0">
        <Softphone />
        <IncomingCallPanel />
        <CustomerInfoPanel />
      </div>

      {/* Bottom Bar */}
      <BottomBar />
    </div>
  )
}

function formatTime(seconds: number): string {
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}
