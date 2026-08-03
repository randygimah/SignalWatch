import ReactECharts from 'echarts-for-react'

import { METRICS } from '../types'
import type { ObservationPoint } from '../types'

type SignalTimelineProps = {
  points: ObservationPoint[]
  loading: boolean
  metric: string
  focusFrequency: number
  frequencies: number[]
  frequencyLocked: boolean
  downsampled: boolean
  onMetricChange: (metric: string) => void
  onFocusFrequencyChange: (frequency: number) => void
  onSelectIncident: (incidentId: string) => void
}

type ChartClick = { data?: { incidentId?: string } }

const colors: Record<string, string> = {
  low: '#8ba8d9',
  medium: '#f0a21a',
  high: '#ed6a3a',
  critical: '#c5222b',
}

function severity(score: number) {
  if (score >= 90) return 'critical'
  if (score >= 80) return 'high'
  if (score >= 65) return 'medium'
  return 'low'
}

export function SignalTimeline({
  points,
  loading,
  metric,
  focusFrequency,
  frequencies,
  frequencyLocked,
  downsampled,
  onMetricChange,
  onFocusFrequencyChange,
  onSelectIncident,
}: SignalTimelineProps) {
  const metricDefinition = METRICS.find((item) => item.value === metric) ?? METRICS[0]
  const anomalies = points
    .filter((point) => point.is_anomaly)
    .map((point) => ({
      value: [point.timestamp, point.actual],
      incidentId: point.incident_id ?? undefined,
      itemStyle: { color: colors[severity(point.severity_score)] },
      symbolSize: point.severity_score >= 90 ? 11 : 8,
      severityScore: point.severity_score,
    }))

  const option = {
    animation: false,
    grid: { left: 58, right: 26, top: 30, bottom: 74 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      valueFormatter: (value: number) => `${Number(value).toFixed(2)} ${metricDefinition.unit}`,
    },
    legend: {
      data: ['Observed', 'Expected', 'Anomaly'],
      right: 14,
      textStyle: { color: '#586174', fontFamily: 'Hanken Grotesk' },
    },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: '#cbd3e2' } },
      axisLabel: { color: '#6d7585', hideOverlap: true },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: metricDefinition.unit,
      nameTextStyle: { color: '#6d7585' },
      axisLabel: { color: '#6d7585' },
      splitLine: { lineStyle: { color: '#e8edf6' } },
      scale: true,
    },
    dataZoom: [
      { type: 'inside', filterMode: 'none' },
      {
        type: 'slider',
        height: 22,
        bottom: 18,
        borderColor: '#d5dceb',
        backgroundColor: '#f3f6fc',
        fillerColor: 'rgba(0,88,190,.12)',
        handleStyle: { color: '#0058be' },
        showDetail: false,
        filterMode: 'none',
      },
    ],
    series: [
      {
        name: 'Normal floor',
        type: 'line',
        data: points.map((point) => [point.timestamp, point.lower]),
        stack: 'normal-band',
        stackStrategy: 'all',
        symbol: 'none',
        lineStyle: { opacity: 0 },
        areaStyle: { opacity: 0 },
        silent: true,
      },
      {
        name: 'Expected',
        type: 'line',
        data: points.map((point) => [point.timestamp, point.upper - point.lower]),
        stack: 'normal-band',
        stackStrategy: 'all',
        symbol: 'none',
        lineStyle: { color: '#9eb9e6', width: 1, opacity: 0.45 },
        areaStyle: { color: 'rgba(61,126,217,.16)' },
        itemStyle: { color: '#9eb9e6' },
        silent: true,
      },
      {
        name: 'Expected',
        type: 'line',
        data: points.map((point) => [point.timestamp, point.expected]),
        symbol: 'none',
        lineStyle: { color: '#7f9bc9', width: 1.25, type: 'dashed' },
        itemStyle: { color: '#7f9bc9' },
      },
      {
        name: 'Observed',
        type: 'line',
        data: points.map((point) => [point.timestamp, point.actual]),
        symbol: 'none',
        lineStyle: { color: '#0058be', width: 1.8 },
        areaStyle: { color: 'rgba(0,88,190,.035)' },
        itemStyle: { color: '#0058be' },
      },
      {
        name: 'Anomaly',
        type: 'scatter',
        data: anomalies,
        z: 10,
      },
    ],
  }

  return (
    <section className="panel timeline-panel">
      <div className="panel-heading panel-heading--chart">
        <div>
          <span className="eyebrow">Actual compared with normal</span>
          <h2>Signal timeline</h2>
        </div>
        <div className="chart-controls">
          <label>
            <span>Metric</span>
            <select value={metric} onChange={(event) => onMetricChange(event.target.value)}>
              {METRICS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <label>
            <span>Focus channel</span>
            <select
              value={focusFrequency}
              disabled={frequencyLocked}
              onChange={(event) => onFocusFrequencyChange(Number(event.target.value))}
            >
              {frequencies.map((frequency) => <option key={frequency} value={frequency}>{frequency.toFixed(2)} MHz</option>)}
            </select>
          </label>
        </div>
      </div>
      {loading && <div className="chart-state"><div className="skeleton skeleton--chart" /></div>}
      {!loading && points.length === 0 && <div className="chart-state empty-state">No signal observations match these filters.</div>}
      {!loading && points.length > 0 && (
        <>
          <ReactECharts
            option={option}
            className="timeline-chart"
            notMerge
            onEvents={{
              click: (params: ChartClick) => {
                if (params.data?.incidentId) onSelectIncident(params.data.incidentId)
              },
            }}
          />
          <div className="chart-footnote">
            <span>{focusFrequency.toFixed(2)} MHz · {metricDefinition.label}</span>
            {downsampled && <span>Normal readings sampled; every anomaly retained</span>}
          </div>
        </>
      )}
    </section>
  )
}
