import { Minus, Square, X } from 'lucide-react'
import './TitleBar.css'

export function TitleBar() {
  return (
    <div className="title-bar">
      <div className="title-bar-label">FRIDAY</div>
      <div className="title-bar-controls">
        <button onClick={() => window.friday.windowMinimize()} aria-label="Minimize">
          <Minus size={14} />
        </button>
        <button onClick={() => window.friday.windowMaximize()} aria-label="Maximize">
          <Square size={12} />
        </button>
        <button onClick={() => window.friday.windowClose()} aria-label="Close" className="close">
          <X size={14} />
        </button>
      </div>
    </div>
  )
}
