import { Chrome, Gauge, AppWindow } from 'lucide-react'
import { Panel } from '../common/Panel'
import { fridaySocket } from '../../services/websocket'
import './QuickActionsPanel.css'

interface QuickAction {
  id: string
  label: string
  icon: React.ReactNode
  command: string
}

// Only wired to tools that exist today (Phase 3). Browser/Screenshot/File/
// Volume actions will be added here once their tools are built (Phase 4) —
// no point offering a button whose command the AI has no tool to fulfill.
const ACTIONS: QuickAction[] = [
  { id: 'open-chrome', label: 'Open Chrome', icon: <Chrome size={16} />, command: 'Open Chrome' },
  { id: 'system', label: 'System Info', icon: <Gauge size={16} />, command: "What's my system status?" },
  { id: 'active-window', label: 'Active Window', icon: <AppWindow size={16} />, command: 'What app is currently active?' },
]

export function QuickActionsPanel() {
  function run(command: string) {
    fridaySocket.send({ type: 'user_text', text: command })
  }

  return (
    <Panel title="QUICK ACTIONS">
      <div className="quick-actions-grid">
        {ACTIONS.map((action) => (
          <button key={action.id} className="quick-action" onClick={() => run(action.command)}>
            <span className="quick-action-icon">{action.icon}</span>
            <span className="quick-action-label">{action.label}</span>
          </button>
        ))}
      </div>
    </Panel>
  )
}
