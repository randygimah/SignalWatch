from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics.config import (
    FREQUENCIES_MHZ,
    INCIDENT_SPECS,
    INTERVAL_MINUTES,
    SEED,
    SENSOR_IDS,
    START_TIME,
    TOTAL_DAYS,
    TRAINING_DAYS,
)


def generate_observations(seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create deterministic normal RF behaviour and inject labelled evaluation incidents."""
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(
        START_TIME,
        periods=TOTAL_DAYS * 24 * (60 // INTERVAL_MINUTES),
        freq=f"{INTERVAL_MINUTES}min",
    )
    index = pd.MultiIndex.from_product(
        [timestamps, SENSOR_IDS, FREQUENCIES_MHZ],
        names=["timestamp", "sensor_id", "frequency_mhz"],
    )
    frame = index.to_frame(index=False)

    sensor_index = frame["sensor_id"].map(dict(zip(SENSOR_IDS, range(len(SENSOR_IDS))))).to_numpy()
    channel_index = frame["frequency_mhz"].map(
        dict(zip(FREQUENCIES_MHZ, range(len(FREQUENCIES_MHZ))))
    ).to_numpy()
    hour = frame["timestamp"].dt.hour.to_numpy() + frame["timestamp"].dt.minute.to_numpy() / 60
    elapsed_days = (frame["timestamp"] - frame["timestamp"].min()).dt.total_seconds().to_numpy() / 86400

    traffic = 0.52 + 0.27 * np.sin(2 * np.pi * (hour - 7) / 24)
    traffic += 0.08 * np.sin(4 * np.pi * (hour - 2) / 24)
    slow_drift = 0.4 * np.sin(2 * np.pi * elapsed_days / 6)
    sensor_noise_offset = np.array([-0.9, 0.6, 1.3])[sensor_index]
    sensor_signal_offset = np.array([1.2, -0.8, 0.4])[sensor_index]
    channel_wave = np.sin(channel_index * 0.9)

    frame["noise_floor_dbm"] = (
        -101.5
        + sensor_noise_offset
        + 2.0 * traffic
        + 0.7 * channel_wave
        + slow_drift
        + rng.normal(0, 0.75, len(frame))
    )
    frame["occupancy_pct"] = np.clip(
        19 + 34 * traffic + 2.0 * sensor_index + 2.5 * channel_wave + rng.normal(0, 3.2, len(frame)),
        0,
        100,
    )
    frame["rssi_dbm"] = (
        -84
        + 14 * traffic
        + sensor_signal_offset
        + 1.2 * channel_wave
        + 0.4 * slow_drift
        + rng.normal(0, 1.5, len(frame))
    )
    frame["snr_db"] = (
        frame["rssi_dbm"] - frame["noise_floor_dbm"] - 4.5 + rng.normal(0, 0.8, len(frame))
    )
    frame["packet_loss_pct"] = np.clip(
        0.35
        + np.maximum(0, 12 - frame["snr_db"].to_numpy()) * 1.4
        + frame["occupancy_pct"].to_numpy() * 0.018
        + rng.normal(0, 0.3, len(frame)),
        0,
        100,
    )
    frame["frequency_offset_khz"] = (
        np.array([-0.25, 0.35, 0.7])[sensor_index]
        + 0.15 * channel_wave
        + rng.normal(0, 0.55, len(frame))
    )

    frame["ground_truth_event_id"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    frame["ground_truth_type"] = pd.Series(pd.NA, index=frame.index, dtype="string")
    start = pd.Timestamp(START_TIME)
    truth_rows: list[dict[str, object]] = []

    for spec in INCIDENT_SPECS:
        event_start = start + pd.Timedelta(hours=spec.start_offset_hours)
        event_end = event_start + pd.Timedelta(minutes=spec.duration_minutes)
        affected_frequencies = FREQUENCIES_MHZ[
            spec.channel_start : spec.channel_start + spec.channel_count
        ]
        mask = (
            (frame["sensor_id"] == spec.sensor_id)
            & frame["frequency_mhz"].isin(affected_frequencies)
            & (frame["timestamp"] >= event_start)
            & (frame["timestamp"] < event_end)
        )
        _inject_event(frame, mask.to_numpy(), spec.anomaly_type, rng)
        frame.loc[mask, "ground_truth_event_id"] = spec.event_id
        frame.loc[mask, "ground_truth_type"] = spec.anomaly_type
        truth_rows.append(
            {
                "event_id": spec.event_id,
                "anomaly_type": spec.anomaly_type,
                "sensor_id": spec.sensor_id,
                "start_time": event_start,
                "end_time": event_end,
                "affected_frequencies": list(affected_frequencies),
            }
        )

    frame.insert(0, "observation_id", np.arange(1, len(frame) + 1, dtype=np.int64))
    training_cutoff = start + pd.Timedelta(days=TRAINING_DAYS)
    frame["is_training"] = frame["timestamp"] < training_cutoff
    truth = pd.DataFrame(truth_rows)
    return frame, truth


def _inject_event(
    frame: pd.DataFrame,
    mask: np.ndarray,
    anomaly_type: str,
    rng: np.random.Generator,
) -> None:
    count = int(mask.sum())
    if count == 0:
        return

    if anomaly_type == "broadband_interference":
        frame.loc[mask, "noise_floor_dbm"] += rng.normal(13.5, 0.8, count)
        frame.loc[mask, "rssi_dbm"] += rng.normal(7.0, 1.0, count)
        frame.loc[mask, "snr_db"] -= rng.normal(13.0, 1.0, count)
        frame.loc[mask, "occupancy_pct"] = np.clip(
            frame.loc[mask, "occupancy_pct"] + rng.normal(31, 3, count), 0, 100
        )
        frame.loc[mask, "packet_loss_pct"] = np.clip(
            frame.loc[mask, "packet_loss_pct"] + rng.normal(14, 2, count), 0, 100
        )
    elif anomaly_type == "narrowband_interference":
        frame.loc[mask, "noise_floor_dbm"] += rng.normal(7.0, 0.7, count)
        frame.loc[mask, "rssi_dbm"] += rng.normal(18.0, 1.2, count)
        frame.loc[mask, "snr_db"] -= rng.normal(6.0, 0.8, count)
        frame.loc[mask, "occupancy_pct"] = np.clip(
            frame.loc[mask, "occupancy_pct"] + rng.normal(42, 3, count), 0, 100
        )
        frame.loc[mask, "packet_loss_pct"] += rng.normal(5, 0.7, count)
    elif anomaly_type == "signal_dropout":
        frame.loc[mask, "rssi_dbm"] -= rng.normal(23.0, 1.0, count)
        frame.loc[mask, "snr_db"] -= rng.normal(19.0, 1.0, count)
        frame.loc[mask, "occupancy_pct"] = np.clip(
            frame.loc[mask, "occupancy_pct"] - rng.normal(17, 2, count), 0, 100
        )
        frame.loc[mask, "packet_loss_pct"] = np.clip(
            frame.loc[mask, "packet_loss_pct"] + rng.normal(39, 3, count), 0, 100
        )
    elif anomaly_type == "sensor_malfunction":
        frame.loc[mask, "noise_floor_dbm"] = rng.normal(-72, 0.12, count)
        frame.loc[mask, "rssi_dbm"] = rng.normal(-71, 0.12, count)
        frame.loc[mask, "snr_db"] = rng.normal(0.3, 0.08, count)
        frame.loc[mask, "occupancy_pct"] = rng.normal(50, 0.1, count)
        frame.loc[mask, "packet_loss_pct"] = rng.normal(57, 0.2, count)
        frame.loc[mask, "frequency_offset_khz"] = rng.normal(21, 0.15, count)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_type}")

