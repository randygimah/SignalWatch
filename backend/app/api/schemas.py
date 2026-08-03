from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    incidents: int
    critical_incidents: int
    affected_sensors: int
    anomaly_rate_pct: float


class ObservationPoint(BaseModel):
    observation_id: int
    timestamp: str
    sensor_id: str
    frequency_mhz: float
    metric: str
    actual: float
    expected: float
    lower: float
    upper: float
    severity_score: float
    is_anomaly: bool
    incident_id: str | None


class ObservationMeta(BaseModel):
    metric: str
    total_points: int
    returned_points: int
    downsampled: bool
    available_sensors: list[str]
    available_frequencies_mhz: list[float]
    from_time: str | None
    to_time: str | None


class ObservationsResponse(BaseModel):
    items: list[ObservationPoint]
    meta: ObservationMeta


class IncidentSummary(BaseModel):
    incident_id: str
    incident_type: str
    title: str
    sensor_id: str
    start_time: str
    end_time: str
    duration_minutes: int
    severity_score: float
    severity: str
    affected_frequencies: list[float]
    detection_count: int
    summary: str
    pattern_description: str


class IncidentListResponse(BaseModel):
    items: list[IncidentSummary]
    total: int
    limit: int
    offset: int


class FeatureContribution(BaseModel):
    feature: str
    contribution_pct: float


class MetricComparison(BaseModel):
    metric: str
    actual: float
    expected: float
    difference: float
    unit: str


class SupportingDetection(BaseModel):
    detection_id: int
    observation_id: int
    timestamp: str
    frequency_mhz: float
    severity_score: float
    severity: str
    values: dict[str, dict[str, float]]
    feature_contributions: list[FeatureContribution]


class IncidentDetail(IncidentSummary):
    metric_comparisons: list[MetricComparison]
    feature_contributions: list[FeatureContribution]
    supporting_detections: list[SupportingDetection]


class HeatmapCell(BaseModel):
    time_bucket: str
    frequency_mhz: float
    severity_score: float
    severity: str
    sensor_id: str
    incident_id: str | None


class HeatmapResponse(BaseModel):
    cells: list[HeatmapCell]
    bucket_minutes: int = Field(ge=5, le=120)


class ErrorResponse(BaseModel):
    detail: str | dict[str, Any]

