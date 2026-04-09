from types import SimpleNamespace
from typing import cast

import torch
from _pytest.monkeypatch import MonkeyPatch
from torch import nn

from learning.federated_learning import ClinicalFlowerClient, build_server_strategy


class TinyModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.fc = nn.Linear(4, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.fc(x))


def _loader() -> list[dict[str, torch.Tensor]]:
    samples = [{"inputs": torch.randn(4, 4), "targets": torch.randint(0, 2, (4,))} for _ in range(2)]
    return samples


def test_client_get_set_fit_evaluate(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("learning.federated_learning.opacus_module", None)
    client = ClinicalFlowerClient(TinyModel(), _loader(), _loader())
    params = client.get_parameters({})
    client.set_parameters(params)
    new_params, n_train, metrics = client.fit(params, {})
    assert isinstance(new_params, list)
    assert n_train > 0
    assert "train_loss" in metrics

    loss, n_val, eval_metrics = client.evaluate(new_params, {})
    assert isinstance(loss, float)
    assert n_val > 0
    assert "accuracy" in eval_metrics


def test_strategy_builder_with_mocked_flwr(monkeypatch: MonkeyPatch) -> None:
    fake_strategy = object()
    fake_flwr = SimpleNamespace(
        server=SimpleNamespace(strategy=SimpleNamespace(FedAvg=lambda min_available_clients: fake_strategy))
    )
    monkeypatch.setattr("learning.federated_learning.flwr_module", fake_flwr)
    assert build_server_strategy() is fake_strategy

