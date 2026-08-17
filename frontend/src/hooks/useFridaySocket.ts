import { useEffect } from 'react'
import { fridaySocket } from '../services/websocket'
import { useConnectionStore } from '../stores/connectionStore'
import { useFridayStore } from '../stores/fridayStore'
import type { ServerEvent } from '../types/events'

export function useFridaySocket(onEvent?: (event: ServerEvent) => void): void {
  const setConnected = useConnectionStore((s) => s.setConnected)

  useEffect(() => {
    fridaySocket.connect()
    const offStatus = fridaySocket.onStatus((connected) => {
      setConnected(connected)
      if (!connected) {
        // Without this, a dropped connection (backend restart, network
        // blip) leaves the UI showing whatever voice state it last saw. The
        // backend now also resends the true state on reconnect, but resetting
        // here too means the mic button can't act on stale state in the gap
        // before that resend arrives — e.g. sending "cancel" for a state the
        // backend has already left, silently swallowing the next click.
        useFridayStore.setState({ voiceState: 'IDLE' })
      }
    })
    const offEvent = onEvent ? fridaySocket.onEvent(onEvent) : undefined

    return () => {
      offStatus()
      offEvent?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}
