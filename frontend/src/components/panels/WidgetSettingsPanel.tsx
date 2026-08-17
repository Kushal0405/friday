import { WIDGET_DEFINITIONS } from '../../types/widgets'
import { useWidgetStore } from '../../stores/widgetStore'
import './WidgetSettingsPanel.css'

export function WidgetSettingsPanel() {
  const enabled = useWidgetStore((s) => s.enabled)
  const setEnabled = useWidgetStore((s) => s.setEnabled)

  return (
    <div className="widget-settings">
      <div className="widget-settings-intro">
        Choose which widgets appear on the home screen. Widgets marked "no live data source yet"
        show an honest empty state rather than invented numbers until that integration is built.
      </div>
      <div className="widget-settings-list">
        {WIDGET_DEFINITIONS.map((widget) => (
          <label key={widget.id} className="widget-settings-row">
            <input
              type="checkbox"
              checked={enabled[widget.id] ?? false}
              onChange={(e) => setEnabled(widget.id, e.target.checked)}
            />
            <div className="widget-settings-text">
              <div className="widget-settings-name">
                {widget.label}
                {!widget.hasRealDataSource && <span className="widget-settings-tag">no live data source yet</span>}
              </div>
              <div className="widget-settings-desc">{widget.description}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}
