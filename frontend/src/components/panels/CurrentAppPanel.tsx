import { AppWindow } from 'lucide-react'
import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
import './CurrentAppPanel.css'

export function CurrentAppPanel() {
  const activeWindow = useFridayStore((s) => s.activeWindow)

  return (
    <Panel title="CURRENT APP">
      <div className="current-app">
        <div className="current-app-icon">
          <AppWindow size={20} />
        </div>
        <div className="current-app-info">
          <div className="current-app-name">{activeWindow?.appName ?? 'Unknown'}</div>
          <div className="current-app-title">{activeWindow?.title || 'No window focused'}</div>
        </div>
      </div>
    </Panel>
  )
}
