# SignalWatch

SignalWatch is a RF anomaly monitoring application. It will generate synthetic sensor observations, detect and group anomalous behaviour, and explain each incident through an interactive dashboard.

## Current milestone

Phase 1 provides the repository skeleton, Docker development environment, FastAPI health endpoint, and React connectivity shell. The synthetic data pipeline is intentionally a placeholder until Phase 2.

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

## Repository layout

- `backend/`: FastAPI application and batch analytics pipeline.
- `frontend/`: React, TypeScript, Vite, ECharts and TanStack Query dashboard.
- `data/`: generated Parquet, model and evaluation artifacts.
- `assets/`: design inspiration and Stitch exports; not application source code.

