import { motion } from 'framer-motion'
import { Mic } from 'lucide-react'
import { useFridayStore } from '../../stores/fridayStore'
import { fridaySocket } from '../../services/websocket'
import './MicControl.css'

export function MicControl() {
  const voiceState = useFridayStore((s) => s.voiceState)
  const audioLevel = useFridayStore((s) => s.audioLevel)
  const listening = voiceState === 'LISTENING'
  const busy = voiceState !== 'IDLE'
  const pulseScale = listening ? 1 + Math.min(audioLevel, 1) * 0.22 : 1

  function handleClick() {
    if (voiceState === 'IDLE') {
      fridaySocket.send({ type: 'manual_listen' })
    } else {
      fridaySocket.send({ type: 'cancel' })
    }
  }

  return (
    <div className="mic-control">
      <motion.button
        className={`mic-button ${listening ? 'mic-button-active' : ''} ${busy ? 'mic-button-busy' : ''}`}
        onClick={handleClick}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.92 }}
        animate={{ scale: pulseScale }}
        transition={{ scale: { type: 'spring', stiffness: 300, damping: 18 } }}
      >
        <Mic size={22} />
      </motion.button>
      <div className="mic-hint">
        {listening ? 'Listening…' : busy ? STATUS_HINTS[voiceState] ?? 'Working…' : 'Tap to speak'}
        <span className="mic-hint-sep"> • </span>Ctrl+Alt+Space
      </div>
    </div>
  )
}

const STATUS_HINTS: Partial<Record<string, string>> = {
  TRANSCRIBING: 'Transcribing…',
  THINKING: 'Thinking…',
  EXECUTING: 'Working…',
  SPEAKING: 'Speaking…',
}
