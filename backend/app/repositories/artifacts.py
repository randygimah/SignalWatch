from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.analytics.config import RAW_METRICS

INCIDENT_TYPES = {
    "broadband_interference",
    "narrowband_interference",
    "signal_dropout",
    "sensor_malfunction",
    "unusual_rf_pattern",
}


class ArtifactUnavailableError(RuntimeError):
    """Raised when the generated analytics artifacts are not available."""


class InvalidFilterError(ValueError):
    """Raised when an API filter is outside the generated dataset domain."""


@dataclass(frozen=True)
class QueryFilters:
    from_time: datetime | None = None
    to_time: datetime | None = None
    sensor_id: str | None = None
    frequency_mhz: float | None = None
    min_severity: float | None = None
    incident_type: str | None = None


class ArtifactRepository:
    required_files = ("observations.parquet", "detections.parquet", "incidents.parquet")

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.observations = pd.DataFrame()
        self.detections = pd.DataFrame()
        self.incidents = pd.DataFrame()
        self.sensors: tuple[str, ...] = ()
        self.frequencies: tuple[float, ...] = ()

    def load(self) -> None:
        missing = [name for name in self.required_files if not (self.data_dir / name).exists()]
        if missing:
            raise ArtifactUnavailableError(
                f"Missing generated artifacts: {', '.join(missing)}. Run `make generate`."
            )

        self.observations = pd.read_parquet(self.data_dir / "observations.parquet")
        self.detections = pd.read_parquet(self.data_dir / "detections.parquet")
        self.incidents = pd.read_parquet(self.data_dir / "incidents.parquet")
        relation = self.detections[["observation_id", "incident_id"]].dropna(
            subset=["incident_id"]
        )
        self.observations = self.observations.merge(
            relation,
            on="observation_id",
            how="left",
            validate="one_to_one",
        )
        self.sensors = tuple(sorted(self.observations["sensor_id"].unique().tolist()))
        self.frequencies = tuple(
            sorted(float(value) for value in self.observations["frequency_mhz"].unique())
        )

    def overview(self, filters: QueryFilters) -> dict[str, Any]:
        self.validate_filters(filters)
        incidents = self._filter_incidents(filters)
        observations = self._filter_observations(
            replace(filters, min_severity=None, incident_type=None),
            evaluation_only=True,
        )
        detections = self._filter_detections(filters, incidents)
        anomaly_rate = len(detections) / len(observations) * 100 if len(observations) else 0
        return {
            "incidents": len(incidents),
            "critical_incidents": int((incidents["severity"] == "critical").sum()),
            "affected_sensors": int(incidents["sensor_id"].nunique()),
            "anomaly_rate_pct": round(anomaly_rate, 2),
        }

    def observation_series(
        self,
        filters: QueryFilters,
        metric: str,
        limit: int = 1_000,
    ) -> dict[str, Any]:
        self.validate_filters(filters, metric=metric)
        rows = self._filter_observations(filters, evaluation_only=True).sort_values(
            ["timestamp", "sensor_id", "frequency_mhz"]
        )
        total = len(rows)
        rows = _downsample_preserving_anomalies(rows, limit)
        items = [
            {
                "observation_id": int(row.observation_id),
                "timestamp": _iso(row.timestamp),
                "sensor_id": row.sensor_id,
                "frequency_mhz": float(row.frequency_mhz),
                "metric": metric,
                "actual": round(float(getattr(row, metric)), 4),
                "expected": round(float(getattr(row, f"expected_{metric}")), 4),
                "lower": round(float(getattr(row, f"lower_{metric}")), 4),
                "upper": round(float(getattr(row, f"upper_{metric}")), 4),
                "severity_score": round(float(row.severity_score), 1),
                "is_anomaly": bool(row.is_anomaly),
                "incident_id": None if pd.isna(row.incident_id) else str(row.incident_id),
            }
            for row in rows.itertuples(index=False)
        ]
        return {
            "items": items,
            "meta": {
                "metric": metric,
                "total_points": total,
                "returned_points": len(items),
                "downsampled": total > len(items),
                "available_sensors": list(self.sensors),
                "available_frequencies_mhz": list(self.frequencies),
                "from_time": _iso(rows["timestamp"].min()) if not rows.empty else None,
                "to_time": _iso(rows["timestamp"].max()) if not rows.empty else None,
            },
        }

    def anomaly_list(self, filters: QueryFilters, limit: int, offset: int) -> dict[str, Any]:
        self.validate_filters(filters)
        rows = self._filter_incidents(filters).sort_values(
            ["severity_score", "start_time"], ascending=[False, True]
        )
        total = len(rows)
        page = rows.iloc[offset : offset + limit]
        return {
            "items": [_incident_summary(row) for row in page.itertuples(index=False)],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def anomaly_detail(self, incident_id: str) -> dict[str, Any] | None:
        matches = self.incidents[self.incidents["incident_id"] == incident_id]
        if matches.empty:
            return None
        incident = matches.iloc[0]
        supporting = self.detections[self.detections["incident_id"] == incident_id].sort_values(
            ["timestamp", "frequency_mhz"]
        )
        detail = _incident_summary(incident)
        detail.update(
            {
                "metric_comparisons": _parse_json(incident["metric_comparisons"]),
                "feature_contributions": _parse_json(incident["feature_contributions"]),
                "supporting_detections": [
                    _supporting_detection(row) for row in supporting.itertuples(index=False)
                ],
            }
        )
        return detail

    def heatmap(self, filters: QueryFilters, bucket_minutes: int) -> dict[str, Any]:
        self.validate_filters(filters)
        incidents = self._filter_incidents(filters)
        rows = self._filter_detections(filters, incidents).copy()
        if rows.empty:
            return {"cells": [], "bucket_minutes": bucket_minutes}
        rows["time_bucket"] = rows["timestamp"].dt.floor(f"{bucket_minutes}min")
        indices = rows.groupby(["time_bucket", "frequency_mhz"], observed=True)[
            "severity_score"
        ].idxmax()
        cells = rows.loc[indices].sort_values(["time_bucket", "frequency_mhz"])
        return {
            "cells": [
                {
                    "time_bucket": _iso(row.time_bucket),
                    "frequency_mhz": float(row.frequency_mhz),
                    "severity_score": round(float(row.severity_score), 1),
                    "severity": str(row.severity),
                    "sensor_id": str(row.sensor_id),
                    "incident_id": None if pd.isna(row.incident_id) else str(row.incident_id),
                }
                for row in cells.itertuples(index=False)
            ],
            "bucket_minutes": bucket_minutes,
        }

    def validate_filters(self, filters: QueryFilters, metric: str | None = None) -> None:
        if (
            filters.from_time
            and filters.to_time
            and _utc_timestamp(filters.from_time) > _utc_timestamp(filters.to_time)
        ):
            raise InvalidFilterError("`from` must be earlier than or equal to `to`.")
        if filters.sensor_id and filters.sensor_id not in self.sensors:
            raise InvalidFilterError(
                f"Unknown sensor_id `{filters.sensor_id}`. Expected one of: {', '.join(self.sensors)}."
            )
        if filters.frequency_mhz is not None and not any(
            np.isclose(filters.frequency_mhz, frequency) for frequency in self.frequencies
        ):
            expected = ", ".join(str(value) for value in self.frequencies)
            raise InvalidFilterError(
                f"Unknown frequency_mhz `{filters.frequency_mhz}`. Expected one of: {expected}."
            )
        if filters.incident_type and filters.incident_type not in INCIDENT_TYPES:
            raise InvalidFilterError(
                f"Unknown incident_type `{filters.incident_type}`. Expected one of: "
                f"{', '.join(sorted(INCIDENT_TYPES))}."
            )
        if metric and metric not in RAW_METRICS:
            raise InvalidFilterError(
                f"Unknown metric `{metric}`. Expected one of: {', '.join(RAW_METRICS)}."
            )

    def _filter_observations(
        self, filters: QueryFilters, *, evaluation_only: bool
    ) -> pd.DataFrame:
        rows = self.observations
        if evaluation_only:
            rows = rows[~rows["is_training"]]
        rows = _apply_common_filters(rows, filters)
        if filters.min_severity is not None:
            rows = rows[rows["severity_score"] >= filters.min_severity]
        return rows

    def _filter_incidents(self, filters: QueryFilters) -> pd.DataFrame:
        rows = self.incidents
        if filters.from_time:
            rows = rows[rows["end_time"] >= _utc_timestamp(filters.from_time)]
        if filters.to_time:
            rows = rows[rows["start_time"] <= _utc_timestamp(filters.to_time)]
        if filters.sensor_id:
            rows = rows[rows["sensor_id"] == filters.sensor_id]
        if filters.frequency_mhz is not None:
            rows = rows[
                rows["affected_frequencies"].map(
                    lambda value: any(
                        np.isclose(filters.frequency_mhz, frequency)
                        for frequency in _parse_json(value)
                    )
                )
            ]
        if filters.min_severity is not None:
            rows = rows[rows["severity_score"] >= filters.min_severity]
        if filters.incident_type:
            rows = rows[rows["incident_type"] == filters.incident_type]
        return rows

    def _filter_detections(
        self, filters: QueryFilters, incidents: pd.DataFrame
    ) -> pd.DataFrame:
        rows = _apply_common_filters(self.detections, filters)
        if filters.min_severity is not None:
            rows = rows[rows["severity_score"] >= filters.min_severity]
        if filters.incident_type:
            allowed_ids = set(incidents["incident_id"])
            rows = rows[rows["incident_id"].isin(allowed_ids)]
        return rows


def _apply_common_filters(rows: pd.DataFrame, filters: QueryFilters) -> pd.DataFrame:
    if filters.from_time:
        rows = rows[rows["timestamp"] >= _utc_timestamp(filters.from_time)]
    if filters.to_time:
        rows = rows[rows["timestamp"] <= _utc_timestamp(filters.to_time)]
    if filters.sensor_id:
        rows = rows[rows["sensor_id"] == filters.sensor_id]
    if filters.frequency_mhz is not None:
        rows = rows[np.isclose(rows["frequency_mhz"], filters.frequency_mhz)]
    return rows


def _downsample_preserving_anomalies(rows: pd.DataFrame, limit: int) -> pd.DataFrame:
    if len(rows) <= limit:
        return rows
    anomalies = rows[rows["is_anomaly"]].sort_values("severity_score", ascending=False)
    if len(anomalies) >= limit:
        return anomalies.head(limit).sort_values("timestamp")
    normal = rows[~rows.index.isin(anomalies.index)]
    remaining = limit - len(anomalies)
    positions = np.linspace(0, len(normal) - 1, remaining, dtype=int)
    sampled = normal.iloc[np.unique(positions)]
    return pd.concat([sampled, anomalies]).drop_duplicates("observation_id").sort_values(
        ["timestamp", "sensor_id", "frequency_mhz"]
    )


def _incident_summary(row: Any) -> dict[str, Any]:
    get = (lambda name: getattr(row, name)) if hasattr(row, "incident_id") else row.__getitem__
    return {
        "incident_id": str(get("incident_id")),
        "incident_type": str(get("incident_type")),
        "title": str(get("title")),
        "sensor_id": str(get("sensor_id")),
        "start_time": _iso(get("start_time")),
        "end_time": _iso(get("end_time")),
        "duration_minutes": int(get("duration_minutes")),
        "severity_score": round(float(get("severity_score")), 1),
        "severity": str(get("severity")),
        "affected_frequencies": [float(value) for value in _parse_json(get("affected_frequencies"))],
        "detection_count": int(get("detection_count")),
        "summary": str(get("summary")),
        "pattern_description": str(get("pattern_description")),
    }


def _supporting_detection(row: Any) -> dict[str, Any]:
    values = {
        metric: {
            "actual": round(float(getattr(row, metric)), 4),
            "expected": round(float(getattr(row, f"expected_{metric}")), 4),
        }
        for metric in RAW_METRICS
    }
    return {
        "detection_id": int(row.detection_id),
        "observation_id": int(row.observation_id),
        "timestamp": _iso(row.timestamp),
        "frequency_mhz": float(row.frequency_mhz),
        "severity_score": round(float(row.severity_score), 1),
        "severity": str(row.severity),
        "values": values,
        "feature_contributions": _parse_json(row.feature_contributions),
    }


def _parse_json(value: str | list[Any]) -> Any:
    return json.loads(value) if isinstance(value, str) else value


def _utc_timestamp(value: datetime) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _iso(value: Any) -> str:
    return pd.Timestamp(value).isoformat().replace("+00:00", "Z")
