from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query

from reasoning.differential_diagnosis import DDxOutput, Diagnosis
from reasoning.explainability import ExplanationBundle, ShapOutput
from reasoning.reasoning_orchestrator import ClinicalRecommendation
from reasoning.risk_prognosis import (
    ComplicationRisks,
    ReadmissionRisk,
    RiskPrognosisOutput,
    SurvivalCurve,
)
from reasoning.treatment_recommender import Recommendation, TreatmentPlan
from safety.human_in_loop import GatedRecommendation, gate_recommendation

router = APIRouter(prefix="/output", tags=["output"])


def build_mock_recommendation(patient_id: str) -> ClinicalRecommendation:
    return ClinicalRecommendation(
        ddx=DDxOutput(
            diagnoses=[
                Diagnosis(
                    name="Community-acquired pneumonia",
                    icd10_code="J18.9",
                    confidence=0.88,
                    evidence_snippets=["Bilateral infiltrates on CXR", "Fever and productive cough"],
                ),
                Diagnosis(
                    name="Acute bronchitis",
                    icd10_code="J20.9",
                    confidence=0.52,
                    evidence_snippets=["Cough dominant symptoms"],
                ),
            ]
        ),
        treatment=TreatmentPlan(
            recommendations=[
                Recommendation(
                    intervention="Start guideline-concordant empiric antibiotics",
                    guideline_source="IDSA-2023",
                    evidence_level="A",
                    contraindications=["Severe beta-lactam allergy"],
                ),
                Recommendation(
                    intervention="Reassess oxygenation in 6 hours",
                    guideline_source="IDSA-2023",
                    evidence_level="B",
                    contraindications=[],
                ),
            ],
            requires_specialist_review=False,
        ),
        risk=RiskPrognosisOutput(
            readmission=ReadmissionRisk(probability=0.67, risk_tier="high"),
            survival=SurvivalCurve(
                time_points=[0.0, 7.0, 14.0, 21.0, 30.0],
                survival_probabilities=[1.0, 0.95, 0.9, 0.84, 0.79],
            ),
            complications=ComplicationRisks(risks={"sepsis": 0.18, "aki": 0.12, "arrhythmia": 0.09}),
        ),
        explanations={
            "tabular": ExplanationBundle(
                shap=ShapOutput(feature_importances={"resp_rate": 0.21, "wbc": 0.17, "spo2": 0.25}, base_value=0.0)
            )
        },
        generated_at=datetime.now(timezone.utc),
        uncertainty_score=0.31,
    )


@router.get("/latest-recommendation", response_model=GatedRecommendation)
def get_latest_recommendation(
    patient_id: str = Query("patient-001", description="Patient identifier"),
) -> GatedRecommendation:
    recommendation = build_mock_recommendation(patient_id)
    return gate_recommendation(recommendation)

