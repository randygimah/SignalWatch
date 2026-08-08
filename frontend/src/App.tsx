import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

import { ApiError, getAnomalies, getHeatmap, getIncident, getObservations, getOverview } from './api'
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

  const dashboardQueries = [overview, observations, anomalies, heatmap]
  const errors = dashboardQueries.map((query) => query.error).filter(Boolean)
  const isRefreshing = dashboardQueries.some((query) => query.isFetching)
  const isInitialLoading = dashboardQueries.every((query) => query.isPending)
  const hasCompleteFailure = dashboardQueries.every((query) => query.isError)
  const artifactUnavailable = errors.find((error) => error instanceof ApiError && error.status === 503)
  const hasEmptyResult = !isRefreshing && errors.length === 0 && overview.data?.incidents === 0
  const availableSensors = observations.data?.meta.available_sensors ?? ['RX-CENTRAL', 'RX-NORTH', 'RX-SOUTH']
  const availableFrequencies = observations.data?.meta.available_frequencies_mhz ?? [433.05, 433.3, 433.55, 433.8, 434.05, 434.3, 434.55, 434.8]

  const retryDashboard = () => {
    void Promise.all(dashboardQueries.map((query) => query.refetch()))
  }

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

        {isInitialLoading && (
          <div className="loading-strip" role="status">
            <span aria-hidden="true" />
            Loading observations, baselines, and ranked incidents…
          </div>
        )}

        {artifactUnavailable && (
          <section className="status-panel status-panel--artifact" role="alert">
            <span className="status-panel__icon" aria-hidden="true">!</span>
            <div>
              <span className="section-label">Demo data required</span>
              <h3>Analysis artifacts are unavailable</h3>
              <p>{errorMessage(artifactUnavailable)}</p>
              <code>make generate</code>
            </div>
            <button type="button" onClick={retryDashboard}>Try again</button>
          </section>
        )}

        {!artifactUnavailable && hasCompleteFailure && (
          <section className="status-panel" role="alert">
            <span className="status-panel__icon" aria-hidden="true">!</span>
            <div>
              <span className="section-label">Connection problem</span>
              <h3>SignalWatch could not reach the analysis service</h3>
              <p>{errorMessage(errors[0])}</p>
            </div>
            <button type="button" onClick={retryDashboard}>Retry</button>
          </section>
        )}

        {!hasCompleteFailure && errors.length > 0 && (
          <div className="error-banner" role="alert">
            <strong>Some analysis could not be loaded.</strong>
            <span>{errorMessage(errors[0])}</span>
          </div>
        )}

        {hasEmptyResult && (
          <div className="empty-banner" role="status">
            <strong>No anomalous incidents match these filters.</strong>
            <span>The timeline still shows normal observations for comparison. Reset or widen the filters to explore incidents.</span>
          </div>
        )}

        {!hasCompleteFailure && (
          <>
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
          </>
        )}
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
