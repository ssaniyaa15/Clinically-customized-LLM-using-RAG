from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel

from fusion.fusion_router import FusedRepresentation
from ingestion.ehr_connector import PatientRecord
from reasoning.differential_diagnosis import DDxOutput, DifferentialDiagnosisHead
from reasoning.explainability import ExplanationBundle, ExplainabilityHead
from reasoning.risk_prognosis import RiskPrognosisHead, RiskPrognosisOutput
from reasoning.treatment_recommender import TreatmentPlan, TreatmentRecommenderHead


class ClinicalRecommendation(BaseModel):
    ddx: DDxOutput
    treatment: TreatmentPlan
    risk: RiskPrognosisOutput
    explanations: dict[str, ExplanationBundle]
    generated_at: datetime
    uncertainty_score: float


class ReasoningOrchestrator:
    """Coordinates diagnosis, treatment, risk, and explainability heads into one recommendation."""

    def __init__(
        self,
        ddx_head: Any = None,
        treatment_head: Any = None,
        risk_head: Any = None,
        explainability_head: Any = None,
    ) -> None:
        self.ddx_head: DifferentialDiagnosisHead | Any = ddx_head or DifferentialDiagnosisHead()
        self.treatment_head: TreatmentRecommenderHead | Any = (
            treatment_head or TreatmentRecommenderHead()
        )
        self.risk_head: RiskPrognosisHead | Any = risk_head or RiskPrognosisHead()
        self.explainability_head: ExplainabilityHead | Any = (
            explainability_head or ExplainabilityHead()
        )

    @staticmethod
    def _build_query(fused: FusedRepresentation, patient: PatientRecord) -> str:
        dx = ", ".join(patient.diagnosis_codes) if patient.diagnosis_codes else "no-known-dx"
        return (
            f"Patient {patient.patient_id} with codes [{dx}] "
            f"and modalities {','.join(fused.available_modalities)}"
        )

    @staticmethod
    def _extract_features(fused: FusedRepresentation) -> NDArray[np.float32]:
        tensor = fused.early_embedding.tensor.detach().cpu().numpy()
        if tensor.ndim == 1:
            tensor = tensor.reshape(1, -1)
        return tensor.astype(np.float32)

    @staticmethod
    def _uncertainty_score(ddx: DDxOutput) -> float:
        if not ddx.diagnoses:
            return 1.0
        vals = [1.0 - float(d.confidence) for d in ddx.diagnoses]
        return float(np.mean(vals))

    def run(self, fused: FusedRepresentation, patient: PatientRecord) -> ClinicalRecommendation:
        query = self._build_query(fused, patient)
        ddx = self.ddx_head.run(query)
        treatment = self.treatment_head.recommend(ddx)
        features = self._extract_features(fused)
        risk = self.risk_head.run(features)

        explanations = {
            "tabular": self.explainability_head.explain("tabular", features[0].tolist()[:16], ddx=ddx),
            "text": self.explainability_head.explain("text", query),
            "image": self.explainability_head.explain("image", None),
        }

        return ClinicalRecommendation(
            ddx=ddx,
            treatment=treatment,
            risk=risk,
            explanations=explanations,
            generated_at=datetime.now(timezone.utc),
            uncertainty_score=self._uncertainty_score(ddx),
        )

