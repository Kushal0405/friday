import { useEffect, useState } from 'react'
import { Menu } from 'lucide-react'
import { useFridayStore } from '../../stores/fridayStore'
import './TopBar.css'

function useClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const now = useClock()
  const voiceState = useFridayStore((s) => s.voiceState)

  const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const date = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <div className="top-bar">
      <button className="top-bar-menu" onClick={onMenuClick} aria-label="Menu">
        <Menu size={18} />
      </button>
      <div className="top-bar-brand">
        <div className="top-bar-brand-mark" />
        <div>
          <div className="top-bar-brand-name">FRIDAY</div>
          <div className="top-bar-brand-sub">Your Personal AI Assistant</div>
        </div>
      </div>
      <div className="top-bar-status">
        {voiceState === 'IDLE' ? 'Say "Friday" or press Ctrl+Alt+Space' : voiceState.replace('_', ' ')}
      </div>
      <div className="top-bar-clock">
        <div className="top-bar-time">{time}</div>
        <div className="top-bar-date">{date}</div>
      </div>
    </div>
  )
}
