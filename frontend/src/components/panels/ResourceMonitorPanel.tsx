import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
import type { SystemStats } from '../../stores/fridayStore'
import './ResourceMonitorPanel.css'

function sparklinePath(values: number[], width: number, height: number): string {
  if (values.length < 2) return ''
  const step = width / (values.length - 1)
  return values
    .map((v, i) => {
      const x = i * step
      const y = height - (v / 100) * height
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

function Sparkline({ values, color }: { values: number[]; color: string }) {
  const width = 100
  const height = 28
  const path = sparklinePath(values, width, height)
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="sparkline" preserveAspectRatio="none">
      {path && <path d={path} stroke={color} strokeWidth="1.5" fill="none" />}
    </svg>
  )
}

function ResourceRow({
  label,
  value,
  history,
  color,
  extractor,
}: {
  label: string
  value: number
  history: SystemStats[]
  color: string
  extractor: (s: SystemStats) => number
}) {
  return (
    <div className="resource-row">
      <div className="resource-header">
        <span className="resource-label">{label}</span>
        <span className="resource-value">{Math.round(value)}%</span>
      </div>
      <Sparkline values={history.map(extractor)} color={color} />
    </div>
  )
}

export function ResourceMonitorPanel() {
  const stats = useFridayStore((s) => s.systemStats)
  const history = useFridayStore((s) => s.systemStatsHistory)

  return (
    <Panel title="RESOURCE MONITOR">
      <div className="resource-rows">
        <ResourceRow label="CPU" value={stats?.cpu ?? 0} history={history} color="#4fb4ff" extractor={(s) => s.cpu} />
        <ResourceRow label="RAM" value={stats?.ram ?? 0} history={history} color="#ff9a4f" extractor={(s) => s.ram} />
        <ResourceRow label="DISK" value={stats?.disk ?? 0} history={history} color="#ffb84f" extractor={(s) => s.disk} />
      </div>
    </Panel>
  )
}
