from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import torch
from _pytest.monkeypatch import MonkeyPatch
from torch import nn

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
from safety.bias_auditor import BiasAuditor
from safety.regulatory_compliance import AuditTrail
from safety.safety_orchestrator import SafetyOrchestrator


class TinyModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(4, 4), nn.ReLU(), nn.Dropout(0.5), nn.Linear(4, 2))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.net(x))


def _rec() -> ClinicalRecommendation:
    return ClinicalRecommendation(
        ddx=DDxOutput(diagnoses=[Diagnosis(name="Dx", icd10_code="A00", confidence=0.9, evidence_snippets=[])]),
        treatment=TreatmentPlan(recommendations=[], requires_specialist_review=False),
        risk=RiskPrognosisOutput(
            readmission=ReadmissionRisk(probability=0.8, risk_tier="high"),
            survival=SurvivalCurve(time_points=[0, 30], survival_probabilities=[1.0, 0.9]),
            complications=ComplicationRisks(risks={}),
        ),
        explanations={"x": ExplanationBundle()},
        generated_at=datetime.now(timezone.utc),
        uncertainty_score=0.5,
    )


def test_safety_orchestrator_adds_warning(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("UNCERTAINTY_EPI_THRESHOLD", "0.01")
    orchestrator = SafetyOrchestrator(
        auditor=BiasAuditor(db_path=str(tmp_path / "bias.db")),
        audit_trail=AuditTrail(db_path=str(tmp_path / "comp.db")),
    )
    bundle = orchestrator.run_safety_checks(TinyModel(), torch.randn(1, 4), _rec())
    assert bundle.gated_recommendation.requires_confirmation
    assert bundle.gated_recommendation.safety_warning is not None

