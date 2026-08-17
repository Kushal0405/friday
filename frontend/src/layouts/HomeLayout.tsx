import { AICore } from '../components/core/AICore'
import { AudioVisualizer } from '../components/widgets/AudioVisualizer'
import { MicControl } from '../components/widgets/MicControl'
import { TextInput } from '../components/common/TextInput'
import { SystemStatusPanel } from '../components/panels/SystemStatusPanel'
import { AiPipelinePanel } from '../components/panels/AiPipelinePanel'
import { CurrentAppPanel } from '../components/panels/CurrentAppPanel'
import { QuickActionsPanel } from '../components/panels/QuickActionsPanel'
import { WeatherPanel } from '../components/panels/WeatherPanel'
import { SecurityStatusPanel } from '../components/panels/SecurityStatusPanel'
import { ResourceMonitorPanel } from '../components/panels/ResourceMonitorPanel'
import { UpcomingPanel } from '../components/panels/UpcomingPanel'
import { ConversationPanel } from '../components/panels/ConversationPanel'
import { RunningTasksPanel } from '../components/panels/RunningTasksPanel'
import { RecentActivityPanel } from '../components/panels/RecentActivityPanel'
import { useWidgetStore } from '../stores/widgetStore'
import './HomeLayout.css'

export function HomeLayout() {
  const isEnabled = useWidgetStore((s) => s.isEnabled)

  return (
    <div className="home-layout">
      <div className="home-column home-column-left">
        {isEnabled('systemStatus') && <SystemStatusPanel />}
        {isEnabled('aiPipeline') && <AiPipelinePanel />}
        {isEnabled('currentApp') && <CurrentAppPanel />}
        {isEnabled('quickActions') && <QuickActionsPanel />}
      </div>

      <div className="home-column home-column-center">
        <div className="home-center-top">
          <AICore />
        </div>
        <AudioVisualizer />
        <MicControl />
        <TextInput />
        <div className="home-center-bottom">
          {isEnabled('recentActivity') && <RecentActivityPanel />}
        </div>
      </div>

      <div className="home-column home-column-right">
        {isEnabled('weather') && <WeatherPanel />}
        {isEnabled('securityStatus') && <SecurityStatusPanel />}
        {isEnabled('resourceMonitor') && <ResourceMonitorPanel />}
        {isEnabled('upcoming') && <UpcomingPanel />}
        {isEnabled('conversation') && <ConversationPanel />}
        {isEnabled('runningTasks') && <RunningTasksPanel />}
      </div>
    </div>
  )
}
