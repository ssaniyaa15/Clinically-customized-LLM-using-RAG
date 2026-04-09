import numpy as np
import torch
from torch import nn
from typing import cast

from safety.uncertainty_quantification import (
    ConformalPredictor,
    mc_dropout_predict,
    quantify_uncertainty,
)


class TinyDropout(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(4, 4), nn.ReLU(), nn.Dropout(p=0.5), nn.Linear(4, 2))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.net(x))


def test_mc_dropout_predict() -> None:
    model = TinyDropout()
    x = torch.randn(1, 4)
    out = mc_dropout_predict(model, x, n_samples=10)
    assert len(out.mean_logits) == 2
    assert out.epistemic_std >= 0.0


def test_conformal_predictor() -> None:
    cp = ConformalPredictor()
    cp.calibrate(np.array([0.1, 0.2, 0.3]))
    ci = cp.predict(0.5, alpha=0.1)
    assert ci.lower <= ci.upper


def test_quantify_uncertainty() -> None:
    model = TinyDropout()
    x = torch.randn(1, 4)
    out = quantify_uncertainty(model, x)
    assert out.conformal_interval.alpha == 0.1

