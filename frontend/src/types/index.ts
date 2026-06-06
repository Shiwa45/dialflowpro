// ── User & Auth ──────────────────────────────────────

export enum UserRole {
  SUPERADMIN = 1,
  MANAGER = 2,
  AGENT = 3,
}

export interface Tenant {
  id: number
  schema_name: string
  name: string
}

export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  role: UserRole
  is_active: boolean
  tenant?: Tenant
}

// ── Agent ────────────────────────────────────────────

export enum AgentStatus {
  LOGGED_OUT = 0,
  AVAILABLE = 1,
  ON_BREAK = 2,
}

export type AgentState =
  | 'Waiting'
  | 'Receiving'
  | 'In a queue call'
  | 'Idle'
  | 'Reserved'

export interface Agent {
  id: number
  name: string
  status: AgentStatus
  status_display: string
  state: AgentState
  sip_extension: string
  calls_answered: number
  talk_time: number
  wrap_up_time: number
  max_no_answer: number
  last_bridge_start: string | null
  last_bridge_end: string | null
}

export interface AgentProfile extends Agent {
  queues: QueueInfo[]
  today: {
    calls: number
    duration: number
    avg_duration: number
  }
  user: User
}

// ── Call ─────────────────────────────────────────────

export type CallState =
  | 'idle'
  | 'ringing'
  | 'active'
  | 'held'
  | 'wrap_up'
  | 'transferring'

export interface ActiveCall {
  call_id: string
  caller_number: string
  caller_name: string
  queue_name: string
  campaign_name: string
  state: CallState
  started_at: number      // Date.now() timestamp
  held_at?: number
  lead?: LeadInfo
  disposition?: string
  notes?: string
}

export interface LeadInfo {
  id?: number
  first_name?: string
  last_name?: string
  phone?: string
  email?: string
  company?: string
  location?: string
  tags?: string[]
  custom_fields?: Record<string, string>
  history?: InteractionRecord[]
}

export interface InteractionRecord {
  type: 'call' | 'email' | 'sms' | 'chat'
  title: string
  subtitle?: string
  date: string
  tag?: string
  duration?: number
  disposition?: string
}

// ── Queue ────────────────────────────────────────────

export interface QueueInfo {
  id: number
  name: string
  strategy?: number
  strategy_display?: string
  level?: number
  position?: number
  waiting_calls: number
  active_agents?: number
}

export interface Queue {
  id: number
  name: string
  description: string
  strategy: number
  strategy_display: string
  agent_count: number
  active_calls: number
}

// ── Campaign ─────────────────────────────────────────

export interface Campaign {
  id: number
  name: string
  campaign_code: string
  status: number
  status_display: string
  callerid: string
  frequency: number
  lines_per_agent?: number
  startingdate: string
  expirationdate: string
  total_contacts?: number
  completed_calls?: number
}

export interface CampaignInfo {
  id: number
  name: string
  campaign_code: string
  script?: string
}

// ── WebSocket Events ─────────────────────────────────

export interface WsAgentState {
  type: 'agent_state'
  agent: Agent
  queues: QueueInfo[]
}

export interface WsIncomingCall {
  type: 'incoming_call'
  call_id: string
  caller_number: string
  caller_name: string
  queue_name: string
  campaign_name: string
  lead: LeadInfo
  timestamp: string
}

export interface WsCallAnswered {
  type: 'call_answered'
  call_id: string
  status: string
  agent_state: string
}

export interface WsCallEnded {
  type: 'call_ended'
  call_id: string
  duration: number
  hangup_cause: string
  timestamp: string
}

export interface WsCampaignLead {
  type: 'campaign_lead'
  call_id: string
  lead: LeadInfo
  campaign: CampaignInfo
  script: string
}

export interface WsQueueStats {
  type: 'queue_stats'
  queue_id: number
  queue_name: string
  waiting_calls: number
  active_agents: number
}

export interface WsPeerStatus {
  type: 'peer_status'
  agent_id: number
  agent_name: string
  status: number
  status_display: string
}

export type AgentDesktopEvent =
  | WsAgentState
  | WsIncomingCall
  | WsCallAnswered
  | WsCallEnded
  | WsCampaignLead
  | WsQueueStats
  | WsPeerStatus
  | { type: 'error'; message: string; action?: string }
  | { type: 'pong'; ts: string }
  | { type: 'disposition_saved'; call_id: string; disposition: string }
  | { type: 'call_held'; call_id: string; status: string }
  | { type: 'call_resumed'; call_id: string; status: string }
  | { type: 'transfer_result'; call_id: string; target: string; status: string }
  | { type: 'dtmf_sent'; call_id: string; digits: string }

// ── CDR ──────────────────────────────────────────────

export interface CallDetailRecord {
  id: number
  callid: string
  caller_number: string
  phone_number: string
  disposition: string
  duration: number
  billsec: number
  starting_date: string
  campaign_name?: string
}

// ── Contacts ─────────────────────────────────────────

export interface Phonebook {
  id: number
  name: string
  contact_count: number
}

export interface Contact {
  id: number
  first_name: string
  last_name: string
  phone: string
  email: string
  status: number
}
