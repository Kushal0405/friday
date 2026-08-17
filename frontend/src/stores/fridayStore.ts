import { create } from 'zustand'
import type { FridayTask, PipelineStats, ServerEvent, VoiceState } from '../types/events'

export interface ConversationEntry {
  id: string
  role: 'user' | 'friday'
  text: string
  timestamp: number
}

export interface SystemStats {
  cpu: number
  ram: number
  disk: number
  battery: number | null
  os: string
  uptimeSeconds: number
  networkMbps: number
  microphone: string | null
  speaker: string | null
}

export interface WeatherState {
  city: string
  region: string
  country: string
  temperatureC: number
  humidity: number
  windKmh: number
  condition: string
  weatherCode: number
}

export interface SecurityState {
  defenderEnabled: boolean | null
  firewallEnabled: boolean | null
  lastUpdateCheck: string | null
  lastUpdateInstall: string | null
}

export interface ActiveWindowState {
  appName: string | null
  title: string | null
}

const MAX_HISTORY_POINTS = 40
const MAX_CONVERSATION_ENTRIES = 100
const MAX_RECENT_ACTIVITY = 20

interface FridayState {
  voiceState: VoiceState
  systemStats: SystemStats | null
  systemStatsHistory: SystemStats[]
  weather: WeatherState | null
  security: SecurityState | null
  activeWindow: ActiveWindowState | null
  pipelineStats: PipelineStats | null
  runningTasks: FridayTask[]
  recentActivity: FridayTask[]
  conversation: ConversationEntry[]
  audioLevel: number
  ttsSpeaking: boolean
  lastError: string | null

  applyEvent: (event: ServerEvent) => void
  clearConversation: () => void
}

let entryCounter = 0

export const useFridayStore = create<FridayState>((set) => ({
  voiceState: 'IDLE',
  systemStats: null,
  systemStatsHistory: [],
  weather: null,
  security: null,
  activeWindow: null,
  pipelineStats: null,
  runningTasks: [],
  recentActivity: [],
  conversation: [],
  audioLevel: 0,
  ttsSpeaking: false,
  lastError: null,

  applyEvent: (event) => {
    switch (event.type) {
      case 'voice_state':
        set({ voiceState: event.state })
        break

      case 'transcript':
        set((s) => ({
          conversation: [
            ...s.conversation.slice(-(MAX_CONVERSATION_ENTRIES - 1)),
            { id: `e${entryCounter++}`, role: 'user', text: event.text, timestamp: Date.now() },
          ],
        }))
        break

      case 'assistant_response':
        set((s) => ({
          conversation: [
            ...s.conversation.slice(-(MAX_CONVERSATION_ENTRIES - 1)),
            { id: `e${entryCounter++}`, role: 'friday', text: event.text, timestamp: Date.now() },
          ],
        }))
        break

      case 'task_started':
        set((s) => ({ runningTasks: [...s.runningTasks.filter((t) => t.id !== event.task.id), event.task] }))
        break

      case 'task_completed':
        set((s) => ({
          runningTasks: s.runningTasks.filter((t) => t.id !== event.task.id),
          recentActivity: [event.task, ...s.recentActivity].slice(0, MAX_RECENT_ACTIVITY),
        }))
        break

      case 'system_stats': {
        const stats: SystemStats = {
          cpu: event.cpu,
          ram: event.ram,
          disk: event.disk,
          battery: event.battery,
          os: event.os,
          uptimeSeconds: event.uptime_seconds,
          networkMbps: event.network_mbps,
          microphone: event.microphone,
          speaker: event.speaker,
        }
        set((s) => ({
          systemStats: stats,
          systemStatsHistory: [...s.systemStatsHistory.slice(-(MAX_HISTORY_POINTS - 1)), stats],
        }))
        break
      }

      case 'audio_level':
        set({ audioLevel: event.level })
        break

      case 'tts_state':
        set({ ttsSpeaking: event.speaking })
        break

      case 'active_window':
        set({ activeWindow: { appName: event.app_name, title: event.title } })
        break

      case 'weather':
        set({
          weather: {
            city: event.city,
            region: event.region,
            country: event.country,
            temperatureC: event.temperature_c,
            humidity: event.humidity,
            windKmh: event.wind_kmh,
            condition: event.condition,
            weatherCode: event.weather_code,
          },
        })
        break

      case 'security_status':
        set({
          security: {
            defenderEnabled: event.defender_enabled,
            firewallEnabled: event.firewall_enabled,
            lastUpdateCheck: event.updates?.last_search ?? null,
            lastUpdateInstall: event.updates?.last_install ?? null,
          },
        })
        break

      case 'pipeline_stats':
        set({
          pipelineStats: {
            last_provider: event.last_provider,
            last_latency_ms: event.last_latency_ms,
            requests_handled: event.requests_handled,
            tool_calls_made: event.tool_calls_made,
            errors: event.errors,
          },
        })
        break

      case 'error':
        set({ lastError: event.message })
        break

      default:
        break
    }
  },

  clearConversation: () => set({ conversation: [] }),
}))

export function selectRunningTasks(state: FridayState) {
  return state.runningTasks
}
