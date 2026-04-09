from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from _pytest.monkeypatch import MonkeyPatch

from amca_api.main import app
from reasoning.differential_diagnosis import DDxOutput, Diagnosis
from reasoning.explainability import ExplanationBundle
from reasoning.reasoning_orchestrator import ClinicalRecommendation
from reasoning.risk_prognosis import (
    ComplicationRisks,
    ReadmissionRisk,
    RiskPrognosisOutput,
    SurvivalCurve,
)
from reasoning.treatment_recommender import TreatmentPlan
from safety import regulatory_compliance as rc


def _rec() -> ClinicalRecommendation:
    return ClinicalRecommendation(
        ddx=DDxOutput(diagnoses=[Diagnosis(name="Dx", icd10_code="A00", confidence=0.7, evidence_snippets=[])]),
        treatment=TreatmentPlan(recommendations=[], requires_specialist_review=False),
        risk=RiskPrognosisOutput(
            readmission=ReadmissionRisk(probability=0.2, risk_tier="low"),
            survival=SurvivalCurve(time_points=[0, 30], survival_probabilities=[1.0, 0.9]),
            complications=ComplicationRisks(risks={"sepsis": 0.1}),
        ),
        explanations={"x": ExplanationBundle()},
        generated_at=datetime.now(timezone.utc),
        uncertainty_score=0.3,
    )


def test_audit_signature_and_list(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    db = tmp_path / "comp.db"
    monkeypatch.setenv("COMPLIANCE_SECRET_KEY", "secret")
    trail = rc.AuditTrail(db_path=str(db))
    entry = trail.log_prediction("p1", _rec(), "clin1", "accepted")
    assert len(entry.electronic_signature_hash) == 64
    rows = trail.list_entries()
    assert len(rows) == 1


def test_compliance_endpoints() -> None:
    client = TestClient(app)
    resp_meta = client.get("/compliance/samd-metadata")
    assert resp_meta.status_code == 200
    resp_audit = client.get("/compliance/audit-trail")
    assert resp_audit.status_code == 200

