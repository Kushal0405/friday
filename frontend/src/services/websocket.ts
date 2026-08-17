import type { ClientEvent, ServerEvent } from '../types/events'

type Listener = (event: ServerEvent) => void
type StatusListener = (connected: boolean) => void

const MIN_BACKOFF_MS = 500
const MAX_BACKOFF_MS = 10_000

class FridaySocket {
  private ws: WebSocket | null = null
  private url: string | null = null
  private listeners = new Set<Listener>()
  private statusListeners = new Set<StatusListener>()
  private backoff = MIN_BACKOFF_MS
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private closedByClient = false

  async connect(): Promise<void> {
    const config = await window.friday.getBackendConfig()
    this.url = `ws://${config.host}:${config.port}/ws/friday`
    this.closedByClient = false
    this.open()
  }

  private open(): void {
    if (!this.url) return
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }
    const socket = new WebSocket(this.url)

    socket.onopen = () => {
      this.backoff = MIN_BACKOFF_MS
      this.statusListeners.forEach((cb) => cb(true))
    }

    socket.onmessage = (msg) => {
      try {
        const parsed = JSON.parse(msg.data) as ServerEvent
        this.listeners.forEach((cb) => cb(parsed))
      } catch {
        // ignore malformed frames
      }
    }

    socket.onclose = () => {
      this.statusListeners.forEach((cb) => cb(false))
      if (!this.closedByClient) this.scheduleReconnect()
    }

    socket.onerror = () => {
      socket.close()
    }

    this.ws = socket
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.backoff = Math.min(this.backoff * 1.7, MAX_BACKOFF_MS)
      this.open()
    }, this.backoff)
  }

  send(event: ClientEvent): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(event))
    }
  }

  onEvent(listener: Listener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  onStatus(listener: StatusListener): () => void {
    this.statusListeners.add(listener)
    return () => this.statusListeners.delete(listener)
  }

  disconnect(): void {
    this.closedByClient = true
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
  }
}

export const fridaySocket = new FridaySocket()
