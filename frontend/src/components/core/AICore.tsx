import { AnimatePresence, motion } from 'framer-motion'
import { useFridayStore } from '../../stores/fridayStore'
import './AICore.css'

const STATE_LABELS: Record<string, string> = {
  IDLE: 'READY',
  WAKE_DETECTED: 'WAKE DETECTED',
  LISTENING: 'LISTENING',
  TRANSCRIBING: 'TRANSCRIBING',
  THINKING: 'THINKING',
  EXECUTING: 'EXECUTING',
  SPEAKING: 'SPEAKING',
  ERROR: 'ERROR',
  CANCELLED: 'CANCELLED',
}

const TICK_COUNT = 60

export function AICore() {
  const voiceState = useFridayStore((s) => s.voiceState)
  const label = STATE_LABELS[voiceState] ?? voiceState

  return (
    <div className={`ai-core ai-core-${voiceState.toLowerCase()}`}>
      <AnimatePresence mode="wait">
        {label && (
          <motion.div
            key={label}
            className="ai-core-state-pill"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 6 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            {label}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        className="ai-core-ticks"
        animate={{ rotate: 360 }}
        transition={{ duration: 90, repeat: Infinity, ease: 'linear' }}
      >
        {Array.from({ length: TICK_COUNT }).map((_, i) => (
          <span key={i} style={{ transform: `rotate(${(360 / TICK_COUNT) * i}deg)` }} />
        ))}
      </motion.div>

      <motion.div
        className="ai-core-ring ai-core-ring-outer"
        animate={
          voiceState === 'THINKING'
            ? { rotate: 360 }
            : voiceState === 'IDLE'
              ? { scale: [1, 1.03, 1] }
              : {}
        }
        transition={
          voiceState === 'THINKING'
            ? { duration: 3, repeat: Infinity, ease: 'linear' }
            : { duration: 3.2, repeat: Infinity, ease: 'easeInOut' }
        }
      />
      <motion.div
        className="ai-core-ring ai-core-ring-dashed"
        animate={{ rotate: -360 }}
        transition={{ duration: 14, repeat: Infinity, ease: 'linear' }}
      />
      <motion.div
        className="ai-core-ring ai-core-ring-mid"
        animate={
          voiceState === 'THINKING'
            ? { rotate: -360 }
            : voiceState === 'LISTENING'
              ? { scale: [1, 1.08, 1] }
              : voiceState === 'SPEAKING'
                ? { scale: [1, 1.05, 0.98, 1.05, 1] }
                : {}
        }
        transition={
          voiceState === 'THINKING'
            ? { duration: 4.5, repeat: Infinity, ease: 'linear' }
            : voiceState === 'SPEAKING'
              ? { duration: 0.9, repeat: Infinity, ease: 'easeInOut' }
              : { duration: 1.4, repeat: Infinity, ease: 'easeInOut' }
        }
      />
      <div className="ai-core-inner-glow" />
      <div className="ai-core-orbit-dot ai-core-orbit-dot-a" />
      <div className="ai-core-orbit-dot ai-core-orbit-dot-b" />
      <div className="ai-core-label">FRIDAY</div>
      <AnimatePresence mode="wait">
        <motion.div
          key={label}
          className="ai-core-status"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {label}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
