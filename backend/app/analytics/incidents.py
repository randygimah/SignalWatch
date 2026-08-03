from __future__ import annotations

import json

import numpy as np
import pandas as pd

from app.analytics.config import FREQUENCIES_MHZ, RAW_METRICS
from app.analytics.detection import DRIVER_NAMES

METRIC_UNITS = {
    "rssi_dbm": "dBm",
    "snr_db": "dB",
    "noise_floor_dbm": "dBm",
    "occupancy_pct": "%",
    "packet_loss_pct": "%",
    "frequency_offset_khz": "kHz",
}


def group_incidents(detections: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Group nearby, adjacent-channel detections into analyst-facing incidents."""
    if detections.empty:
        return pd.DataFrame(), detections.assign(incident_id=pd.Series(dtype="string"))

    working = detections.copy().reset_index(drop=True)
    parent = np.arange(len(working))
    channel_lookup = {frequency: index for index, frequency in enumerate(FREQUENCIES_MHZ)}

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = int(parent[index])
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for _, sensor_rows in working.groupby("sensor_id", sort=True, observed=True):
        ordered = sensor_rows.sort_values(["timestamp", "frequency_mhz"]).index.to_list()
        for offset, current_index in enumerate(ordered):
            current = working.loc[current_index]
            current_channel = channel_lookup[float(current["frequency_mhz"])]
            for previous_index in reversed(ordered[:offset]):
                previous = working.loc[previous_index]
                delta_minutes = (current["timestamp"] - previous["timestamp"]).total_seconds() / 60
                if delta_minutes > 10:
                    break
                previous_channel = channel_lookup[float(previous["frequency_mhz"])]
                if abs(current_channel - previous_channel) <= 1:
                    union(current_index, previous_index)

    components: dict[int, list[int]] = {}
    for index in range(len(working)):
        components.setdefault(find(index), []).append(index)
    ordered_components = sorted(
        components.values(),
        key=lambda indices: working.loc[indices, "timestamp"].min(),
    )
    ordered_components = [
        indices
        for indices in ordered_components
        if len(indices) >= 2 or float(working.loc[indices, "severity_score"].max()) >= 90
    ]

    incident_rows: list[dict[str, object]] = []
    incident_ids = pd.Series(index=working.index, dtype="string")
    for number, indices in enumerate(ordered_components, start=1):
        rows = working.loc[indices].sort_values(["timestamp", "frequency_mhz"])
        incident_id = f"INC-{number:04d}"
        incident_ids.loc[indices] = incident_id
        incident_rows.append(_summarise_incident(incident_id, rows))

    working["incident_id"] = incident_ids
    incidents = pd.DataFrame(incident_rows).sort_values(
        ["severity_score", "start_time"], ascending=[False, True]
    ).reset_index(drop=True)
    return incidents, working


def _summarise_incident(incident_id: str, rows: pd.DataFrame) -> dict[str, object]:
    frequencies = sorted(float(value) for value in rows["frequency_mhz"].unique())
    duration_minutes = max(
        5,
        int((rows["timestamp"].max() - rows["timestamp"].min()).total_seconds() / 60) + 5,
    )
    z_medians = {metric: float(rows[f"{metric}_z"].median()) for metric in RAW_METRICS}
    incident_type = _classify_incident(rows, z_medians, len(frequencies))
    title = {
        "sensor_malfunction": "Sensor malfunction",
        "signal_dropout": "Signal dropout",
        "broadband_interference": "Broadband interference",
        "narrowband_interference": "Narrowband interference",
        "unusual_rf_pattern": "Unusual RF pattern",
    }[incident_type]
    severity_score = round(float(rows["severity_score"].quantile(0.95)), 1)
    severity = _incident_severity(severity_score)
    comparisons = _metric_comparisons(rows, z_medians)
    contributions = _aggregate_contributions(rows["feature_contributions"])

    return {
        "incident_id": incident_id,
        "incident_type": incident_type,
        "title": title,
        "sensor_id": str(rows["sensor_id"].iloc[0]),
        "start_time": rows["timestamp"].min(),
        "end_time": rows["timestamp"].max() + pd.Timedelta(minutes=5),
        "duration_minutes": duration_minutes,
        "severity_score": severity_score,
        "severity": severity,
        "affected_frequencies": json.dumps(frequencies, separators=(",", ":")),
        "detection_count": len(rows),
        "summary": _plain_language_summary(
            incident_type, rows, frequencies, duration_minutes
        ),
        "pattern_description": _pattern_description(len(frequencies), duration_minutes, len(rows)),
        "feature_contributions": json.dumps(contributions, separators=(",", ":")),
        "metric_comparisons": json.dumps(comparisons, separators=(",", ":")),
        "detection_ids": json.dumps(
            [int(value) for value in rows["detection_id"]], separators=(",", ":")
        ),
    }


def _classify_incident(
    rows: pd.DataFrame, z: dict[str, float], channel_count: int
) -> str:
    if abs(z["frequency_offset_khz"]) > 8 and z["packet_loss_pct"] > 5:
        return "sensor_malfunction"
    if z["rssi_dbm"] < -5 and z["packet_loss_pct"] > 5:
        return "signal_dropout"
    if rows["peer_noise_high_count"].median() >= 3 and z["noise_floor_dbm"] > 4:
        return "broadband_interference"
    narrowband_core = rows[(rows["occupancy_pct_z"] > 5) & (rows["rssi_dbm_z"] > 7)]
    narrowband_channels = narrowband_core["frequency_mhz"].nunique()
    if len(narrowband_core) >= 2 and 1 <= narrowband_channels <= 2:
        return "narrowband_interference"
    if channel_count >= 3 and z["noise_floor_dbm"] > 4:
        return "broadband_interference"
    if z["occupancy_pct"] > 4 or z["rssi_dbm"] > 4:
        return "narrowband_interference"
    return "unusual_rf_pattern"


def _incident_severity(score: float) -> str:
    if score >= 90:
        return "critical"
    if score >= 80:
        return "high"
    if score >= 65:
        return "medium"
    return "low"


def _metric_comparisons(
    rows: pd.DataFrame, z_medians: dict[str, float]
) -> list[dict[str, object]]:
    metrics = sorted(RAW_METRICS, key=lambda metric: abs(z_medians[metric]), reverse=True)[:3]
    output: list[dict[str, object]] = []
    for metric in metrics:
        actual = float(rows[metric].median())
        expected = float(rows[f"expected_{metric}"].median())
        output.append(
            {
                "metric": DRIVER_NAMES[metric],
                "actual": round(actual, 2),
                "expected": round(expected, 2),
                "difference": round(actual - expected, 2),
                "unit": METRIC_UNITS[metric],
            }
        )
    return output


def _aggregate_contributions(values: pd.Series) -> list[dict[str, object]]:
    totals: dict[str, float] = {}
    for value in values:
        for contribution in json.loads(value):
            feature = contribution["feature"]
            totals[feature] = totals.get(feature, 0) + float(contribution["contribution_pct"])
    overall = sum(totals.values()) or 1
    return [
        {"feature": feature, "contribution_pct": round(value / overall * 100, 1)}
        for feature, value in sorted(totals.items(), key=lambda item: item[1], reverse=True)[:3]
    ]


def _plain_language_summary(
    incident_type: str,
    rows: pd.DataFrame,
    frequencies: list[float],
    duration_minutes: int,
) -> str:
    noise_delta = float((rows["noise_floor_dbm"] - rows["expected_noise_floor_dbm"]).median())
    snr_actual = float(rows["snr_db"].median())
    snr_expected = float(rows["expected_snr_db"].median())
    snr_change_pct = abs((snr_actual - snr_expected) / max(abs(snr_expected), 0.1) * 100)
    packet_loss = float(rows["packet_loss_pct"].median())
    channel_phrase = f"{len(frequencies)} adjacent channel{'s' if len(frequencies) != 1 else ''}"

    if incident_type == "broadband_interference":
        return (
            f"Noise rose across {channel_phrase} for {duration_minutes} minutes. "
            f"The noise floor was {noise_delta:.1f} dB above normal, SNR changed by "
            f"{snr_change_pct:.0f}%, and packet loss reached {packet_loss:.1f}%."
        )
    if incident_type == "signal_dropout":
        rssi_delta = float((rows["rssi_dbm"] - rows["expected_rssi_dbm"]).median())
        return (
            f"Signal strength dropped {abs(rssi_delta):.1f} dB below normal across "
            f"{channel_phrase} for {duration_minutes} minutes, while packet loss reached "
            f"{packet_loss:.1f}%."
        )
    if incident_type == "sensor_malfunction":
        offset = float(rows["frequency_offset_khz"].median())
        return (
            f"Multiple measurements moved outside the sensor's normal operating range across "
            f"{channel_phrase}. Frequency offset reached {offset:.1f} kHz and packet loss "
            f"reached {packet_loss:.1f}%."
        )
    if incident_type == "narrowband_interference":
        occupancy = float(rows["occupancy_pct"].median())
        return (
            f"A concentrated RF disturbance affected {channel_phrase} for {duration_minutes} "
            f"minutes. Channel occupancy reached {occupancy:.1f}% and the noise floor moved "
            f"{noise_delta:.1f} dB from normal."
        )
    return (
        f"An unusual combination of RF measurements persisted for {duration_minutes} minutes "
        f"across {channel_phrase}."
    )


def _pattern_description(channel_count: int, duration_minutes: int, detection_count: int) -> str:
    if channel_count >= 3:
        return (
            f"This is a coordinated multi-channel pattern: {detection_count} unusual readings "
            f"were linked across {channel_count} adjacent channels."
        )
    if duration_minutes > 10:
        return (
            f"This is a sustained pattern rather than a single spike: {detection_count} unusual "
            f"readings continued for {duration_minutes} minutes."
        )
    return "This appears isolated: only a short run of closely related readings was detected."
