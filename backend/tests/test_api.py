from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.pipeline import run_pipeline
from app.repositories.artifacts import ArtifactRepository


@pytest.fixture(scope="module")
def repository(tmp_path_factory: pytest.TempPathFactory) -> ArtifactRepository:
    output_dir: Path = tmp_path_factory.mktemp("api-artifacts")
    run_pipeline(output_dir)
    loaded = ArtifactRepository(output_dir)
    loaded.load()
    return loaded


@pytest.fixture(scope="module")
def client(repository: ArtifactRepository) -> TestClient:
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.state.repository = repository
    with TestClient(test_app) as test_client:
        yield test_client


def test_overview_and_ranked_incident_list(client: TestClient) -> None:
    overview = client.get("/api/v1/overview")
    assert overview.status_code == 200
    assert overview.json() == {
        "incidents": 51,
        "critical_incidents": 8,
        "affected_sensors": 3,
        "anomaly_rate_pct": 1.53,
    }

    response = client.get("/api/v1/anomalies", params={"limit": 100})
    assert response.status_code == 200
    payload = response.json()
    scores = [item["severity_score"] for item in payload["items"]]
    assert payload["total"] == 51
    assert scores == sorted(scores, reverse=True)
    assert payload["items"][0]["severity"] == "critical"


def test_filters_apply_to_overview_and_incidents(client: TestClient) -> None:
    params = {
        "sensor_id": "RX-NORTH",
        "min_severity": 90,
        "incident_type": "broadband_interference",
    }
    overview = client.get("/api/v1/overview", params=params).json()
    incidents = client.get("/api/v1/anomalies", params=params).json()["items"]

    assert 0 < overview["incidents"] == len(incidents)
    assert overview["anomaly_rate_pct"] < 100
    assert all(item["sensor_id"] == "RX-NORTH" for item in incidents)
    assert all(item["severity_score"] >= 90 for item in incidents)
    assert all(item["incident_type"] == "broadband_interference" for item in incidents)


def test_observations_are_bounded_and_preserve_anomalies(client: TestClient) -> None:
    response = client.get("/api/v1/observations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_points"] == 48_384
    assert payload["meta"]["returned_points"] == 1_000
    assert payload["meta"]["downsampled"] is True
    assert sum(item["is_anomaly"] for item in payload["items"]) == 742

    filtered = client.get(
        "/api/v1/observations",
        params={
            "sensor_id": "RX-NORTH",
            "frequency_mhz": 433.05,
            "metric": "snr_db",
            "limit": 50,
        },
    ).json()
    assert len(filtered["items"]) == 50
    assert all(item["sensor_id"] == "RX-NORTH" for item in filtered["items"])
    assert all(item["frequency_mhz"] == 433.05 for item in filtered["items"])
    assert all(item["metric"] == "snr_db" for item in filtered["items"])
    assert all(item["lower"] <= item["expected"] <= item["upper"] for item in filtered["items"])


def test_anomaly_detail_contains_explanation_and_supporting_evidence(client: TestClient) -> None:
    incident = client.get("/api/v1/anomalies", params={"limit": 1}).json()["items"][0]
    response = client.get(f"/api/v1/anomalies/{incident['incident_id']}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["summary"]
    assert detail["pattern_description"]
    assert len(detail["metric_comparisons"]) == 3
    assert 1 <= len(detail["feature_contributions"]) <= 3
    assert detail["supporting_detections"]
    assert all(
        detection["values"]["noise_floor_dbm"].keys() == {"actual", "expected"}
        for detection in detail["supporting_detections"]
    )


def test_heatmap_is_bucketed_and_filterable(client: TestClient) -> None:
    response = client.get(
        "/api/v1/heatmap",
        params={"sensor_id": "RX-SOUTH", "bucket_minutes": 60, "min_severity": 80},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["bucket_minutes"] == 60
    assert payload["cells"]
    assert all(cell["sensor_id"] == "RX-SOUTH" for cell in payload["cells"])
    assert all(cell["severity_score"] >= 80 for cell in payload["cells"])


@pytest.mark.parametrize(
    ("path", "expected_fragment"),
    [
        ("/api/v1/overview?from=2026-07-10T00:00:00Z&to=2026-07-09T00:00:00Z", "earlier"),
        ("/api/v1/overview?sensor_id=UNKNOWN", "Unknown sensor_id"),
        ("/api/v1/overview?frequency_mhz=999", "Unknown frequency_mhz"),
        ("/api/v1/anomalies?incident_type=unknown", "Unknown incident_type"),
        ("/api/v1/observations?metric=unknown", "Unknown metric"),
    ],
)
def test_domain_validation(client: TestClient, path: str, expected_fragment: str) -> None:
    response = client.get(path)
    assert response.status_code == 422
    assert expected_fragment in response.json()["detail"]


def test_framework_validation_and_missing_incident(client: TestClient) -> None:
    assert client.get("/api/v1/overview?from=not-a-date").status_code == 422
    response = client.get("/api/v1/anomalies/INC-9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_missing_artifacts_return_service_unavailable() -> None:
    unavailable_app = FastAPI()
    unavailable_app.include_router(router)
    unavailable_app.state.repository = None
    unavailable_app.state.artifact_error = "Missing generated artifacts. Run `make generate`."

    with TestClient(unavailable_app) as unavailable_client:
        response = unavailable_client.get("/api/v1/overview")

    assert response.status_code == 503
    assert "make generate" in response.json()["detail"]

