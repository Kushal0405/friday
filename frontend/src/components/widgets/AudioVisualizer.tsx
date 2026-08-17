import { useFridayStore } from '../../stores/fridayStore'
import './AudioVisualizer.css'

const BAR_COUNT = 48

export function AudioVisualizer() {
  const voiceState = useFridayStore((s) => s.voiceState)
  const audioLevel = useFridayStore((s) => s.audioLevel)
  const active = voiceState === 'LISTENING' || voiceState === 'SPEAKING'

  return (
    <div className={`audio-viz ${active ? 'audio-viz-active' : ''}`}>
      {Array.from({ length: BAR_COUNT }).map((_, i) => {
        const mid = BAR_COUNT / 2
        const distanceFromMid = Math.abs(i - mid) / mid
        const baseHeight = active ? (1 - distanceFromMid * 0.6) * audioLevel : 0.06
        return (
          <span
            key={i}
            className="audio-viz-bar"
            style={{ height: `${Math.max(4, baseHeight * 40)}px` }}
          />
        )
      })}
    </div>
  )
}
