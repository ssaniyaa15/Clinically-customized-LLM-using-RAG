import numpy as np
import pytest
import torch

from fusion.cross_modal_attention import CrossModalEmbedding
from fusion.early_fusion import JointEmbedding
from fusion.fusion_router import FusedRepresentation
from fusion.late_fusion import LateFusionOutput
from ingestion.ehr_connector import PatientRecord
from reasoning.differential_diagnosis import DDxOutput, Diagnosis
from reasoning.explainability import ExplanationBundle, GradCamOutput, LimeOutput, ShapOutput
from reasoning.reasoning_orchestrator import ReasoningOrchestrator
from reasoning.risk_prognosis import (
    ComplicationRisks,
    ReadmissionRisk,
    RiskPrognosisOutput,
    SurvivalCurve,
)
from reasoning.treatment_recommender import TreatmentPlan


class FakeDDx:
    def run(self, query: str) -> DDxOutput:
        _ = query
        return DDxOutput(
            diagnoses=[
                Diagnosis(
                    name="Pneumonia",
                    icd10_code="J18.9",
                    confidence=0.8,
                    evidence_snippets=["infiltrate"],
                )
            ]
        )


class FakeTx:
    def recommend(self, ddx: DDxOutput) -> TreatmentPlan:
        _ = ddx
        return TreatmentPlan(recommendations=[], requires_specialist_review=True)


class FakeRisk:
    def run(self, features: np.ndarray) -> RiskPrognosisOutput:
        _ = features
        return RiskPrognosisOutput(
            readmission=ReadmissionRisk(probability=0.2, risk_tier="low"),
            survival=SurvivalCurve(time_points=[0, 30], survival_probabilities=[1.0, 0.9]),
            complications=ComplicationRisks(risks={"sepsis": 0.1}),
        )


class FakeExplain:
    def explain(self, input_type: str, data: object) -> ExplanationBundle:
        _ = (input_type, data)
        return ExplanationBundle(
            shap=ShapOutput(feature_importances={"a": 0.1}, base_value=0.0),
            lime=LimeOutput(top_words=[("fever", 0.2)]),
            gradcam=GradCamOutput(),
        )


def _fused() -> FusedRepresentation:
    return FusedRepresentation(
        early_embedding=JointEmbedding(tensor=torch.randn(1, 512)),
        cross_modal_embedding=CrossModalEmbedding(tensor=torch.randn(1, 768)),
        late_output=LateFusionOutput(final_logits=torch.randn(1, 3), modality_weights={"a": 1.0}),
        available_modalities=["tabular", "imaging", "clinical_text"],
    )


def test_orchestrator_run() -> None:
    orch = ReasoningOrchestrator(
        ddx_head=FakeDDx(),
        treatment_head=FakeTx(),
        risk_head=FakeRisk(),
        explainability_head=FakeExplain(),
    )
    patient = PatientRecord(patient_id="P1", source_system="hl7v2", diagnosis_codes=["J18.9"])
    rec = orch.run(_fused(), patient)
    assert rec.ddx.diagnoses[0].name == "Pneumonia"
    assert rec.uncertainty_score == pytest.approx(0.2)
    assert "tabular" in rec.explanations


def test_uncertainty_score_empty_ddx() -> None:
    score = ReasoningOrchestrator._uncertainty_score(DDxOutput(diagnoses=[]))
    assert score == 1.0

