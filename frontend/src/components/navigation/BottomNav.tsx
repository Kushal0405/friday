import { Home, Grid3x3, FolderCog, Cpu, Settings, Power } from 'lucide-react'
import './BottomNav.css'

export type NavSection = 'home' | 'apps' | 'files' | 'system' | 'settings'

interface BottomNavProps {
  active: NavSection
  onSelect: (section: NavSection) => void
  onPower: () => void
}

const ITEMS: { id: NavSection; label: string; icon: React.ReactNode }[] = [
  { id: 'home', label: 'Home', icon: <Home size={16} /> },
  { id: 'apps', label: 'Apps', icon: <Grid3x3 size={16} /> },
  { id: 'files', label: 'Files', icon: <FolderCog size={16} /> },
  { id: 'system', label: 'System', icon: <Cpu size={16} /> },
  { id: 'settings', label: 'Settings', icon: <Settings size={16} /> },
]

export function BottomNav({ active, onSelect, onPower }: BottomNavProps) {
  return (
    <div className="bottom-nav">
      {ITEMS.slice(0, 3).map((item) => (
        <button
          key={item.id}
          className={`bottom-nav-item ${active === item.id ? 'active' : ''}`}
          onClick={() => onSelect(item.id)}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
      <div className="bottom-nav-spacer" />
      {ITEMS.slice(3).map((item) => (
        <button
          key={item.id}
          className={`bottom-nav-item ${active === item.id ? 'active' : ''}`}
          onClick={() => onSelect(item.id)}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
      <button className="bottom-nav-item bottom-nav-power" onClick={onPower}>
        <Power size={16} />
      </button>
    </div>
  )
}
