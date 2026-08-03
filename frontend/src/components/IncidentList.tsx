import type { IncidentSummary } from '../types'

type IncidentListProps = {
  incidents: IncidentSummary[]
  total: number
  loading: boolean
  selectedId: string | null
  onSelect: (incidentId: string) => void
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  }).format(new Date(value))
}

export function IncidentList({ incidents, total, loading, selectedId, onSelect }: IncidentListProps) {
  return (
    <section className="panel incident-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Ranked by severity</span>
          <h2>Top incidents</h2>
        </div>
        <span className="count-badge">{total}</span>
      </div>
      <div className="incident-list">
        {loading && Array.from({ length: 5 }, (_, index) => <div className="incident-skeleton skeleton" key={index} />)}
        {!loading && incidents.length === 0 && <div className="empty-state">No incidents match these filters.</div>}
        {incidents.map((incident) => (
          <button
            type="button"
            className={`incident-row ${selectedId === incident.incident_id ? 'incident-row--selected' : ''}`}
            key={incident.incident_id}
            onClick={() => onSelect(incident.incident_id)}
          >
            <span className={`score-box score-box--${incident.severity}`}>{Math.round(incident.severity_score)}</span>
            <span className="incident-row__body">
              <strong>{incident.title}</strong>
              <span>{incident.sensor_id} · {formatTime(incident.start_time)} UTC</span>
              <small>{incident.affected_frequencies.length} channel{incident.affected_frequencies.length === 1 ? '' : 's'} · {incident.duration_minutes} min</small>
            </span>
            <span className="chevron" aria-hidden="true">›</span>
          </button>
        ))}
      </div>
    </section>
  )
}

