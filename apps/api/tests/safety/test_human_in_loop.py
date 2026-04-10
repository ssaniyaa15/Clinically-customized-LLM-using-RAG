from datetime import datetime, timezone

from fastapi.testclient import TestClient

from main import app
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
from safety.human_in_loop import gate_recommendation


async def _fake_escalation_message(gated: object) -> str:
    _ = gated
    return "Escalate now."


def _rec(conf: float, tier: str, uncertainty: float) -> ClinicalRecommendation:
    return ClinicalRecommendation(
        ddx=DDxOutput(diagnoses=[Diagnosis(name="Dx", icd10_code="A00", confidence=conf, evidence_snippets=[])]),
        treatment=TreatmentPlan(recommendations=[], requires_specialist_review=False),
        risk=RiskPrognosisOutput(
            readmission=ReadmissionRisk(probability=0.8, risk_tier=tier),
            survival=SurvivalCurve(time_points=[0, 30], survival_probabilities=[1.0, 0.9]),
            complications=ComplicationRisks(risks={}),
        ),
        explanations={"x": ExplanationBundle()},
        generated_at=datetime.now(timezone.utc),
        uncertainty_score=uncertainty,
    )


def test_gate_rules() -> None:
    from _pytest.monkeypatch import MonkeyPatch

    monkeypatch = MonkeyPatch()
    monkeypatch.setattr("safety.human_in_loop.generate_escalation_message", _fake_escalation_message)
    critical = gate_recommendation(_rec(0.9, "high", 0.1))
    assert critical.escalation_level == "critical"
    assert critical.escalation_message == "Escalate now."
    urgent = gate_recommendation(_rec(0.6, "moderate", 0.5))
    assert urgent.escalation_level == "urgent"
    routine = gate_recommendation(_rec(0.6, "low", 0.1))
    assert routine.escalation_level == "routine"
    monkeypatch.undo()


def test_gate_endpoints() -> None:
    client = TestClient(app)
    c = client.post("/gate/confirm", json={"clinician_id": "c1", "recommendation_id": "r1", "confirmed": True})
    assert c.status_code == 200
    o = client.post("/gate/override", json={"clinician_id": "c1", "recommendation_id": "r1", "reason": "override"})
    assert o.status_code == 200

