import numpy as np
from numpy.typing import NDArray

from reasoning.risk_prognosis import RiskPrognosisHead


class FakeLR:
    def predict_proba(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        _ = x
        return np.array([[0.2, 0.8]])


class FakeMulti:
    def predict(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        _ = x
        return np.array([[0.1, 0.2, 0.3]])


def test_readmission_placeholder_when_model_missing() -> None:
    head = RiskPrognosisHead(models_dir="nonexistent_models")
    out = head.predict_readmission(np.ones((1, 4)))
    assert out.probability == 0.0
    assert out.risk_tier == "low"


def test_readmission_with_model() -> None:
    head = RiskPrognosisHead(models_dir="nonexistent_models")
    head.readmission_model = FakeLR()
    out = head.predict_readmission(np.ones((1, 4)))
    assert out.probability == 0.8
    assert out.risk_tier == "high"


def test_complication_prediction_with_model() -> None:
    head = RiskPrognosisHead(models_dir="nonexistent_models")
    head.complication_model = FakeMulti()
    out = head.predict_complications(np.ones((1, 4)))
    assert out.risks["sepsis"] == 0.1
    assert out.risks["arrhythmia"] == 0.3


def test_run_aggregates_outputs() -> None:
    head = RiskPrognosisHead(models_dir="nonexistent_models")
    out = head.run(np.ones((1, 4)))
    assert out.readmission.probability == 0.0
    assert len(out.survival.time_points) == 5

