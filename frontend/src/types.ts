export type Severity = 'low' | 'medium' | 'high' | 'critical'

export type DashboardFilters = {
  from: string
  to: string
  sensorId: string
  frequencyMhz: number | null
  minSeverity: number | null
  incidentType: string
}

export type Overview = {
  incidents: number
  critical_incidents: number
  affected_sensors: number
  anomaly_rate_pct: number
}

export type ObservationPoint = {
  observation_id: number
  timestamp: string
  sensor_id: string
  frequency_mhz: number
  metric: string
  actual: number
  expected: number
  lower: number
  upper: number
  severity_score: number
  is_anomaly: boolean
  incident_id: string | null
}

export type ObservationResponse = {
  items: ObservationPoint[]
  meta: {
    metric: string
    total_points: number
    returned_points: number
    downsampled: boolean
    available_sensors: string[]
    available_frequencies_mhz: number[]
    from_time: string | null
    to_time: string | null
  }
}

export type IncidentSummary = {
  incident_id: string
  incident_type: string
  title: string
  sensor_id: string
  start_time: string
  end_time: string
  duration_minutes: number
  severity_score: number
  severity: Severity
  affected_frequencies: number[]
  detection_count: number
  summary: string
  pattern_description: string
}

export type IncidentListResponse = {
  items: IncidentSummary[]
  total: number
  limit: number
  offset: number
}

export type FeatureContribution = {
  feature: string
  contribution_pct: number
}

export type MetricComparison = {
  metric: string
  actual: number
  expected: number
  difference: number
  unit: string
}

export type SupportingDetection = {
  detection_id: number
  observation_id: number
  timestamp: string
  frequency_mhz: number
  severity_score: number
  severity: Severity
  values: Record<string, { actual: number; expected: number }>
  feature_contributions: FeatureContribution[]
}

export type IncidentDetail = IncidentSummary & {
  metric_comparisons: MetricComparison[]
  feature_contributions: FeatureContribution[]
  supporting_detections: SupportingDetection[]
}

export type HeatmapCell = {
  time_bucket: string
  frequency_mhz: number
  severity_score: number
  severity: Severity
  sensor_id: string
  incident_id: string | null
}

export type HeatmapResponse = {
  cells: HeatmapCell[]
  bucket_minutes: number
}

export const METRICS = [
  { value: 'noise_floor_dbm', label: 'Noise floor', unit: 'dBm' },
  { value: 'rssi_dbm', label: 'RSSI', unit: 'dBm' },
  { value: 'snr_db', label: 'SNR', unit: 'dB' },
  { value: 'occupancy_pct', label: 'Channel occupancy', unit: '%' },
  { value: 'packet_loss_pct', label: 'Packet loss', unit: '%' },
  { value: 'frequency_offset_khz', label: 'Frequency offset', unit: 'kHz' },
] as const

export const INCIDENT_TYPES = [
  { value: 'broadband_interference', label: 'Broadband interference' },
  { value: 'narrowband_interference', label: 'Narrowband interference' },
  { value: 'signal_dropout', label: 'Signal dropout' },
  { value: 'sensor_malfunction', label: 'Sensor malfunction' },
  { value: 'unusual_rf_pattern', label: 'Unusual RF pattern' },
] as const

