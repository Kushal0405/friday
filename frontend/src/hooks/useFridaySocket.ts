import { useEffect } from 'react'
import { fridaySocket } from '../services/websocket'
import { useConnectionStore } from '../stores/connectionStore'
import type { ServerEvent } from '../types/events'

export function useFridaySocket(onEvent?: (event: ServerEvent) => void): void {
  const setConnected = useConnectionStore((s) => s.setConnected)

  useEffect(() => {
    fridaySocket.connect()
    const offStatus = fridaySocket.onStatus(setConnected)
    const offEvent = onEvent ? fridaySocket.onEvent(onEvent) : undefined

    return () => {
      offStatus()
      offEvent?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}
