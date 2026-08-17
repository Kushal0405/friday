export type WidgetId =
  | 'systemStatus'
  | 'aiPipeline'
  | 'currentApp'
  | 'weather'
  | 'securityStatus'
  | 'resourceMonitor'
  | 'upcoming'
  | 'quickActions'
  | 'recentActivity'
  | 'conversation'
  | 'runningTasks'

export interface WidgetDefinition {
  id: WidgetId
  label: string
  description: string
  hasRealDataSource: boolean
  defaultEnabled: boolean
}

export const WIDGET_DEFINITIONS: WidgetDefinition[] = [
  {
    id: 'systemStatus',
    label: 'System Status',
    description: 'Live CPU, RAM, disk, battery, network, mic and speaker state.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'aiPipeline',
    label: 'AI Pipeline',
    description: 'Which AI provider last answered, response latency, tool-call count.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'currentApp',
    label: 'Current App',
    description: 'The application currently focused on your desktop.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'weather',
    label: 'Weather',
    description: 'Current conditions for your approximate location (via IP geolocation).',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'securityStatus',
    label: 'Security Status',
    description: 'Real Windows Defender and Firewall status, last update check.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'resourceMonitor',
    label: 'Resource Monitor',
    description: 'CPU/RAM/disk history graph.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'upcoming',
    label: 'Upcoming Events',
    description: 'Calendar integration is not wired up yet — no real data source.',
    hasRealDataSource: false,
    defaultEnabled: false,
  },
  {
    id: 'quickActions',
    label: 'Quick Actions',
    description: 'One-tap shortcuts for common commands.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'recentActivity',
    label: 'Recent Activity',
    description: 'Recently completed tasks.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'conversation',
    label: 'Conversation',
    description: 'Live transcript and FRIDAY responses.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
  {
    id: 'runningTasks',
    label: 'Running Tasks',
    description: 'Tasks currently in progress.',
    hasRealDataSource: true,
    defaultEnabled: true,
  },
]
