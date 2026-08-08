import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { vi } from 'vitest'

import App from './App'

vi.mock('echarts-for-react', () => ({
  default: ({
    className,
    onEvents,
  }: {
    className?: string
    onEvents?: { click?: (params: { data: { incidentId: string } }) => void }
  }) => (
    <div data-testid="echarts" className={className}>
      {className === 'timeline-chart' && (
        <button type="button" aria-label="Select timeline incident" onClick={() => onEvents?.click?.({ data: { incidentId: 'INC-0001' } })} />
      )}
      {className === 'heatmap-chart' && (
        <button type="button" aria-label="Select heatmap incident" onClick={() => onEvents?.click?.({ data: { incidentId: 'INC-0001' } })} />
      )}
    </div>
  ),
}))

const incident = {
  incident_id: 'INC-0001',
  incident_type: 'broadband_interference',
  title: 'Broadband interference',
  sensor_id: 'RX-NORTH',
  start_time: '2026-07-08T09:00:00Z',
  end_time: '2026-07-08T09:45:00Z',
  duration_minutes: 45,
  severity_score: 96,
  severity: 'critical',
  affected_frequencies: [433.05, 433.3],
  detection_count: 4,
  summary: 'Noise rose across two adjacent channels.',
  pattern_description: 'This is a coordinated multi-channel pattern.',
}

function ok(body: unknown) {
  return Promise.resolve({ ok: true, json: async () => body })
}

function installSuccessfulApiMock() {
  vi.stubGlobal('fetch', vi.fn((input: string | URL | Request) => {
    const url = String(input)
    if (url.includes('/overview')) return ok({ incidents: 8, critical_incidents: 3, affected_sensors: 2, anomaly_rate_pct: 1.5 })
    if (url.includes('/observations')) return ok({
      items: [{
        observation_id: 1,
        timestamp: '2026-07-08T09:00:00Z',
        sensor_id: 'RX-NORTH',
        frequency_mhz: 433.05,
        metric: 'noise_floor_dbm',
        actual: -82,
        expected: -99,
        lower: -101,
        upper: -97,
        severity_score: 96,
        is_anomaly: true,
        incident_id: 'INC-0001',
      }],
      meta: {
        metric: 'noise_floor_dbm',
        total_points: 1,
        returned_points: 1,
        downsampled: false,
        available_sensors: ['RX-NORTH', 'RX-SOUTH'],
        available_frequencies_mhz: [433.05, 433.3],
        from_time: '2026-07-08T09:00:00Z',
        to_time: '2026-07-08T09:00:00Z',
      },
    })
    if (url.endsWith('/anomalies/INC-0001')) return ok({
      ...incident,
      metric_comparisons: [{ metric: 'Noise floor', actual: -82, expected: -99, difference: 17, unit: 'dBm' }],
      feature_contributions: [{ feature: 'Noise floor', contribution_pct: 62 }],
      supporting_detections: [{
        detection_id: 1,
        observation_id: 1,
        timestamp: '2026-07-08T09:00:00Z',
        frequency_mhz: 433.05,
        severity_score: 96,
        severity: 'critical',
        values: { noise_floor_dbm: { actual: -82, expected: -99 } },
        feature_contributions: [{ feature: 'Noise floor', contribution_pct: 62 }],
      }],
    })
    if (url.includes('/anomalies')) return ok({ items: [incident], total: 1, limit: 12, offset: 0 })
    if (url.includes('/heatmap')) return ok({
      cells: [{
        time_bucket: '2026-07-08T09:00:00Z',
        frequency_mhz: 433.05,
        severity_score: 96,
        severity: 'critical',
        sensor_id: 'RX-NORTH',
        incident_id: 'INC-0001',
      }],
      bucket_minutes: 60,
    })
    throw new Error(`Unexpected request: ${url}`)
  }))
}

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
}

test('renders live summary data and opens an incident explanation', async () => {
  installSuccessfulApiMock()
  renderApp()

  expect(screen.getByRole('heading', { name: 'RF anomaly overview' })).toBeInTheDocument()
  const criticalCard = (await screen.findByText('Critical')).closest('article')
  expect(criticalCard).not.toBeNull()
  expect(await within(criticalCard!).findByText('3')).toBeInTheDocument()

  fireEvent.click(await screen.findByRole('button', { name: /Broadband interference/i }))
  const drawer = await screen.findByRole('dialog')
  expect(await within(drawer).findByRole('heading', { name: 'Broadband interference' })).toBeInTheDocument()
  expect(await within(drawer).findByText('Noise rose across two adjacent channels.')).toBeInTheDocument()
  expect(await within(drawer).findByText('62%')).toBeInTheDocument()
})

test('surfaces missing artifacts with a recovery command', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false,
    status: 503,
    json: async () => ({ detail: 'Analytics artifacts are unavailable. Run `make generate`.' }),
  }))
  renderApp()

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Analysis artifacts are unavailable')
  expect(alert).toHaveTextContent('make generate')
  expect(within(alert).getByRole('button', { name: 'Try again' })).toBeInTheDocument()
})

test('applies global sensor and severity filters to every dashboard query', async () => {
  installSuccessfulApiMock()
  renderApp()

  await screen.findByText('Broadband interference')
  const fetchMock = vi.mocked(fetch)
  fetchMock.mockClear()

  fireEvent.change(screen.getByRole('combobox', { name: 'Sensor' }), { target: { value: 'RX-SOUTH' } })
  fireEvent.change(screen.getByRole('combobox', { name: 'Minimum severity' }), { target: { value: '90' } })

  await waitFor(() => {
    const requested = fetchMock.mock.calls.map(([input]) => new URL(String(input)))
    for (const path of ['/api/v1/overview', '/api/v1/observations', '/api/v1/anomalies', '/api/v1/heatmap']) {
      expect(requested.some((url) => (
        url.pathname === path
        && url.searchParams.get('sensor_id') === 'RX-SOUTH'
        && url.searchParams.get('min_severity') === '90'
      ))).toBe(true)
    }
  })
})

test('opens the same explained incident from timeline and heatmap selections', async () => {
  installSuccessfulApiMock()
  renderApp()

  fireEvent.click(await screen.findByRole('button', { name: 'Select timeline incident' }))
  let drawer = await screen.findByRole('dialog')
  expect(await within(drawer).findByRole('heading', { name: 'Broadband interference' })).toBeInTheDocument()
  fireEvent.click(within(drawer).getByRole('button', { name: 'Close incident detail' }))
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Select heatmap incident' }))
  drawer = await screen.findByRole('dialog')
  expect(within(drawer).getByText('Noise rose across two adjacent channels.')).toBeInTheDocument()
})
