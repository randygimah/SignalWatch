"""Render README figures from pipeline artifacts.

Usage (from backend/): uv run --with matplotlib python ../scripts/make_figures.py [DATA_DIR] [OUT_DIR]
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "docs" / "images"

# Same severity colours and ink as the dashboard (frontend/src/components/SignalTimeline.tsx).
SEVERITY = {"low": "#8ba8d9", "medium": "#f0a21a", "high": "#ed6a3a", "critical": "#c5222b"}
BANDS = [(0, 65, "low"), (65, 80, "medium"), (80, 90, "high"), (90, 100, "critical")]
INK, MUTED, GRID = "#111c2d", "#697184", "#e8edf6"
TYPES = {
    "broadband_interference": "Broadband\ninterference",
    "narrowband_interference": "Narrowband\ninterference",
    "sensor_malfunction": "Sensor\nmalfunction",
    "signal_dropout": "Signal\ndropout",
    "unusual_rf_pattern": "Unusual RF\npattern",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "text.color": INK,
    "axes.labelcolor": MUTED,
    "axes.edgecolor": GRID,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

incidents = pd.read_parquet(DATA / "incidents.parquet")
metrics = json.loads((DATA / "evaluation_metrics.json").read_text())
matched = {m["matched_incident_id"] for m in metrics["event_matches"]}
assert set(incidents.incident_type) <= set(TYPES), "unknown incident type; extend TYPES"


def severity_by_type(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.4), dpi=200)
    for low, high, name in BANDS:
        ax.axhspan(low, high, color=SEVERITY[name], alpha=0.08, lw=0)
        ax.text(4.62, (low + high) / 2 if low else 55, name, va="center", ha="left",
                color=MUTED, fontsize=8.5)
    rng = np.random.default_rng(42)
    for x, kind in enumerate(TYPES):
        rows = incidents[incidents.incident_type == kind]
        jitter = rng.uniform(-0.18, 0.18, len(rows))
        for (_, row), dx in zip(rows.iterrows(), jitter):
            injected = row.incident_id in matched
            ax.scatter(x + dx, row.severity_score, s=64 if injected else 34,
                       color=SEVERITY[row.severity], edgecolor=INK if injected else "white",
                       linewidth=1.2 if injected else 0.8, zorder=3)
        ax.text(x, 101.5, f"n = {len(rows)}", ha="center", color=MUTED, fontsize=8.5)
    ax.set_xticks(range(len(TYPES)), TYPES.values())
    ax.set_xlim(-0.6, 5.1)
    ax.set_ylim(min(45, incidents.severity_score.min() - 3), 104)
    ax.set_ylabel("Severity score (0–100)")
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.scatter([], [], s=64, color="white", edgecolor=INK, linewidth=1.2,
               label="Matched to an injected ground-truth event")
    ax.legend(loc="lower left", frameon=False, fontsize=8.5)
    ax.set_title(f"All {metrics['injected_incidents']} injected events are detected and typed correctly; "
                 "unlabelled detections stay low or medium", loc="left", fontsize=11, pad=18)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def contribution_heatmap(path: Path) -> None:
    rows = [
        {"type": kind, "feature": c["feature"], "pct": c["contribution_pct"]}
        for kind, raw in zip(incidents.incident_type, incidents.feature_contributions)
        for c in json.loads(raw)
    ]
    # Top-3 contributions per incident; a dimension outside an incident's top 3 counts as 0.
    totals = pd.DataFrame(rows).pivot_table(index="type", columns="feature", values="pct", aggfunc="sum")
    table = totals.div(incidents.incident_type.value_counts(), axis=0).fillna(0)
    table = table.reindex(list(TYPES))
    table = table[table.max()[table.max() >= 1].sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=200)
    ax.imshow(table.values, cmap="Blues", vmin=0, vmax=table.values.max(), aspect="auto")
    for (i, j), value in np.ndenumerate(table.values):
        if value >= 1:
            ax.text(j, i, f"{value:.0f}%", ha="center", va="center", fontsize=8.5,
                    color="white" if value > table.values.max() * 0.55 else INK)
    ax.set_xticks(range(table.shape[1]), table.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(TYPES)), [t.replace("\n", " ") for t in TYPES.values()])
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("What drove each alert: mean counterfactual contribution by incident type",
                 loc="left", fontsize=11, pad=10)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


OUT.mkdir(parents=True, exist_ok=True)
severity_by_type(OUT / "severity-by-type.png")
contribution_heatmap(OUT / "feature-contributions.png")
print(f"Wrote figures to {OUT}")
