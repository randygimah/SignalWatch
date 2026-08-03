import { INCIDENT_TYPES } from '../types'
import type { DashboardFilters } from '../types'

type FilterBarProps = {
  filters: DashboardFilters
  sensors: string[]
  frequencies: number[]
  onChange: (filters: DashboardFilters) => void
}

export function FilterBar({ filters, sensors, frequencies, onChange }: FilterBarProps) {
  const update = <Key extends keyof DashboardFilters>(key: Key, value: DashboardFilters[Key]) => {
    onChange({ ...filters, [key]: value })
  }

  return (
    <section className="filter-bar" aria-label="Dashboard filters">
      <label className="filter-field">
        <span>From (UTC)</span>
        <input type="datetime-local" value={filters.from} onChange={(event) => update('from', event.target.value)} />
      </label>
      <label className="filter-field">
        <span>To (UTC)</span>
        <input type="datetime-local" value={filters.to} onChange={(event) => update('to', event.target.value)} />
      </label>
      <label className="filter-field">
        <span>Sensor</span>
        <select value={filters.sensorId} onChange={(event) => update('sensorId', event.target.value)}>
          <option value="">All sensors</option>
          {sensors.map((sensor) => <option key={sensor} value={sensor}>{sensor}</option>)}
        </select>
      </label>
      <label className="filter-field">
        <span>Frequency</span>
        <select
          value={filters.frequencyMhz ?? ''}
          onChange={(event) => update('frequencyMhz', event.target.value ? Number(event.target.value) : null)}
        >
          <option value="">All channels</option>
          {frequencies.map((frequency) => <option key={frequency} value={frequency}>{frequency.toFixed(2)} MHz</option>)}
        </select>
      </label>
      <label className="filter-field">
        <span>Minimum severity</span>
        <select
          value={filters.minSeverity ?? ''}
          onChange={(event) => update('minSeverity', event.target.value ? Number(event.target.value) : null)}
        >
          <option value="">All severities</option>
          <option value="65">Medium · 65+</option>
          <option value="80">High · 80+</option>
          <option value="90">Critical · 90+</option>
        </select>
      </label>
      <label className="filter-field">
        <span>Incident type</span>
        <select value={filters.incidentType} onChange={(event) => update('incidentType', event.target.value)}>
          <option value="">All incident types</option>
          {INCIDENT_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
        </select>
      </label>
      <button
        className="reset-button"
        type="button"
        onClick={() => onChange({ from: '', to: '', sensorId: 'RX-NORTH', frequencyMhz: null, minSeverity: null, incidentType: '' })}
      >
        Reset
      </button>
    </section>
  )
}

