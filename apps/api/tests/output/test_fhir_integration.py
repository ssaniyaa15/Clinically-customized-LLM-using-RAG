from datetime import datetime, timezone

from fastapi.testclient import TestClient

from amca_api.main import app
from output.fhir_integration import build_oru_message
from output.integration_api import build_mock_recommendation


def test_build_oru_message() -> None:
    rec = build_mock_recommendation("patient-001")
    msg = build_oru_message(rec)
    assert "ORU^R01" in msg
    assert "OBX|1|TX|DDX" in msg


def test_fhir_endpoints() -> None:
    client = TestClient(app)
    manifest = client.get("/fhir/smart-manifest")
    assert manifest.status_code == 200
    rec = build_mock_recommendation("patient-001").model_dump(mode="json")
    resp = client.post("/fhir/diagnostic-report", json={"patient_id": "patient-001", "recommendation": rec})
    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "DiagnosticReport"

