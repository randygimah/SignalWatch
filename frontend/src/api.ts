import type {
  DashboardFilters,
  HeatmapResponse,
  IncidentDetail,
  IncidentListResponse,
  ObservationResponse,
  Overview,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

function filterParams(filters: DashboardFilters): URLSearchParams {
  const params = new URLSearchParams()
  if (filters.from) params.set('from', filters.from)
  if (filters.to) params.set('to', filters.to)
  if (filters.sensorId) params.set('sensor_id', filters.sensorId)
  if (filters.frequencyMhz !== null) params.set('frequency_mhz', String(filters.frequencyMhz))
  if (filters.minSeverity !== null) params.set('min_severity', String(filters.minSeverity))
  if (filters.incidentType) params.set('incident_type', filters.incidentType)
  return params
}

async function request<T>(path: string, params?: URLSearchParams): Promise<T> {
  const query = params?.toString()
  const response = await fetch(`${API_BASE_URL}${path}${query ? `?${query}` : ''}`)
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function getOverview(filters: DashboardFilters): Promise<Overview> {
  return request('/api/v1/overview', filterParams(filters))
}

export function getObservations(
  filters: DashboardFilters,
  metric: string,
): Promise<ObservationResponse> {
  const params = filterParams(filters)
  params.set('metric', metric)
  params.set('limit', '1000')
  return request('/api/v1/observations', params)
}

export function getAnomalies(filters: DashboardFilters): Promise<IncidentListResponse> {
  const params = filterParams(filters)
  params.set('limit', '12')
  return request('/api/v1/anomalies', params)
}

export function getIncident(incidentId: string): Promise<IncidentDetail> {
  return request(`/api/v1/anomalies/${incidentId}`)
}

export function getHeatmap(filters: DashboardFilters): Promise<HeatmapResponse> {
  const params = filterParams(filters)
  params.set('bucket_minutes', '60')
  return request('/api/v1/heatmap', params)
}

