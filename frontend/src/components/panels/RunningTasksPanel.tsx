import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
import './RunningTasksPanel.css'

export function RunningTasksPanel() {
  const runningTasks = useFridayStore((s) => s.runningTasks)

  return (
    <Panel
      title="RUNNING TASKS"
      badge={runningTasks.length > 0 ? <span className="running-count">{runningTasks.length} Active</span> : undefined}
    >
      {runningTasks.length === 0 ? (
        <div className="running-empty">No tasks running.</div>
      ) : (
        <div className="running-list">
          {runningTasks.map((task) => (
            <div key={task.id} className="running-item">
              <div className="running-name">{task.name}</div>
              <div className="running-bar-track">
                <div className="running-bar-fill" />
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}
