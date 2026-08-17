import type { ReactNode } from 'react'
import './Panel.css'

interface PanelProps {
  title: string
  badge?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function Panel({ title, badge, action, children, className }: PanelProps) {
  return (
    <div className={`panel ${className ?? ''}`}>
      <div className="panel-header">
        <span className="panel-title">{title}</span>
        {badge}
        {action && <span className="panel-action">{action}</span>}
      </div>
      <div className="panel-body">{children}</div>
    </div>
  )
}
