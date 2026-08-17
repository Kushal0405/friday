import { Panel } from '../common/Panel'
import './UpcomingPanel.css'

export function UpcomingPanel() {
  return (
    <Panel title="UPCOMING">
      <div className="upcoming-empty">
        Calendar isn't connected yet. Enable this in a future update once FRIDAY supports calendar access.
      </div>
    </Panel>
  )
}
