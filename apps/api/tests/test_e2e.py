import json

from fastapi.testclient import TestClient
from _pytest.monkeypatch import MonkeyPatch

from main import app


def test_analyse_end_to_end_with_mocks(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("reasoning.differential_diagnosis.faiss", None)
    monkeypatch.setattr("reasoning.differential_diagnosis.openai_module", None)
    monkeypatch.setattr("output.feedback_capture.Producer", None)
    monkeypatch.setattr(
        "output.fhir_integration.build_diagnostic_report",
        lambda rec, patient_id: {"resourceType": "DiagnosticReport", "subject": {"reference": f"Patient/{patient_id}"}},
    )

    client = TestClient(app)
    payload = {
        "ehr_json": json.dumps(
            {
                "patient_id": "patient-xyz",
                "source_system": "hl7v2",
                "sex": "F",
                "diagnosis_codes": ["J18.9"],
                "observation_summary": {"clinical_text": "fever cough dyspnea"},
            }
        ),
        "clinical_note": "Patient with fever and cough",
        "omics_csv": "GENE,VALUE\nTP53,1.2",
    }
    response = client.post("/analyse", data=payload)
    assert response.status_code == 200
    body = response.json()
    assert "gated_recommendation" in body
    assert body["gated_recommendation"]["requires_confirmation"] is True
    assert "safety_bundle" in body
    assert body["safety_bundle"]["audit_entry"]["electronic_signature_hash"]

    audit = client.get("/compliance/audit-trail")
    assert audit.status_code == 200
    assert len(audit.json()) >= 1

    fhir_resp = client.post(
        "/fhir/diagnostic-report",
        json={"patient_id": "patient-xyz", "recommendation": body["gated_recommendation"]["recommendation"]},
    )
    assert fhir_resp.status_code == 200
    assert fhir_resp.json()["resourceType"] == "DiagnosticReport"

    feedback = client.post(
        "/feedback",
        json={
            "recommendation_id": "rec-e2e",
            "clinician_id": "clinician-e2e",
            "action": "accept",
            "free_text": "Looks good",
            "patient_id": "patient-xyz",
        },
    )
    assert feedback.status_code == 200
    assert float(feedback.json()["reward"]) == 1.0

