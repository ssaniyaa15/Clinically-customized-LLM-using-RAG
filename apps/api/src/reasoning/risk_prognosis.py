from __future__ import annotations

import os
from typing import Any, cast

import numpy as np
from pydantic import BaseModel, Field

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None


class ReadmissionRisk(BaseModel):
    probability: float
    risk_tier: str


class SurvivalCurve(BaseModel):
    time_points: list[float] = Field(default_factory=list)
    survival_probabilities: list[float] = Field(default_factory=list)


class ComplicationRisks(BaseModel):
    risks: dict[str, float] = Field(default_factory=dict)


class RiskPrognosisOutput(BaseModel):
    readmission: ReadmissionRisk
    survival: SurvivalCurve
    complications: ComplicationRisks


class RiskPrognosisHead:
    """Wraps readmission, survival, and complication risk estimators with safe placeholders."""

    def __init__(self, models_dir: str = "models") -> None:
        self.models_dir = models_dir
        self.readmission_model = self._load_model("readmission_lr.joblib")
        self.complication_model = self._load_model("complication_multilabel.joblib")

    def _load_model(self, filename: str) -> Any:
        if joblib is None:
            return None
        path = os.path.join(self.models_dir, filename)
        if not os.path.exists(path):
            return None
        return cast(Any, joblib.load(path))

    @staticmethod
    def _risk_tier(probability: float) -> str:
        if probability >= 0.7:
            return "high"
        if probability >= 0.3:
            return "moderate"
        return "low"

    def predict_readmission(self, features: np.ndarray) -> ReadmissionRisk:
        if self.readmission_model is None:
            return ReadmissionRisk(probability=0.0, risk_tier="low")
        if hasattr(self.readmission_model, "predict_proba"):
            proba = float(self.readmission_model.predict_proba(features)[0][1])
        else:
            proba = float(self.readmission_model.predict(features)[0])
        return ReadmissionRisk(probability=proba, risk_tier=self._risk_tier(proba))

    @staticmethod
    def predict_survival_curve(_features: np.ndarray) -> SurvivalCurve:
        # Placeholder DeepSurv-style deterministic curve.
        points = [0.0, 7.0, 14.0, 21.0, 30.0]
        probs = [1.0, 0.95, 0.9, 0.86, 0.82]
        return SurvivalCurve(time_points=points, survival_probabilities=probs)

    def predict_complications(self, features: np.ndarray) -> ComplicationRisks:
        names = ["sepsis", "aki", "arrhythmia"]
        if self.complication_model is None:
            return ComplicationRisks(risks={name: 0.0 for name in names})

        if hasattr(self.complication_model, "predict_proba"):
            raw = self.complication_model.predict_proba(features)
            if isinstance(raw, list):
                vals = [float(item[0][1]) if hasattr(item, "__getitem__") else 0.0 for item in raw]
            else:
                vals = [float(x) for x in raw[0]]
        else:
            pred = self.complication_model.predict(features)[0]
            vals = [float(x) for x in pred]
        vals = (vals + [0.0, 0.0, 0.0])[:3]
        return ComplicationRisks(risks={name: vals[i] for i, name in enumerate(names)})

    def run(self, features: np.ndarray) -> RiskPrognosisOutput:
        return RiskPrognosisOutput(
            readmission=self.predict_readmission(features),
            survival=self.predict_survival_curve(features),
            complications=self.predict_complications(features),
        )

