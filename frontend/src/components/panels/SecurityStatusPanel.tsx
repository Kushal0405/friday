import { CheckCircle2, ShieldAlert, XCircle } from 'lucide-react'
import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
import './SecurityStatusPanel.css'

function StatusIcon({ state }: { state: boolean | null }) {
  if (state === null) return <ShieldAlert size={13} className="sec-icon-unknown" />
  if (state) return <CheckCircle2 size={13} className="sec-icon-ok" />
  return <XCircle size={13} className="sec-icon-bad" />
}

function formatRelative(iso: string | null): string {
  if (!iso) return 'Unknown'
  const then = new Date(iso).getTime()
  const diffMs = Date.now() - then
  const hours = Math.floor(diffMs / 3_600_000)
  if (hours < 1) return 'Less than an hour ago'
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function SecurityStatusPanel() {
  const security = useFridayStore((s) => s.security)

  return (
    <Panel title="SECURITY STATUS">
      <div className="sec-rows">
        <div className="sec-row">
          <StatusIcon state={security?.defenderEnabled ?? null} />
          <span className="sec-name">Defender</span>
          <span className="sec-value">
            {security?.defenderEnabled === null || security?.defenderEnabled === undefined
              ? 'Unknown'
              : security.defenderEnabled
                ? 'Active'
                : 'Disabled'}
          </span>
        </div>
        <div className="sec-row">
          <StatusIcon state={security?.firewallEnabled ?? null} />
          <span className="sec-name">Firewall</span>
          <span className="sec-value">
            {security?.firewallEnabled === null || security?.firewallEnabled === undefined
              ? 'Unknown'
              : security.firewallEnabled
                ? 'Active'
                : 'Disabled'}
          </span>
        </div>
        <div className="sec-row">
          <StatusIcon state={security?.lastUpdateCheck != null} />
          <span className="sec-name">Last Update Check</span>
          <span className="sec-value">{formatRelative(security?.lastUpdateCheck ?? null)}</span>
        </div>
      </div>
    </Panel>
  )
}
