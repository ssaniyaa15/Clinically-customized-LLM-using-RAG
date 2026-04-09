from __future__ import annotations

import os

import numpy as np
import torch
from numpy.typing import NDArray
from pydantic import BaseModel
from torch import Tensor, nn


class UncertaintyOutput(BaseModel):
    mean_logits: list[float]
    epistemic_std: float
    aleatoric_std: float


class ConfidenceInterval(BaseModel):
    lower: float
    upper: float
    alpha: float


class UncertaintyBundle(BaseModel):
    mc_output: UncertaintyOutput
    conformal_interval: ConfidenceInterval
    is_high_uncertainty: bool


class ConformalPredictor:
    def __init__(self) -> None:
        self.qhat = 0.0

    def calibrate(self, cal_scores: NDArray[np.float64]) -> None:
        if cal_scores.size == 0:
            self.qhat = 0.0
            return
        self.qhat = float(np.quantile(cal_scores, 0.9))

    def predict(self, score: float, alpha: float = 0.1) -> ConfidenceInterval:
        return ConfidenceInterval(lower=float(score - self.qhat), upper=float(score + self.qhat), alpha=alpha)


def mc_dropout_predict(model: nn.Module, x: Tensor, n_samples: int = 50) -> UncertaintyOutput:
    model.train()
    preds = []
    with torch.no_grad():
        for _ in range(n_samples):
            logits = model(x)
            preds.append(logits.detach().cpu().numpy())
    arr = np.stack(preds, axis=0)
    mean_logits = np.mean(arr, axis=0).flatten()
    epistemic_std = float(np.std(np.mean(arr, axis=1)))
    probs = torch.softmax(torch.tensor(arr), dim=-1).numpy()
    aleatoric_std = float(np.mean(np.std(probs, axis=0)))
    return UncertaintyOutput(
        mean_logits=[float(v) for v in mean_logits.tolist()],
        epistemic_std=epistemic_std,
        aleatoric_std=aleatoric_std,
    )


def quantify_uncertainty(model: nn.Module, input_tensor: Tensor) -> UncertaintyBundle:
    mc = mc_dropout_predict(model, input_tensor, n_samples=50)
    cp = ConformalPredictor()
    cal = np.random.uniform(0.0, 1.0, 100)
    cp.calibrate(cal)
    score = float(np.max(np.array(mc.mean_logits))) if mc.mean_logits else 0.0
    interval = cp.predict(score, alpha=0.1)
    threshold = float(os.getenv("UNCERTAINTY_EPI_THRESHOLD", "0.2"))
    return UncertaintyBundle(
        mc_output=mc,
        conformal_interval=interval,
        is_high_uncertainty=bool(mc.epistemic_std > threshold),
    )

