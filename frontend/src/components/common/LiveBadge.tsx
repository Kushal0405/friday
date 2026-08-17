import './LiveBadge.css'

export function LiveBadge({ label = 'LIVE' }: { label?: string }) {
  return (
    <span className="live-badge">
      <span className="live-dot" />
      {label}
    </span>
  )
}
