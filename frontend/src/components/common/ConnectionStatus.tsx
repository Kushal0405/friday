import { useConnectionStore } from '../../stores/connectionStore'
import './ConnectionStatus.css'

export function ConnectionStatus() {
  const connected = useConnectionStore((s) => s.connected)

  return (
    <div className="connection-status">
      <span className={`dot ${connected ? 'connected' : 'disconnected'}`} />
      <span>{connected ? 'BACKEND CONNECTED' : 'RECONNECTING…'}</span>
    </div>
  )
}
