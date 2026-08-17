import { Cpu, Gauge as GaugeIcon, MessageSquare, Wrench } from 'lucide-react'
import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
import './AiPipelinePanel.css'

const PROVIDER_LABELS: Record<string, string> = {
  OpenAICompatibleProvider: 'Ollama',
  AnthropicCLIProvider: 'Claude',
}

export function AiPipelinePanel() {
  const stats = useFridayStore((s) => s.pipelineStats)
  const providerLabel = stats?.last_provider ? PROVIDER_LABELS[stats.last_provider] ?? stats.last_provider : '—'

  return (
    <Panel title="AI PIPELINE" badge={<span className="pipeline-online">ONLINE</span>}>
      <div className="pipeline-rows">
        <div className="pipeline-row">
          <span className="pipeline-icon"><Cpu size={13} /></span>
          <span className="pipeline-name">Last Provider</span>
          <span className="pipeline-value">{providerLabel}</span>
        </div>
        <div className="pipeline-row">
          <span className="pipeline-icon"><GaugeIcon size={13} /></span>
          <span className="pipeline-name">Latency</span>
          <span className="pipeline-value">
            {stats?.last_latency_ms != null ? `${stats.last_latency_ms} ms` : '—'}
          </span>
        </div>
        <div className="pipeline-row">
          <span className="pipeline-icon"><MessageSquare size={13} /></span>
          <span className="pipeline-name">Requests</span>
          <span className="pipeline-value">{stats?.requests_handled ?? 0}</span>
        </div>
        <div className="pipeline-row">
          <span className="pipeline-icon"><Wrench size={13} /></span>
          <span className="pipeline-name">Tool Calls</span>
          <span className="pipeline-value">{stats?.tool_calls_made ?? 0}</span>
        </div>
      </div>
    </Panel>
  )
}
