import { CheckCircle2, XCircle } from 'lucide-react'
import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
import './RecentActivityPanel.css'

function timeAgo(iso: string | null): string {
  if (!iso) return ''
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diffMs / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hours = Math.floor(mins / 60)
  return `${hours}h ago`
}

export function RecentActivityPanel() {
  const recentActivity = useFridayStore((s) => s.recentActivity)

  return (
    <Panel title="RECENT ACTIVITY">
      {recentActivity.length === 0 ? (
        <div className="recent-empty">No activity yet.</div>
      ) : (
        <div className="recent-list">
          {recentActivity.map((task) => (
            <div key={task.id} className="recent-item">
              {task.status === 'COMPLETED' ? (
                <CheckCircle2 size={13} className="recent-icon-ok" />
              ) : (
                <XCircle size={13} className="recent-icon-bad" />
              )}
              <div className="recent-info">
                <div className="recent-name">{task.name}</div>
                <div className="recent-time">{timeAgo(task.completedAt)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}
