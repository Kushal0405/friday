import { WidgetSettingsPanel } from '../components/panels/WidgetSettingsPanel'
import './SettingsLayout.css'

export function SettingsLayout() {
  return (
    <div className="settings-layout">
      <h2 className="settings-heading">Widgets</h2>
      <WidgetSettingsPanel />
    </div>
  )
}
