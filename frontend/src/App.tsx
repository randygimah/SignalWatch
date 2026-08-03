import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

import { getAnomalies, getHeatmap, getIncident, getObservations, getOverview } from './api'
import { AnomalyHeatmap } from './components/AnomalyHeatmap'
import { FilterBar } from './components/FilterBar'
import { IncidentDrawer } from './components/IncidentDrawer'
import { IncidentList } from './components/IncidentList'
import { SignalTimeline } from './components/SignalTimeline'
import { SummaryCards } from './components/SummaryCards'
import type { DashboardFilters } from './types'

const initialFilters: DashboardFilters = {
  from: '',
  to: '',
  sensorId: 'RX-NORTH',
  frequencyMhz: null,
  minSeverity: null,
  incidentType: '',
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'The analysis service could not complete this request.'
}

export default function App() {
  const [filters, setFilters] = useState(initialFilters)
  const [metric, setMetric] = useState('noise_floor_dbm')
  const [focusFrequency, setFocusFrequency] = useState(433.05)
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null)

  const timelineFilters = useMemo(
    () => ({ ...filters, frequencyMhz: filters.frequencyMhz ?? focusFrequency }),
    [filters, focusFrequency],
  )

  const overview = useQuery({ queryKey: ['overview', filters], queryFn: () => getOverview(filters) })
  const observations = useQuery({
    queryKey: ['observations', timelineFilters, metric],
    queryFn: () => getObservations(timelineFilters, metric),
  })
  const anomalies = useQuery({ queryKey: ['anomalies', filters], queryFn: () => getAnomalies(filters) })
  const heatmap = useQuery({ queryKey: ['heatmap', filters], queryFn: () => getHeatmap(filters) })
  const incident = useQuery({
    queryKey: ['incident', selectedIncidentId],
    queryFn: () => getIncident(selectedIncidentId!),
    enabled: selectedIncidentId !== null,
  })

  useEffect(() => {
    if (filters.frequencyMhz !== null) setFocusFrequency(filters.frequencyMhz)
  }, [filters.frequencyMhz])

  useEffect(() => {
    setSelectedIncidentId(null)
  }, [filters])

  const errors = [overview.error, observations.error, anomalies.error, heatmap.error].filter(Boolean)
  const isRefreshing = overview.isFetching || observations.isFetching || anomalies.isFetching || heatmap.isFetching
  const availableSensors = observations.data?.meta.available_sensors ?? ['RX-CENTRAL', 'RX-NORTH', 'RX-SOUTH']
  const availableFrequencies = observations.data?.meta.available_frequencies_mhz ?? [433.05, 433.3, 433.55, 433.8, 434.05, 434.3, 434.55, 434.8]

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
          <div>
            <h1>SignalWatch</h1>
            <p>RF anomaly intelligence</p>
          </div>
        </div>
        <div className={`service-status ${isRefreshing ? 'service-status--busy' : ''}`}>
          <span aria-hidden="true" />
          {isRefreshing ? 'Refreshing analysis' : 'Analysis ready'}
        </div>
      </header>

      <main className="dashboard">
        <div className="page-intro">
          <div>
            <span className="eyebrow">Spectrum operations</span>
            <h2>RF anomaly overview</h2>
            <p>See what changed, how severe it is, and which signal dimensions drove the alert.</p>
          </div>
          <div className="batch-stamp">
            <span>Analysis window</span>
            <strong>08–14 Jul 2026 · UTC</strong>
          </div>
        </div>

        <FilterBar
          filters={filters}
          sensors={availableSensors}
          frequencies={availableFrequencies}
          onChange={setFilters}
        />

        {errors.length > 0 && (
          <div className="error-banner" role="alert">
            <strong>Some analysis could not be loaded.</strong>
            <span>{errorMessage(errors[0])}</span>
          </div>
        )}

        <SummaryCards overview={overview.data} loading={overview.isPending} />

        <div className="analysis-grid">
          <SignalTimeline
            points={observations.data?.items ?? []}
            loading={observations.isPending}
            metric={metric}
            focusFrequency={focusFrequency}
            frequencies={availableFrequencies}
            frequencyLocked={filters.frequencyMhz !== null}
            downsampled={observations.data?.meta.downsampled ?? false}
            onMetricChange={setMetric}
            onFocusFrequencyChange={setFocusFrequency}
            onSelectIncident={setSelectedIncidentId}
          />
          <IncidentList
            incidents={anomalies.data?.items ?? []}
            total={anomalies.data?.total ?? 0}
            loading={anomalies.isPending}
            selectedId={selectedIncidentId}
            onSelect={setSelectedIncidentId}
          />
        </div>

        <AnomalyHeatmap
          cells={heatmap.data?.cells ?? []}
          loading={heatmap.isPending}
          onSelectIncident={setSelectedIncidentId}
        />
      </main>

      {selectedIncidentId && (
        <IncidentDrawer
          incident={incident.data}
          loading={incident.isPending}
          error={incident.error ? errorMessage(incident.error) : null}
          onClose={() => setSelectedIncidentId(null)}
        />
      )}
    </div>
  )
}

