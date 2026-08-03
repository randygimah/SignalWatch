from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics.config import RAW_METRICS

MAD_FLOORS = {
    "rssi_dbm": 0.5,
    "snr_db": 0.5,
    "noise_floor_dbm": 0.25,
    "occupancy_pct": 1.0,
    "packet_loss_pct": 0.15,
    "frequency_offset_khz": 0.1,
}


def build_feature_frame(observations: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict[str, float]]:
    frame = observations.copy().sort_values(["sensor_id", "frequency_mhz", "timestamp"])
    frame["hour"] = frame["timestamp"].dt.hour
    training = frame[frame["is_training"]]

    baseline_parts: list[pd.DataFrame] = []
    keys = ["sensor_id", "frequency_mhz", "hour"]
    for metric in RAW_METRICS:
        grouped = training.groupby(keys, observed=True)[metric]
        part = grouped.agg(
            **{
                f"expected_{metric}": "median",
                f"lower_{metric}": lambda values: values.quantile(0.05),
                f"upper_{metric}": lambda values: values.quantile(0.95),
                f"mad_{metric}": lambda values: np.median(
                    np.abs(values - np.median(values))
                ),
            }
        ).reset_index()
        baseline_parts.append(part)

    baseline = baseline_parts[0]
    for part in baseline_parts[1:]:
        baseline = baseline.merge(part, on=keys, how="inner", validate="one_to_one")
    frame = frame.merge(baseline, on=keys, how="left", validate="many_to_one")

    feature_columns: list[str] = []
    baseline_values: dict[str, float] = {}
    for metric in RAW_METRICS:
        scale = (1.4826 * frame[f"mad_{metric}"]).clip(lower=MAD_FLOORS[metric])
        column = f"{metric}_z"
        frame[column] = (frame[metric] - frame[f"expected_{metric}"]) / scale
        feature_columns.append(column)
        baseline_values[column] = 0.0

    grouped = frame.groupby(["sensor_id", "frequency_mhz"], sort=False, observed=True)
    for metric in ("noise_floor_dbm", "rssi_dbm", "snr_db"):
        raw_change = grouped[metric].diff().fillna(0)
        train_scale = max(float(raw_change[frame["is_training"]].std()), MAD_FLOORS[metric])
        column = f"{metric}_change_z"
        frame[column] = raw_change / train_scale
        feature_columns.append(column)
        baseline_values[column] = 0.0

    for metric in ("noise_floor_dbm", "snr_db"):
        volatility = grouped[metric].transform(
            lambda values: values.rolling(6, min_periods=2).std()
        ).fillna(0)
        normal_volatility = (
            pd.DataFrame(
                {
                    "sensor_id": frame.loc[frame["is_training"], "sensor_id"],
                    "frequency_mhz": frame.loc[frame["is_training"], "frequency_mhz"],
                    "volatility": volatility[frame["is_training"]],
                }
            )
            .groupby(["sensor_id", "frequency_mhz"], observed=True)["volatility"]
            .median()
            .rename("normal_volatility")
            .reset_index()
        )
        lookup = frame[["sensor_id", "frequency_mhz"]].merge(
            normal_volatility,
            on=["sensor_id", "frequency_mhz"],
            how="left",
        )["normal_volatility"].clip(lower=0.05)
        column = f"{metric}_volatility_ratio"
        frame[column] = volatility.to_numpy() / lookup.to_numpy()
        feature_columns.append(column)
        baseline_values[column] = 1.0

    noise_column = "noise_floor_dbm_z"
    peers = frame.groupby(["timestamp", "sensor_id"], observed=True)[noise_column]
    frame["peer_noise_z_mean"] = peers.transform("mean")
    frame["peer_noise_high_count"] = peers.transform(lambda values: (values > 3).sum())
    feature_columns.extend(["peer_noise_z_mean", "peer_noise_high_count"])
    baseline_values.update({"peer_noise_z_mean": 0.0, "peer_noise_high_count": 0.0})

    frame = frame.sort_values("observation_id").reset_index(drop=True)
    return frame, feature_columns, baseline_values

