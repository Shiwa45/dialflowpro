// AI Agent feature types — mirror backend serializers.

export enum AIAgentStatus {
  DRAFT = 0,
  ACTIVE = 1,
  PAUSED = 2,
  TRAINING = 3,
}

export type LLMProvider = 'sarvam' | 'gemini'

export interface AISubscription {
  is_active: boolean
  plan_name?: string
  max_agents?: number
  monthly_minute_quota?: number
  minutes_used_this_period?: number
  minutes_remaining?: number
  quota_exhausted?: boolean
  period_start?: string | null
  period_end?: string | null
  detail?: string
}

export interface AIAgent {
  id: number
  name: string
  description: string
  status: AIAgentStatus
  status_display: string
  call_direction: 'inbound' | 'outbound'
  persona_name: string
  greeting: string
  system_prompt: string
  temperature: number
  max_response_tokens: number
  llm_provider: LLMProvider
  sarvam_llm_model: string
  gemini_model: string
  enable_thinking: boolean
  active_llm_model: string
  primary_language: string
  auto_detect_language: boolean
  stt_model: string
  stt_mode: string
  tts_model: string
  tts_speaker: string
  tts_pace: number
  tts_temperature: number
  allow_human_transfer: boolean
  transfer_queue: number | null
  allow_callback: boolean
  confidence_transfer_threshold: number
  max_call_duration_seconds: number
  kb_last_indexed: string | null
  kb_chunk_count: number
  knowledge_count: number
  created_date?: string
  updated_date?: string
}

export interface AIKnowledgeItem {
  id: number
  agent: number
  source_type: 'product' | 'faq' | 'document' | 'freeform'
  source_type_display: string
  title: string
  content: string
  product_name: string
  product_price: string
  product_attributes: Record<string, string>
  is_active: boolean
}

export interface AICallSession {
  id: number
  agent: number
  agent_name: string
  caller_number: string
  started_at: string | null
  duration_seconds: number
  outcome: string
  outcome_display: string
  detected_language: string
  sentiment_score: number | null
}

export const LANGUAGES: { code: string; label: string }[] = [
  { code: 'unknown', label: 'Auto-detect' },
  { code: 'hi-IN', label: 'Hindi' },
  { code: 'en-IN', label: 'English (India)' },
  { code: 'bn-IN', label: 'Bengali' },
  { code: 'ta-IN', label: 'Tamil' },
  { code: 'te-IN', label: 'Telugu' },
  { code: 'gu-IN', label: 'Gujarati' },
  { code: 'kn-IN', label: 'Kannada' },
  { code: 'ml-IN', label: 'Malayalam' },
  { code: 'mr-IN', label: 'Marathi' },
  { code: 'pa-IN', label: 'Punjabi' },
  { code: 'od-IN', label: 'Odia' },
]

// Bulbul v3 speakers, grouped for the picker.
export const V3_SPEAKERS = {
  Male: ['shubh', 'aditya', 'rahul', 'rohan', 'amit', 'dev', 'ratan', 'varun',
    'manan', 'sumit', 'kabir', 'aayan', 'ashutosh', 'advait', 'anand', 'tarun',
    'sunny', 'mani', 'gokul', 'vijay', 'mohit', 'rehan', 'soham'],
  Female: ['ritu', 'priya', 'neha', 'pooja', 'simran', 'kavya', 'ishita',
    'shreya', 'roopa', 'tanya', 'shruti', 'suhani', 'kavitha', 'rupali'],
}

export const SARVAM_MODELS = [
  { value: 'sarvam-105b', label: 'Sarvam 105B (flagship)' },
  { value: 'sarvam-30b', label: 'Sarvam 30B (balanced)' },
  { value: 'sarvam-m', label: 'Sarvam-M 24B (legacy)' },
]

export const GEMINI_MODELS = [
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
]
