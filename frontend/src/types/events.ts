export type VoiceState =
  | 'IDLE'
  | 'WAKE_DETECTED'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'THINKING'
  | 'EXECUTING'
  | 'SPEAKING'
  | 'ERROR'
  | 'CANCELLED'

export type TaskStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'

export interface FridayTask {
  id: string
  name: string
  status: TaskStatus
  progress: number | null
  startedAt: string | null
  completedAt: string | null
  result: string | null
  error: string | null
}

export interface PipelineStats {
  last_provider: string | null
  last_latency_ms: number | null
  requests_handled: number
  tool_calls_made: number
  errors: number
}

export type ServerEvent =
  | { type: 'voice_state'; state: VoiceState }
  | { type: 'transcript'; text: string }
  | { type: 'assistant_response'; text: string }
  | { type: 'task_started'; task: FridayTask }
  | { type: 'task_completed'; task: FridayTask }
  | {
      type: 'system_stats'
      cpu: number
      ram: number
      disk: number
      battery: number | null
      os: string
      uptime_seconds: number
      network_mbps: number
      microphone: string | null
      speaker: string | null
    }
  | { type: 'audio_level'; level: number }
  | { type: 'thinking'; active: boolean }
  | { type: 'tool_started'; tool: string; task_id: string }
  | { type: 'tool_completed'; tool: string; task_id: string; success: boolean }
  | { type: 'notification'; level: 'info' | 'warning' | 'error'; message: string; requires_confirmation?: boolean; confirmation_id?: string }
  | { type: 'error'; message: string; context?: string }
  | { type: 'connection'; status: 'connected' | 'disconnected' }
  | { type: 'active_window'; app_name: string | null; title: string | null }
  | { type: 'tts_state'; speaking: boolean }
  | {
      type: 'weather'
      city: string
      region: string
      country: string
      temperature_c: number
      humidity: number
      wind_kmh: number
      condition: string
      weather_code: number
    }
  | {
      type: 'security_status'
      defender_enabled: boolean | null
      firewall_enabled: boolean | null
      updates: { last_search: string | null; last_install: string | null } | null
    }
  | ({ type: 'pipeline_stats' } & PipelineStats)

export type ClientEvent =
  | { type: 'user_text'; text: string }
  | { type: 'manual_listen' }
  | { type: 'cancel' }
  | { type: 'confirm'; confirmation_id: string; approved: boolean }
