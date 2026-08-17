import { Battery, Mic, Speaker, Wifi } from 'lucide-react'
import { Panel } from '../common/Panel'
import { LiveBadge } from '../common/LiveBadge'
import { useFridayStore } from '../../stores/fridayStore'
import './SystemStatusPanel.css'

function Gauge({ label, value, color }: { label: string; value: number; color: string }) {
  const circumference = 2 * Math.PI * 20
  const offset = circumference - (value / 100) * circumference
  return (
    <div className="gauge">
      <svg width="52" height="52" viewBox="0 0 52 52">
        <circle cx="26" cy="26" r="20" className="gauge-track" />
        <circle
          cx="26"
          cy="26"
          r="20"
          stroke={color}
          strokeWidth="4"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 26 26)"
          className="gauge-value"
        />
      </svg>
      <div className="gauge-label">
        <span className="gauge-pct">{Math.round(value)}%</span>
        <span className="gauge-name">{label}</span>
      </div>
    </div>
  )
}

export function SystemStatusPanel() {
  const stats = useFridayStore((s) => s.systemStats)

  return (
    <Panel title="SYSTEM STATUS" badge={<LiveBadge />}>
      <div className="gauge-grid">
        <Gauge label="CPU" value={stats?.cpu ?? 0} color="#4fb4ff" />
        <Gauge label="RAM" value={stats?.ram ?? 0} color="#ff9a4f" />
        <Gauge label="DISK" value={stats?.disk ?? 0} color="#ffb84f" />
      </div>
      <div className="status-rows">
        <div className="status-row">
          <span className="status-icon"><Wifi size={13} /></span>
          <span className="status-name">Network</span>
          <span className="status-value">
            {stats?.networkMbps != null ? `${stats.networkMbps.toFixed(1)} Mbps` : '—'}
          </span>
        </div>
        <div className="status-row">
          <span className="status-icon"><Battery size={13} /></span>
          <span className="status-name">Battery</span>
          <span className="status-value">{stats?.battery != null ? `${stats.battery}%` : 'N/A'}</span>
        </div>
        <div className="status-row">
          <span className="status-icon"><Mic size={13} /></span>
          <span className="status-name">Microphone</span>
          <span className="status-value">{stats?.microphone ?? 'Not detected'}</span>
        </div>
        <div className="status-row">
          <span className="status-icon"><Speaker size={13} /></span>
          <span className="status-name">Speaker</span>
          <span className="status-value">{stats?.speaker ?? 'Not detected'}</span>
        </div>
      </div>
    </Panel>
  )
}
