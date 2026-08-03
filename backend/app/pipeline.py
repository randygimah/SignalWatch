"""Generate, score, group, evaluate, and persist the SignalWatch demo dataset."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import joblib
import pandas as pd

from app.analytics.config import RAW_METRICS, SEED
from app.analytics.detection import detect_anomalies
from app.analytics.features import build_feature_frame
from app.analytics.incidents import group_incidents
from app.analytics.synthetic import generate_observations


def run_pipeline(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_observations, ground_truth = generate_observations()
    features, feature_columns, baseline_values = build_feature_frame(raw_observations)
    result = detect_anomalies(features, feature_columns, baseline_values)
    incidents, detections = group_incidents(result.detections)

    metrics = _evaluate(result.scored_observations, detections, incidents, ground_truth)
    observations = _public_observations(result.scored_observations)
    public_detections = detections.drop(
        columns=["ground_truth_event_id", "ground_truth_type"], errors="ignore"
    )

    observations.to_parquet(output_dir / "observations.parquet", index=False)
    public_detections.to_parquet(output_dir / "detections.parquet", index=False)
    incidents.to_parquet(output_dir / "incidents.parquet", index=False)
    joblib.dump(result.model_bundle, output_dir / "isolation_forest.joblib")
    (output_dir / "evaluation_metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    artifact_hashes = {
        name: _sha256(output_dir / name)
        for name in (
            "observations.parquet",
            "detections.parquet",
            "incidents.parquet",
            "isolation_forest.joblib",
            "evaluation_metrics.json",
        )
    }
    metadata = {
        "seed": SEED,
        "observation_count": len(observations),
        "detection_count": len(public_detections),
        "incident_count": len(incidents),
        "feature_columns": feature_columns,
        "artifact_sha256": artifact_hashes,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**metrics, **metadata}


def main() -> None:
    output_dir = Path(os.environ.get("SIGNALWATCH_DATA_DIR", "../data")).resolve()
    summary = run_pipeline(output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


def _public_observations(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "observation_id",
        "timestamp",
        "sensor_id",
        "frequency_mhz",
        *RAW_METRICS,
        "is_training",
        "raw_anomaly_score",
        "severity_score",
        "is_anomaly",
    ]
    for metric in RAW_METRICS:
        columns.extend([f"expected_{metric}", f"lower_{metric}", f"upper_{metric}"])
    return frame[columns].copy()


def _evaluate(
    scored: pd.DataFrame,
    detections: pd.DataFrame,
    incidents: pd.DataFrame,
    truth: pd.DataFrame,
) -> dict[str, object]:
    evaluation = scored[~scored["is_training"]]
    clean = evaluation["ground_truth_event_id"].isna()
    false_positive_rate = float(evaluation.loc[clean, "is_anomaly"].mean())
    detected_truth_ids = set(
        detections["ground_truth_event_id"].dropna().astype(str).unique().tolist()
    )
    truth_ids = set(truth["event_id"].astype(str))
    incident_recall = len(detected_truth_ids) / len(truth_ids)
    matches_by_type: dict[str, dict[str, int]] = {}
    for anomaly_type, rows in truth.groupby("anomaly_type", observed=True):
        expected_ids = set(rows["event_id"].astype(str))
        matches_by_type[str(anomaly_type)] = {
            "injected": len(expected_ids),
            "detected": len(expected_ids & detected_truth_ids),
        }
    severity_distribution = (
        incidents["severity"].value_counts().reindex(["critical", "high", "medium", "low"], fill_value=0)
    )
    incident_type_lookup = incidents.set_index("incident_id")["incident_type"].to_dict()
    incident_score_lookup = incidents.set_index("incident_id")["severity_score"].to_dict()
    event_matches: list[dict[str, object]] = []
    correctly_classified = 0
    for truth_row in truth.itertuples(index=False):
        event_detections = detections[
            detections["ground_truth_event_id"].astype("string") == truth_row.event_id
        ].dropna(subset=["incident_id"])
        incident_id = (
            str(event_detections["incident_id"].value_counts().index[0])
            if not event_detections.empty
            else None
        )
        predicted_type = incident_type_lookup.get(incident_id) if incident_id else None
        correctly_classified += int(predicted_type == truth_row.anomaly_type)
        event_matches.append(
            {
                "event_id": truth_row.event_id,
                "expected_type": truth_row.anomaly_type,
                "matched_incident_id": incident_id,
                "predicted_type": predicted_type,
                "severity_score": (
                    round(float(incident_score_lookup[incident_id]), 1) if incident_id else None
                ),
            }
        )
    return {
        "training_observations": int(scored["is_training"].sum()),
        "evaluation_observations": int((~scored["is_training"]).sum()),
        "injected_incidents": len(truth),
        "detected_injected_incidents": len(detected_truth_ids),
        "incident_recall": round(incident_recall, 4),
        "clean_observation_false_positive_rate": round(false_positive_rate, 4),
        "matches_by_type": matches_by_type,
        "incident_type_accuracy": round(correctly_classified / len(truth), 4),
        "event_matches": event_matches,
        "severity_distribution": {key: int(value) for key, value in severity_distribution.items()},
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
