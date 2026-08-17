import { Mic } from 'lucide-react'
import { useFridayStore } from '../../stores/fridayStore'
import { fridaySocket } from '../../services/websocket'
import './MicControl.css'

export function MicControl() {
  const voiceState = useFridayStore((s) => s.voiceState)
  const listening = voiceState === 'LISTENING'
  const busy = voiceState !== 'IDLE'

  function handleClick() {
    if (voiceState === 'IDLE') {
      fridaySocket.send({ type: 'manual_listen' })
    } else {
      fridaySocket.send({ type: 'cancel' })
    }
  }

  return (
    <div className="mic-control">
      <button
        className={`mic-button ${listening ? 'mic-button-active' : ''} ${busy ? 'mic-button-busy' : ''}`}
        onClick={handleClick}
      >
        <Mic size={22} />
      </button>
      <div className="mic-hint">Tap to speak &nbsp;•&nbsp; Press Ctrl+Alt+Space</div>
    </div>
  )
}
