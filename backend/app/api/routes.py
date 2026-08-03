from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies import get_repository
from app.api.schemas import (
    HeatmapResponse,
    IncidentDetail,
    IncidentListResponse,
    ObservationsResponse,
    OverviewResponse,
)
from app.repositories.artifacts import (
    ArtifactRepository,
    InvalidFilterError,
    QueryFilters,
)

router = APIRouter(prefix="/api/v1")
Repository = Annotated[ArtifactRepository, Depends(get_repository)]


@router.get("/overview", response_model=OverviewResponse, tags=["analytics"])
def overview(
    repository: Repository,
    from_time: Annotated[datetime | None, Query(alias="from")] = None,
    to_time: Annotated[datetime | None, Query(alias="to")] = None,
    sensor_id: str | None = None,
    frequency_mhz: float | None = None,
    min_severity: Annotated[float | None, Query(ge=0, le=100)] = None,
    incident_type: str | None = None,
) -> dict:
    return _handle_filters(
        repository.overview,
        _filters(from_time, to_time, sensor_id, frequency_mhz, min_severity, incident_type),
    )


@router.get("/observations", response_model=ObservationsResponse, tags=["analytics"])
def observations(
    repository: Repository,
    metric: str = "noise_floor_dbm",
    from_time: Annotated[datetime | None, Query(alias="from")] = None,
    to_time: Annotated[datetime | None, Query(alias="to")] = None,
    sensor_id: str | None = None,
    frequency_mhz: float | None = None,
    min_severity: Annotated[float | None, Query(ge=0, le=100)] = None,
    limit: Annotated[int, Query(ge=1, le=1_000)] = 1_000,
) -> dict:
    filters = _filters(from_time, to_time, sensor_id, frequency_mhz, min_severity, None)
    try:
        return repository.observation_series(filters, metric, limit)
    except InvalidFilterError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@router.get("/anomalies", response_model=IncidentListResponse, tags=["anomalies"])
def anomalies(
    repository: Repository,
    from_time: Annotated[datetime | None, Query(alias="from")] = None,
    to_time: Annotated[datetime | None, Query(alias="to")] = None,
    sensor_id: str | None = None,
    frequency_mhz: float | None = None,
    min_severity: Annotated[float | None, Query(ge=0, le=100)] = None,
    incident_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    filters = _filters(from_time, to_time, sensor_id, frequency_mhz, min_severity, incident_type)
    try:
        return repository.anomaly_list(filters, limit, offset)
    except InvalidFilterError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@router.get("/anomalies/{incident_id}", response_model=IncidentDetail, tags=["anomalies"])
def anomaly_detail(
    repository: Repository,
    incident_id: Annotated[str, Path(pattern=r"^INC-\d{4}$")],
) -> dict:
    detail = repository.anomaly_detail(incident_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident `{incident_id}` was not found.",
        )
    return detail


@router.get("/heatmap", response_model=HeatmapResponse, tags=["analytics"])
def heatmap(
    repository: Repository,
    from_time: Annotated[datetime | None, Query(alias="from")] = None,
    to_time: Annotated[datetime | None, Query(alias="to")] = None,
    sensor_id: str | None = None,
    frequency_mhz: float | None = None,
    min_severity: Annotated[float | None, Query(ge=0, le=100)] = None,
    incident_type: str | None = None,
    bucket_minutes: Annotated[int, Query(ge=5, le=120)] = 30,
) -> dict:
    filters = _filters(from_time, to_time, sensor_id, frequency_mhz, min_severity, incident_type)
    try:
        return repository.heatmap(filters, bucket_minutes)
    except InvalidFilterError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


def _filters(
    from_time: datetime | None,
    to_time: datetime | None,
    sensor_id: str | None,
    frequency_mhz: float | None,
    min_severity: float | None,
    incident_type: str | None,
) -> QueryFilters:
    return QueryFilters(
        from_time=from_time,
        to_time=to_time,
        sensor_id=sensor_id,
        frequency_mhz=frequency_mhz,
        min_severity=min_severity,
        incident_type=incident_type,
    )


def _handle_filters(function, filters: QueryFilters) -> dict:
    try:
        return function(filters)
    except InvalidFilterError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error

