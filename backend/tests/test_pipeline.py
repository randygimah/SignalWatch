from __future__ import annotations

import json

import pandas as pd

from app.analytics.config import INCIDENT_SPECS
from app.analytics.synthetic import generate_observations
from app.pipeline import run_pipeline


def test_synthetic_generator_is_reproducible_and_keeps_training_clean() -> None:
    first, first_truth = generate_observations()
    second, second_truth = generate_observations()

    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(first_truth, second_truth)
    assert len(first) == 96_768
    assert len(first_truth) == len(INCIDENT_SPECS) == 12
    assert first.loc[first["is_training"], "ground_truth_event_id"].isna().all()


def test_pipeline_writes_private_label_free_artifacts_and_meets_quality_targets(tmp_path) -> None:
    summary = run_pipeline(tmp_path)

    assert summary["incident_recall"] >= 0.70
    assert summary["clean_observation_false_positive_rate"] < 0.05
    assert summary["detected_injected_incidents"] == 12
    assert summary["incident_type_accuracy"] >= 0.90
    assert summary["observation_count"] == 96_768
    assert summary["detection_count"] > 0
    assert 12 <= summary["incident_count"] <= 100

    expected_artifacts = {
        "observations.parquet",
        "detections.parquet",
        "incidents.parquet",
        "isolation_forest.joblib",
        "evaluation_metrics.json",
        "metadata.json",
    }
    assert expected_artifacts == {path.name for path in tmp_path.iterdir()}

    observations = pd.read_parquet(tmp_path / "observations.parquet")
    detections = pd.read_parquet(tmp_path / "detections.parquet")
    incidents = pd.read_parquet(tmp_path / "incidents.parquet")
    assert "ground_truth_event_id" not in observations.columns
    assert "ground_truth_type" not in observations.columns
    assert "ground_truth_event_id" not in detections.columns
    assert "ground_truth_type" not in detections.columns
    assert incidents["severity_score"].is_monotonic_decreasing

    metrics = json.loads((tmp_path / "evaluation_metrics.json").read_text())
    assert len(metrics["event_matches"]) == 12
    assert all(match["matched_incident_id"] for match in metrics["event_matches"])

