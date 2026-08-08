# SignalWatch MVP Implementation Plan

## Summary

SignalWatch is a Dockerized RF anomaly-monitoring application. It generates synthetic radio-frequency observations, detects anomalous behaviour with Isolation Forest, groups related detections into incidents, and explains each incident through baseline comparisons and feature contributions.

Development is split into five reviewable phases. Each phase ends with verification and a review gate before the next phase begins.

| Phase | Status | Outcome |
| --- | --- | --- |
| 1. Repository skeleton | Complete | Dockerized React and FastAPI foundation |
| 2. Synthetic data and ML pipeline | Complete | Reproducible scored RF dataset and grouped incidents |
| 3. Query API | Complete | Filtered, versioned analytics endpoints |
| 4. Interactive dashboard | Complete | Analyst-facing exploration and explanation UI |
| 5. Integration and demo hardening | Complete | Recoverable startup, cross-view integration coverage, and demo documentation |

The Stitch exports are visual inspiration, not a specification. SignalWatch will retain their typography, restrained palette, summary cards, chart-and-incident layout, heatmap, and explanation drawer. Decorative navigation, search, notifications, profiles, maps, unsupported pages, and placeholder visualizations remain out of scope.

## Phase 1 — Repository Skeleton

**Status:** Complete and pushed to `main` in commit `17cbc7c`.

### Delivered

- Initialized a Git repository and standardized the design asset path as `assets/`.
- Scaffolded a React 19, TypeScript, Vite, Tailwind CSS, ECharts, and TanStack Query frontend.
- Scaffolded a Python 3.12 FastAPI backend managed with `uv`.
- Added Docker Compose services for the batch pipeline, API, and web application.
- Added locked dependencies, environment examples, ignore rules, formatting defaults, and root commands.
- Implemented `GET /api/v1/health` and a frontend API-connectivity indicator.
- Added backend and frontend smoke tests.

### Commands

```bash
make generate
make demo
make test
make down
```

### Acceptance evidence

- All three Docker images build successfully.
- The API becomes healthy and returns the service name and version.
- The frontend responds on port `5173` and confirms API connectivity.
- Backend lint, backend tests, frontend tests, and the production frontend build pass.

### Relevant files

Repository and container foundation:

- [`.editorconfig`](../.editorconfig)
- [`.env.example`](../.env.example)
- [`.gitignore`](../.gitignore)
- [`Makefile`](../Makefile)
- [`README.md`](../README.md)
- [`compose.yaml`](../compose.yaml)
- [`data/.gitkeep`](../data/.gitkeep)

Backend foundation:

- [`backend/Dockerfile`](../backend/Dockerfile)
- [`backend/pyproject.toml`](../backend/pyproject.toml)
- [`backend/uv.lock`](../backend/uv.lock)
- [`backend/app/__init__.py`](../backend/app/__init__.py)
- [`backend/app/main.py`](../backend/app/main.py)
- [`backend/tests/test_health.py`](../backend/tests/test_health.py)

Frontend foundation:

- [`frontend/Dockerfile`](../frontend/Dockerfile)
- [`frontend/package.json`](../frontend/package.json)
- [`frontend/package-lock.json`](../frontend/package-lock.json)
- [`frontend/index.html`](../frontend/index.html)
- [`frontend/vite.config.ts`](../frontend/vite.config.ts)
- [`frontend/tsconfig.json`](../frontend/tsconfig.json)
- [`frontend/tsconfig.app.json`](../frontend/tsconfig.app.json)
- [`frontend/tsconfig.node.json`](../frontend/tsconfig.node.json)
- [`frontend/src/vite-env.d.ts`](../frontend/src/vite-env.d.ts)
- [`frontend/src/main.tsx`](../frontend/src/main.tsx)
- [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- [`frontend/src/api.ts`](../frontend/src/api.ts)
- [`frontend/src/index.css`](../frontend/src/index.css)
- [`frontend/src/App.test.tsx`](../frontend/src/App.test.tsx)
- [`frontend/src/test/setup.ts`](../frontend/src/test/setup.ts)

## Phase 2 — Synthetic Data and ML Pipeline

**Status:** Complete and approved.

### Delivered

- Generate 14 days of deterministic five-minute observations for three sensors and eight adjacent RF channels.
- Use the first seven days as clean training data and inject twelve evaluation incidents into the second week:
  - Broadband interference
  - Narrowband interference
  - Signal dropout
  - Sensor malfunction
- Model sensor and channel differences, time-of-day behaviour, correlated metrics, slow drift, and measurement noise.
- Calculate sensor/channel/hour baselines and engineer deviation, temporal-change, rolling-volatility, and cross-channel features.
- Train a seed-42 Isolation Forest with 200 estimators and 2% contamination.
- Apply a conservative alert threshold derived from the clean training-score distribution.
- Convert anomalous margins into ranked severity scores from 0–100.
- Estimate explanation drivers by replacing each model feature with its normal baseline and measuring the reduction in anomaly score.
- Group related detections by sensor, ten-minute proximity, and adjacent frequency.
- Suppress isolated low-confidence points from the analyst-facing incident list while retaining them in detection evidence.
- Classify grouped incidents with deterministic, interpretable RF rules and generate plain-language explanations.
- Persist observations, detections, incidents, the trained model, evaluation results, and artifact metadata.
- Keep injected labels out of all public observation, detection, and incident artifacts.

### Evaluation result

| Metric | Result | Required |
| --- | ---: | ---: |
| Total observations | 96,768 | 96,768 |
| Injected incidents detected | 12 / 12 | At least 70% |
| Incident recall | 100% | At least 70% |
| Clean-observation false-positive rate | 0.77% | Below 5% |
| Injected root-cause classification accuracy | 100% | Informational |
| Surfaced grouped incidents | 51 | Manageable ranked set |

Severity distribution: eight critical, one high, twenty-six medium, and sixteen low incidents.

### Generated artifacts

The following Git-ignored files are created under `data/` by `make generate`:

- `observations.parquet`
- `detections.parquet`
- `incidents.parquet`
- `isolation_forest.joblib`
- `evaluation_metrics.json`
- `metadata.json`

### Relevant files

- [`backend/app/analytics/__init__.py`](../backend/app/analytics/__init__.py)
- [`backend/app/analytics/config.py`](../backend/app/analytics/config.py) — dataset constants, RF channels, sensors, seed, and injected-event specifications.
- [`backend/app/analytics/synthetic.py`](../backend/app/analytics/synthetic.py) — normal RF behaviour and evaluation incident generation.
- [`backend/app/analytics/features.py`](../backend/app/analytics/features.py) — normal baselines and model feature engineering.
- [`backend/app/analytics/detection.py`](../backend/app/analytics/detection.py) — Isolation Forest training, score calibration, and counterfactual contributions.
- [`backend/app/analytics/incidents.py`](../backend/app/analytics/incidents.py) — grouping, root-cause rules, comparisons, and explanations.
- [`backend/app/pipeline.py`](../backend/app/pipeline.py) — end-to-end orchestration, persistence, metadata, and evaluation.
- [`backend/tests/test_pipeline.py`](../backend/tests/test_pipeline.py) — reproducibility, quality, ordering, and label-leakage tests.
- [`backend/pyproject.toml`](../backend/pyproject.toml) and [`backend/uv.lock`](../backend/uv.lock) — analytics dependencies and locked versions.
- [`compose.yaml`](../compose.yaml) and [`Makefile`](../Makefile) — containerized pipeline execution.
- [`README.md`](../README.md) — pipeline usage and artifact descriptions.
- [`data/.gitkeep`](../data/.gitkeep) — generated-artifact directory placeholder.

## Phase 3 — Query API

**Status:** Complete.

### Delivered endpoints

```http
GET /api/v1/health
GET /api/v1/overview
GET /api/v1/observations
GET /api/v1/anomalies
GET /api/v1/anomalies/{id}
GET /api/v1/heatmap
```

### Delivered behaviour

- Load generated Parquet artifacts once during application startup and expose a clear `503` unavailable-artifact error when generation has not run.
- Filter applicable endpoints by UTC time range, sensor, frequency, minimum severity, and incident type.
- Return grouped incidents ranked by numeric severity.
- Downsample time-series responses to at most 1,000 points while retaining normal bounds and severe points.
- Return actual values, expected values, normal bounds, severity, and incident relationships.
- Return an incident summary, duration, affected frequencies, metric comparisons, top contributions, pattern description, and supporting detections.
- Validate unknown sensors, frequencies, metrics, types, malformed timestamps, and reversed ranges.
- Return `404` for unknown incident IDs.
- Add API contract, filter, failure-path, and artifact-loading tests.
- Publish typed response schemas in OpenAPI for summary, observation, incident, detail, and heatmap payloads.
- Include available sensors and frequencies in observation metadata for the dashboard filter controls.

### Acceptance evidence

- All six endpoints are published under `/api/v1` and visible in OpenAPI.
- Observation results never exceed 1,000 points and retain all 742 anomalous points in the unfiltered demo dataset.
- Incident results remain ordered by descending numeric severity.
- Domain validation covers timestamps, sensors, frequencies, metrics, severity values, and incident types.
- Missing incidents return `404`; missing generated artifacts return `503` with recovery instructions.
- Twelve dedicated API tests pass alongside the pipeline and health suites.

### Relevant files

- [`backend/app/main.py`](../backend/app/main.py)
- [`backend/app/__init__.py`](../backend/app/__init__.py)
- [`backend/app/api/__init__.py`](../backend/app/api/__init__.py)
- [`backend/app/api/dependencies.py`](../backend/app/api/dependencies.py)
- [`backend/app/api/routes.py`](../backend/app/api/routes.py)
- [`backend/app/api/schemas.py`](../backend/app/api/schemas.py)
- [`backend/app/repositories/__init__.py`](../backend/app/repositories/__init__.py)
- [`backend/app/repositories/artifacts.py`](../backend/app/repositories/artifacts.py)
- [`backend/tests/test_api.py`](../backend/tests/test_api.py)
- [`backend/tests/test_health.py`](../backend/tests/test_health.py)
- [`backend/pyproject.toml`](../backend/pyproject.toml)
- [`compose.yaml`](../compose.yaml)
- [`data/.gitkeep`](../data/.gitkeep)

## Phase 4 — Interactive Dashboard

**Status:** Complete.

### Delivered behaviour

- Build one responsive desktop dashboard backed entirely by the Phase 3 API.
- Add global time, sensor, frequency, severity, and incident-type filters.
- Show summary cards for incidents, critical incidents, affected sensors, and anomaly rate.
- Add an ECharts time-series with selectable metric, actual values, expected-normal band, severity markers, tooltips, and drag-to-zoom navigation.
- Place a severity-ranked incident list beside the main chart.
- Add a channel-by-time anomaly heatmap beneath the chart.
- Use shared selection state so chart markers, incident cards, and heatmap cells open the same drawer.
- Show incident name, severity, explanation, actual-versus-expected metrics, comparison chart, top contribution bars, duration, affected frequencies, and pattern context in the drawer.
- Include loading, empty, and request-error states for each data region.
- Keep the timeline analytically coherent by using a labelled focus channel when global frequency is set to all channels.

### Visual direction

- Retain Hanken Grotesk and JetBrains Mono.
- Use navy typography, blue nominal data, amber warnings, and coral-red severe anomalies.
- Use restrained white cards, subtle borders, and generous whitespace.
- Do not add the Stitch side rail, unsupported pages, search, profile, notifications, settings, map, archive, reports, or static placeholder charts.

### Acceptance evidence

- Summary cards, incidents, timeline, and heatmap load from live API responses.
- Severity filtering updates all four regions consistently.
- Ranked incidents open a populated detail drawer with comparisons and model drivers.
- The signal chart presents its expected-normal range at the correct RF baseline and retains anomaly markers.
- The heatmap exposes adjacent-channel patterns using severity colour.
- Loading, empty, API-error, and drawer-error states are implemented.
- Two frontend interaction/error tests and the production TypeScript build pass.
- Local browser inspection reports no runtime console errors.

### Relevant files

- [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- [`frontend/src/api.ts`](../frontend/src/api.ts)
- [`frontend/src/types.ts`](../frontend/src/types.ts)
- [`frontend/src/index.css`](../frontend/src/index.css)
- [`frontend/src/main.tsx`](../frontend/src/main.tsx)
- [`frontend/src/App.test.tsx`](../frontend/src/App.test.tsx)
- [`frontend/src/test/setup.ts`](../frontend/src/test/setup.ts)
- [`frontend/src/components/FilterBar.tsx`](../frontend/src/components/FilterBar.tsx)
- [`frontend/src/components/SummaryCards.tsx`](../frontend/src/components/SummaryCards.tsx)
- [`frontend/src/components/SignalTimeline.tsx`](../frontend/src/components/SignalTimeline.tsx)
- [`frontend/src/components/IncidentList.tsx`](../frontend/src/components/IncidentList.tsx)
- [`frontend/src/components/AnomalyHeatmap.tsx`](../frontend/src/components/AnomalyHeatmap.tsx)
- [`frontend/src/components/IncidentDrawer.tsx`](../frontend/src/components/IncidentDrawer.tsx)
- [`frontend/package.json`](../frontend/package.json)
- [`frontend/package-lock.json`](../frontend/package-lock.json)
- [`frontend/vite.config.ts`](../frontend/vite.config.ts)
- [`frontend/index.html`](../frontend/index.html)

Design references:

- [`assets/stitch_signalwatch_rf_anomaly_dashboard/signalwatch_professional/DESIGN.md`](../assets/stitch_signalwatch_rf_anomaly_dashboard/signalwatch_professional/DESIGN.md)
- [`assets/stitch_signalwatch_rf_anomaly_dashboard/signalwatch_dashboard/screen.png`](../assets/stitch_signalwatch_rf_anomaly_dashboard/signalwatch_dashboard/screen.png)
- [`assets/stitch_signalwatch_rf_anomaly_dashboard/signalwatch_dashboard/code.html`](../assets/stitch_signalwatch_rf_anomaly_dashboard/signalwatch_dashboard/code.html)
- [`assets/stitch_signalwatch_rf_anomaly_dashboard/incident_detail_drawer/screen.png`](../assets/stitch_signalwatch_rf_anomaly_dashboard/incident_detail_drawer/screen.png)
- [`assets/stitch_signalwatch_rf_anomaly_dashboard/incident_detail_drawer/code.html`](../assets/stitch_signalwatch_rf_anomaly_dashboard/incident_detail_drawer/code.html)
- [`assets/inspo/anomaly_detection_UI_inspo1.png`](../assets/inspo/anomaly_detection_UI_inspo1.png)
- [`assets/inspo/anomaly_detection_UI_inspo2.png`](../assets/inspo/anomaly_detection_UI_inspo2.png)
- [`assets/inspo/anomaly_detection_UI_inspo2.jpg`](../assets/inspo/anomaly_detection_UI_inspo2.jpg)
- [`assets/inspo/anomaly_detection_UI_inspo3.png`](../assets/inspo/anomaly_detection_UI_inspo3.png)

## Phase 5 — Integration and Demo Hardening

**Status:** Complete.

### Delivered behaviour

- Make global filters update overview, observations, incidents, and heatmap through one shared filter state.
- Verify that incident rows, timeline markers, and heatmap cells resolve to the same incident-detail endpoint and explanation drawer.
- Distinguish initial loading, filtered-empty results, partial failures, complete service failures, missing analytics artifacts, and drawer failures.
- Provide retry controls and a specific `make generate` recovery path when artifacts are unavailable.
- Make `make demo` check for all six required artifacts and generate the deterministic dataset only when any file is missing.
- Allow pipeline artifacts to be generated into an isolated directory with `DATA_DIR=/absolute/path` for clean-start verification.
- Add a running-stack smoke test for API health, a real filtered overview query, and the dashboard response.
- Document architecture, synthetic data, model reasoning, baselines, severity calibration, counterfactual explanations, startup, commands, limitations, and a three-minute walkthrough.

### Acceptance evidence

- Four frontend tests cover live rendering, incident-row detail, unavailable-artifact recovery, consistent cross-endpoint filters, and timeline/heatmap selection paths.
- The frontend production TypeScript build passes.
- The complete backend suite passes and retains its API, pipeline-quality, reproducibility, schema, and error-path assertions.
- Artifact generation is verified in an isolated empty directory and produces the same deterministic SHA-256 hashes.
- Docker Compose clean-build and running-stack smoke checks pass for the pipeline, API, and web services.
- `make demo` is the only command required to generate missing data and start the application.

### Relevant files

- [`README.md`](../README.md)
- [`docs/implementation.md`](implementation.md)
- [`Makefile`](../Makefile)
- [`compose.yaml`](../compose.yaml)
- [`.env.example`](../.env.example)
- [`.gitignore`](../.gitignore)
- [`scripts/smoke-test.sh`](../scripts/smoke-test.sh)
- [`backend/Dockerfile`](../backend/Dockerfile)
- [`backend/app/main.py`](../backend/app/main.py)
- [`backend/app/pipeline.py`](../backend/app/pipeline.py)
- [`backend/app/api/dependencies.py`](../backend/app/api/dependencies.py)
- [`backend/app/api/routes.py`](../backend/app/api/routes.py)
- [`backend/app/repositories/artifacts.py`](../backend/app/repositories/artifacts.py)
- [`backend/tests/test_api.py`](../backend/tests/test_api.py)
- [`backend/tests/test_health.py`](../backend/tests/test_health.py)
- [`backend/tests/test_pipeline.py`](../backend/tests/test_pipeline.py)
- [`frontend/Dockerfile`](../frontend/Dockerfile)
- [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- [`frontend/src/api.ts`](../frontend/src/api.ts)
- [`frontend/src/index.css`](../frontend/src/index.css)
- [`frontend/src/App.test.tsx`](../frontend/src/App.test.tsx)
- [`frontend/src/components/FilterBar.tsx`](../frontend/src/components/FilterBar.tsx)
- [`frontend/src/components/SignalTimeline.tsx`](../frontend/src/components/SignalTimeline.tsx)
- [`frontend/src/components/IncidentList.tsx`](../frontend/src/components/IncidentList.tsx)
- [`frontend/src/components/AnomalyHeatmap.tsx`](../frontend/src/components/AnomalyHeatmap.tsx)
- [`frontend/src/components/IncidentDrawer.tsx`](../frontend/src/components/IncidentDrawer.tsx)

## Assumptions and Exclusions

- Parquet is the only persistence layer.
- Detection is deterministic and batch-based; live streaming and automatic retraining are excluded.
- Authentication, user accounts, alert acknowledgement, database migrations, PostGIS, maps, cloud deployment, and mobile-specific design are excluded.
- Explanations use counterfactual model sensitivity and deterministic templates, not an LLM.
- Synthetic ground-truth labels are evaluation-only and never enter model training or public application responses.
- Severity is relative to the generated batch and is not a real-world probability.
