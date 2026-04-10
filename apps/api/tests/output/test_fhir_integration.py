from datetime import datetime, timezone

from fastapi.testclient import TestClient
from _pytest.monkeypatch import MonkeyPatch
from unittest.mock import AsyncMock, patch

from main import app
from output.fhir_integration import build_diagnostic_report, build_oru_message
from output.integration_api import build_mock_recommendation


def test_build_oru_message() -> None:
    rec = build_mock_recommendation("patient-001")
    msg = build_oru_message(rec)
    assert "ORU^R01" in msg
    assert "OBX|1|TX|DDX" in msg


@patch("shared.llm_client.llm_complete", new_callable=AsyncMock)
def test_fhir_endpoints(mock_llm_complete: AsyncMock) -> None:
    mock_llm_complete.return_value = type("Resp", (), {"content": "Formal diagnostic narrative."})()
    client = TestClient(app)
    manifest = client.get("/fhir/smart-manifest")
    assert manifest.status_code == 200
    rec = build_mock_recommendation("patient-001").model_dump(mode="json")
    resp = client.post("/fhir/diagnostic-report", json={"patient_id": "patient-001", "recommendation": rec})
    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "DiagnosticReport"
    assert "text" in resp.json()
    assert "div" in resp.json()["text"]


async def _fake_llm_complete(**kwargs: object) -> object:
    class _Resp:
        content = "Formal diagnostic narrative."

    return _Resp()


def test_build_diagnostic_report_includes_narrative(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("output.fhir_integration.llm_complete", _fake_llm_complete)
    rec = build_mock_recommendation("patient-001")
    report = build_diagnostic_report(rec, "patient-001")
    assert "text" in report
    text = report["text"]
    assert isinstance(text, dict)
    assert "Formal diagnostic narrative." in str(text.get("div"))

