import { useState } from 'react'
import { TitleBar } from './components/common/TitleBar'
import { TopBar } from './components/navigation/TopBar'
import { BottomNav, type NavSection } from './components/navigation/BottomNav'
import { HomeLayout } from './layouts/HomeLayout'
import { SettingsLayout } from './layouts/SettingsLayout'
import { useFridaySocket } from './hooks/useFridaySocket'
import { useFridayStore } from './stores/fridayStore'
import { useConnectionStore } from './stores/connectionStore'
import './App.css'

function ComingSoon({ label }: { label: string }) {
  return <div className="coming-soon">{label} — coming in a later phase.</div>
}

function App() {
  const [section, setSection] = useState<NavSection>('home')
  const applyEvent = useFridayStore((s) => s.applyEvent)
  const connected = useConnectionStore((s) => s.connected)

  useFridaySocket(applyEvent)

  return (
    <div className="app-shell">
      <TitleBar />
      <TopBar onMenuClick={() => setSection('settings')} />
      {!connected && <div className="reconnect-banner">Reconnecting to FRIDAY backend…</div>}
      <div className="app-content">
        {section === 'home' && <HomeLayout />}
        {section === 'settings' && <SettingsLayout />}
        {section === 'apps' && <ComingSoon label="Applications" />}
        {section === 'files' && <ComingSoon label="Files" />}
        {section === 'system' && <ComingSoon label="System" />}
      </div>
      <BottomNav active={section} onSelect={setSection} onPower={() => window.friday.windowClose()} />
    </div>
  )
}

export default App
