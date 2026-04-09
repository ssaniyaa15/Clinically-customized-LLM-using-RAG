from fastapi.testclient import TestClient

from amca_api.main import app


def test_monitoring_endpoints() -> None:
    client = TestClient(app)

    drift = client.get("/monitoring/drift")
    assert drift.status_code == 200

    perf = client.get("/monitoring/performance")
    assert perf.status_code == 200

    payload = {
        "reference": [{"a": 1.0, "b": 2.0}, {"a": 2.0, "b": 3.0}],
        "current": [{"a": 1.2, "b": 2.2}, {"a": 2.5, "b": 3.5}],
        "predictions": [0.2, 0.8],
        "ground_truth": [0, 1],
        "sensitive_attrs": [0, 1],
        "error_rate": 0.1,
    }
    ing = client.post("/monitoring/ingest", json=payload)
    assert ing.status_code == 200
    body = ing.json()
    assert "drift_report" in body
    assert "performance" in body
    assert "concept_drift" in body

