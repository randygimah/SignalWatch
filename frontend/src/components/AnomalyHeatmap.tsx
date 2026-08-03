import ReactECharts from 'echarts-for-react'

import type { HeatmapCell } from '../types'

type AnomalyHeatmapProps = {
  cells: HeatmapCell[]
  loading: boolean
  onSelectIncident: (incidentId: string) => void
}

type HeatmapClick = { data?: { incidentId?: string } }

export function AnomalyHeatmap({ cells, loading, onSelectIncident }: AnomalyHeatmapProps) {
  const times = [...new Set(cells.map((cell) => cell.time_bucket))].sort()
  const frequencies = [...new Set(cells.map((cell) => cell.frequency_mhz))].sort((a, b) => a - b)
  const timeIndex = new Map(times.map((time, index) => [time, index]))
  const frequencyIndex = new Map(frequencies.map((frequency, index) => [frequency, index]))

  const option = {
    animation: false,
    grid: { left: 76, right: 26, top: 30, bottom: 92 },
    tooltip: {
      formatter: (params: { data: { value: [number, number, number]; cell: HeatmapCell } }) => {
        const cell = params.data.cell
        return [
          `<strong>${cell.frequency_mhz.toFixed(2)} MHz</strong>`,
          new Date(cell.time_bucket).toLocaleString('en-GB', { timeZone: 'UTC' }) + ' UTC',
          `Severity ${cell.severity_score.toFixed(1)} · ${cell.severity}`,
          cell.incident_id ? 'Click to inspect incident' : 'Isolated detection',
        ].join('<br/>')
      },
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: {
        color: '#6d7585',
        formatter: (value: string) => new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', timeZone: 'UTC' }).format(new Date(value)),
      },
      axisLine: { lineStyle: { color: '#cbd3e2' } },
      splitArea: { show: true },
    },
    yAxis: {
      type: 'category',
      data: frequencies.map((frequency) => `${frequency.toFixed(2)} MHz`),
      axisLabel: { color: '#5e6675', fontFamily: 'JetBrains Mono' },
      axisLine: { lineStyle: { color: '#cbd3e2' } },
      splitArea: { show: true },
    },
    visualMap: {
      min: 50,
      max: 100,
      calculable: false,
      orient: 'horizontal',
      right: 20,
      bottom: 4,
      text: ['Critical', 'Low'],
      inRange: { color: ['#bed0eb', '#f1b74f', '#ed7346', '#bd1f29'] },
      textStyle: { color: '#6d7585' },
    },
    series: [
      {
        type: 'heatmap',
        data: cells.map((cell) => ({
          value: [timeIndex.get(cell.time_bucket), frequencyIndex.get(cell.frequency_mhz), cell.severity_score],
          incidentId: cell.incident_id ?? undefined,
          cell,
        })),
        itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 2 },
        emphasis: { itemStyle: { borderColor: '#111c2d', borderWidth: 1 } },
      },
    ],
  }

  return (
    <section className="panel heatmap-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Patterns across adjacent frequencies</span>
          <h2>Channel anomaly heatmap</h2>
        </div>
        <span className="panel-note">60-minute buckets</span>
      </div>
      {loading && <div className="chart-state"><div className="skeleton skeleton--chart" /></div>}
      {!loading && cells.length === 0 && <div className="chart-state empty-state">No anomalous channel activity matches these filters.</div>}
      {!loading && cells.length > 0 && (
        <ReactECharts
          option={option}
          className="heatmap-chart"
          notMerge
          onEvents={{ click: (params: HeatmapClick) => params.data?.incidentId && onSelectIncident(params.data.incidentId) }}
        />
      )}
    </section>
  )
}
