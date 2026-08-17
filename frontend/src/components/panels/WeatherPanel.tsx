import { Cloud, CloudRain, CloudSnow, Sun, Zap } from 'lucide-react'
import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
import './WeatherPanel.css'

function conditionIcon(code: number | undefined) {
  if (code === undefined) return <Cloud size={28} />
  if (code === 0 || code === 1) return <Sun size={28} />
  if (code >= 51 && code <= 82) return <CloudRain size={28} />
  if (code >= 71 && code <= 75) return <CloudSnow size={28} />
  if (code >= 95) return <Zap size={28} />
  return <Cloud size={28} />
}

export function WeatherPanel() {
  const weather = useFridayStore((s) => s.weather)

  if (!weather) {
    return (
      <Panel title="WEATHER">
        <div className="weather-empty">Fetching location…</div>
      </Panel>
    )
  }

  return (
    <Panel title="WEATHER">
      <div className="weather-location">{weather.city}</div>
      <div className="weather-main">
        <span className="weather-icon">{conditionIcon(weather.weatherCode)}</span>
        <span className="weather-temp">{Math.round(weather.temperatureC)}°C</span>
      </div>
      <div className="weather-condition">{weather.condition}</div>
      <div className="weather-details">
        <div>
          <span className="weather-detail-label">Humidity</span>
          <span className="weather-detail-value">{weather.humidity}%</span>
        </div>
        <div>
          <span className="weather-detail-label">Wind</span>
          <span className="weather-detail-value">{weather.windKmh} km/h</span>
        </div>
      </div>
    </Panel>
  )
}
