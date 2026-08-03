from dataclasses import dataclass

import numpy as np

SEED = 42
START_TIME = "2026-07-01T00:00:00Z"
INTERVAL_MINUTES = 5
TOTAL_DAYS = 14
TRAINING_DAYS = 7
SENSOR_IDS = ("RX-NORTH", "RX-CENTRAL", "RX-SOUTH")
FREQUENCIES_MHZ = tuple(np.round(433.05 + np.arange(8) * 0.25, 2))

RAW_METRICS = (
    "rssi_dbm",
    "snr_db",
    "noise_floor_dbm",
    "occupancy_pct",
    "packet_loss_pct",
    "frequency_offset_khz",
)


@dataclass(frozen=True)
class IncidentSpec:
    event_id: str
    anomaly_type: str
    sensor_id: str
    start_offset_hours: float
    duration_minutes: int
    channel_start: int
    channel_count: int


INCIDENT_SPECS = (
    IncidentSpec("GT-001", "broadband_interference", "RX-NORTH", 7 * 24 + 9, 45, 1, 6),
    IncidentSpec("GT-002", "broadband_interference", "RX-CENTRAL", 9 * 24 + 14, 35, 0, 5),
    IncidentSpec("GT-003", "broadband_interference", "RX-SOUTH", 12 * 24 + 19, 55, 2, 6),
    IncidentSpec("GT-004", "narrowband_interference", "RX-CENTRAL", 7 * 24 + 17, 30, 3, 1),
    IncidentSpec("GT-005", "narrowband_interference", "RX-SOUTH", 10 * 24 + 11, 40, 6, 1),
    IncidentSpec("GT-006", "narrowband_interference", "RX-NORTH", 13 * 24 + 7, 25, 1, 2),
    IncidentSpec("GT-007", "signal_dropout", "RX-SOUTH", 8 * 24 + 5, 35, 0, 2),
    IncidentSpec("GT-008", "signal_dropout", "RX-NORTH", 10 * 24 + 22, 50, 4, 2),
    IncidentSpec("GT-009", "signal_dropout", "RX-CENTRAL", 12 * 24 + 8, 30, 6, 2),
    IncidentSpec("GT-010", "sensor_malfunction", "RX-NORTH", 8 * 24 + 15, 25, 0, 8),
    IncidentSpec("GT-011", "sensor_malfunction", "RX-SOUTH", 11 * 24 + 3, 40, 0, 8),
    IncidentSpec("GT-012", "sensor_malfunction", "RX-CENTRAL", 13 * 24 + 16, 30, 0, 8),
)

