import ReactECharts from 'echarts-for-react'
import { useEffect } from 'react'

import type { IncidentDetail } from '../types'

type IncidentDrawerProps = {
  incident?: IncidentDetail
  loading: boolean
  error: string | null
  onClose: () => void
}

export function IncidentDrawer({ incident, loading, error, onClose }: IncidentDrawerProps) {
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  const comparisonOption = incident ? {
    animation: false,
    grid: { left: 44, right: 16, top: 18, bottom: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'time',
      axisLabel: { color: '#71798a', hideOverlap: true },
      axisLine: { lineStyle: { color: '#d3daea' } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: '#71798a' },
      splitLine: { lineStyle: { color: '#edf0f6' } },
    },
    series: [
      {
        name: 'Actual noise floor',
        type: 'line',
        symbol: 'none',
        lineStyle: { color: '#bd1f29', width: 2 },
        areaStyle: { color: 'rgba(189,31,41,.08)' },
        data: incident.supporting_detections.map((point) => [point.timestamp, point.values.noise_floor_dbm.actual]),
      },
      {
        name: 'Expected',
        type: 'line',
        symbol: 'none',
        lineStyle: { color: '#8090aa', width: 1.4, type: 'dashed' },
        data: incident.supporting_detections.map((point) => [point.timestamp, point.values.noise_floor_dbm.expected]),
      },
    ],
  } : {}

  return (
    <div className="drawer-layer" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <aside className="incident-drawer" role="dialog" aria-modal="true" aria-labelledby="incident-drawer-title">
        <header className="drawer-header">
          <div>
            <span className="eyebrow">Incident analysis</span>
            <h2 id="incident-drawer-title">{incident?.title ?? 'Incident detail'}</h2>
          </div>
          <button type="button" className="icon-button" aria-label="Close incident detail" onClick={onClose}>×</button>
        </header>
        <div className="drawer-content">
          {loading && <div className="drawer-loading"><div className="skeleton skeleton--value" /><div className="skeleton skeleton--block" /></div>}
          {error && <div role="alert" className="error-state">{error}</div>}
          {incident && (
            <>
              <section className="severity-hero">
                <div>
                  <span className={`severity-pill severity-pill--${incident.severity}`}>{incident.severity} alert</span>
                  <p>{incident.sensor_id} · {incident.duration_minutes} minutes</p>
                </div>
                <strong>{Math.round(incident.severity_score)}<small>/100</small></strong>
                <div className="severity-track"><span style={{ width: `${incident.severity_score}%` }} /></div>
              </section>

              <section className="explanation-card">
                <span className="section-label">What happened</span>
                <p>{incident.summary}</p>
              </section>

              <section>
                <span className="section-label">Actual compared with normal</span>
                <div className="metric-grid">
                  {incident.metric_comparisons.map((metric) => (
                    <article className="metric-card" key={metric.metric}>
                      <span>{metric.metric}</span>
                      <strong>{metric.actual}<small>{metric.unit}</small></strong>
                      <p>Expected {metric.expected} {metric.unit}</p>
                    </article>
                  ))}
                </div>
              </section>

              <section>
                <div className="section-title-row">
                  <span className="section-label">Noise floor during incident</span>
                  <span>{incident.supporting_detections.length} readings</span>
                </div>
                <ReactECharts option={comparisonOption} className="drawer-chart" notMerge />
              </section>

              <section>
                <span className="section-label">Why the model flagged it</span>
                <div className="contribution-list">
                  {incident.feature_contributions.map((contribution) => (
                    <div className="contribution" key={contribution.feature}>
                      <div><span>{contribution.feature}</span><strong>{contribution.contribution_pct}%</strong></div>
                      <div className="contribution-track"><span style={{ width: `${contribution.contribution_pct}%` }} /></div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="pattern-card">
                <span className="section-label">Pattern context</span>
                <p>{incident.pattern_description}</p>
                <div className="frequency-tags">
                  {incident.affected_frequencies.map((frequency) => <span key={frequency}>{frequency.toFixed(2)} MHz</span>)}
                </div>
              </section>
            </>
          )}
        </div>
      </aside>
    </div>
  )
}

