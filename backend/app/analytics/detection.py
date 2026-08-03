from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.analytics.config import RAW_METRICS, SEED

DRIVER_NAMES = {
    "rssi_dbm": "RSSI",
    "snr_db": "SNR",
    "noise_floor_dbm": "Noise floor",
    "occupancy_pct": "Channel occupancy",
    "packet_loss_pct": "Packet loss",
    "frequency_offset_khz": "Frequency offset",
    "peer_noise": "Cross-channel noise",
}


@dataclass
class DetectionResult:
    scored_observations: pd.DataFrame
    detections: pd.DataFrame
    model_bundle: dict[str, object]


def detect_anomalies(
    frame: pd.DataFrame,
    feature_columns: list[str],
    baseline_values: dict[str, float],
) -> DetectionResult:
    model = IsolationForest(
        n_estimators=200,
        contamination=0.02,
        random_state=SEED,
        n_jobs=-1,
    )
    training_mask = frame["is_training"].to_numpy()
    evaluation_mask = ~training_mask
    model.fit(frame.loc[training_mask, feature_columns])

    evaluation_features = frame.loc[evaluation_mask, feature_columns].reset_index(drop=True)
    training_abnormality = -model.decision_function(frame.loc[training_mask, feature_columns])
    alert_threshold = float(np.quantile(training_abnormality, 0.995))
    abnormality = -model.decision_function(evaluation_features)
    flagged = abnormality >= alert_threshold
    severity = _calibrate_severity(abnormality, flagged)

    scored = frame.copy()
    scored["raw_anomaly_score"] = np.nan
    scored["severity_score"] = 0.0
    scored["is_anomaly"] = False
    scored.loc[evaluation_mask, "raw_anomaly_score"] = abnormality
    scored.loc[evaluation_mask, "severity_score"] = severity
    scored.loc[evaluation_mask, "is_anomaly"] = flagged

    detection_positions = np.flatnonzero(evaluation_mask)[flagged]
    detections = scored.iloc[detection_positions].copy().reset_index(drop=True)
    detections.insert(0, "detection_id", np.arange(1, len(detections) + 1, dtype=np.int64))
    detections["severity"] = detections["severity_score"].map(_severity_label)

    contribution_json = _counterfactual_contributions(
        model,
        evaluation_features.loc[flagged],
        abnormality[flagged],
        feature_columns,
        baseline_values,
    )
    detections["feature_contributions"] = contribution_json

    bundle: dict[str, object] = {
        "model": model,
        "feature_columns": feature_columns,
        "baseline_feature_values": baseline_values,
        "alert_threshold": alert_threshold,
        "seed": SEED,
    }
    return DetectionResult(scored, detections, bundle)


def _calibrate_severity(abnormality: np.ndarray, flagged: np.ndarray) -> np.ndarray:
    severity = np.zeros(len(abnormality), dtype=float)
    normal = ~flagged
    if normal.any():
        severity[normal] = (
            pd.Series(abnormality[normal]).rank(method="average", pct=True).to_numpy() * 49
        )
    count = int(flagged.sum())
    if count == 1:
        severity[flagged] = 100
    elif count > 1:
        ranks = pd.Series(abnormality[flagged]).rank(method="average").to_numpy() - 1
        severity[flagged] = 50 + 50 * ranks / (count - 1)
    return np.round(severity, 1)


def _severity_label(score: float) -> str:
    if score >= 90:
        return "critical"
    if score >= 80:
        return "high"
    if score >= 65:
        return "medium"
    return "low"


def _counterfactual_contributions(
    model: IsolationForest,
    features: pd.DataFrame,
    base_abnormality: np.ndarray,
    feature_columns: list[str],
    baseline_values: dict[str, float],
) -> list[str]:
    contributions = np.zeros((len(features), len(feature_columns)), dtype=float)
    for index, feature in enumerate(feature_columns):
        counterfactual = features.copy()
        counterfactual[feature] = baseline_values[feature]
        counterfactual_score = -model.decision_function(counterfactual)
        contributions[:, index] = np.maximum(base_abnormality - counterfactual_score, 0)

    output: list[str] = []
    for row in contributions:
        grouped: dict[str, float] = {}
        for feature, value in zip(feature_columns, row):
            driver = _driver_for_feature(feature)
            grouped[driver] = grouped.get(driver, 0.0) + float(value)
        total = sum(grouped.values())
        ranked = sorted(grouped.items(), key=lambda item: item[1], reverse=True)
        if total <= 0:
            payload = [{"feature": "Combined RF behaviour", "contribution_pct": 100.0}]
        else:
            payload = [
                {"feature": feature, "contribution_pct": round(value / total * 100, 1)}
                for feature, value in ranked[:3]
                if value > 0
            ]
        output.append(json.dumps(payload, separators=(",", ":")))
    return output


def _driver_for_feature(feature: str) -> str:
    if feature.startswith("peer_noise"):
        return DRIVER_NAMES["peer_noise"]
    for metric in RAW_METRICS:
        if feature.startswith(metric):
            return DRIVER_NAMES[metric]
    return feature
