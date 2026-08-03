# SignalWatch

SignalWatch is a RF anomaly monitoring application. It will generate synthetic sensor observations, detect and group anomalous behaviour, and explain each incident through an interactive dashboard.

## Current milestone

Phase 2 provides a deterministic synthetic RF dataset and batch anomaly pipeline. The dashboard remains a connectivity shell until the API and visualization phases.

## Prerequisites

- Docker with Docker Compose
- Make

## Run locally

```bash
make demo
```

Open the dashboard at <http://localhost:5173> and the API documentation at <http://localhost:8000/docs>.

## Common commands

```bash
make generate  # run the batch pipeline
make build     # build all containers
make test      # run backend and frontend tests
make down      # stop the stack
```

## Synthetic RF pipeline

`make generate` creates fourteen days of five-minute readings for three sensors and eight adjacent channels. The first week establishes normal behaviour; the second contains twelve evaluation-only incidents covering broadband interference, narrowband interference, signal dropout and sensor malfunction.

The pipeline computes sensor/channel/hour baselines, engineers deviation and temporal features, trains a 200-tree Isolation Forest, applies a conservative threshold derived from the clean training distribution, and converts anomalous margins into a 0–100 severity score. Related detections are grouped by sensor, time and adjacent frequency. Per-feature counterfactual rescoring supplies the explanation drivers.

Generated files under `data/` are intentionally Git-ignored:

- `observations.parquet`: public time-series values, expected values and model scores.
- `detections.parquet`: anomalous points and counterfactual feature contributions.
- `incidents.parquet`: ranked, grouped incidents and deterministic explanations.
- `isolation_forest.joblib`: trained model plus feature metadata.
- `evaluation_metrics.json`: ground-truth evaluation used during development only.
- `metadata.json`: row counts, feature list and artifact hashes.

Synthetic ground-truth labels are never written into the public observation, detection, or incident artifacts.

## Repository layout

- `backend/`: FastAPI application and batch analytics pipeline.
- `frontend/`: React, TypeScript, Vite, ECharts and TanStack Query dashboard.
- `data/`: generated Parquet, model and evaluation artifacts.
- `assets/`: design inspiration and Stitch exports; not application source code.
