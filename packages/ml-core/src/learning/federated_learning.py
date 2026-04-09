from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import torch
from torch import Tensor, nn

flwr_module: Any
try:
    import flwr as flwr_module
except Exception:  # pragma: no cover
    flwr_module = None

try:
    import opacus as opacus_module
except Exception:  # pragma: no cover
    opacus_module = None

if TYPE_CHECKING:
    from flwr.client import NumPyClient as NumPyClientBase
else:
    NumPyClientBase = cast(Any, flwr_module.client.NumPyClient if flwr_module is not None else object)


class ClinicalFlowerClient(NumPyClientBase):
    """Flower NumPyClient for clinical federated training with optional DP wrapping."""

    def __init__(self, model: nn.Module, train_loader: Any, val_loader: Any) -> None:
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.loss_fn = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        self.dp_attached = False
        self._attach_dp()

    def _attach_dp(self) -> None:
        if opacus_module is None:
            return
        try:
            pe = opacus_module.PrivacyEngine()
            self.model, self.optimizer, self.train_loader = pe.make_private_with_epsilon(
                module=self.model,
                optimizer=self.optimizer,
                data_loader=self.train_loader,
                epochs=1,
                target_epsilon=1.0,
                target_delta=1e-5,
                max_grad_norm=1.0,
            )
            self.dp_attached = True
        except Exception:
            self.dp_attached = False

    @staticmethod
    def _unpack_batch(batch: Any) -> tuple[Tensor, Tensor]:
        if isinstance(batch, dict):
            return batch["inputs"], batch["targets"]
        if isinstance(batch, list) and batch and isinstance(batch[0], dict):
            inputs = torch.cat([item["inputs"] for item in batch], dim=0)
            targets = torch.cat([item["targets"] for item in batch], dim=0)
            return inputs, targets
        raise TypeError("Unsupported batch format for ClinicalFlowerClient.")

    def get_parameters(self, config: dict[str, Any]) -> list[np.ndarray]:
        _ = config
        return [p.detach().cpu().numpy() for _, p in self.model.state_dict().items()]

    def set_parameters(self, parameters: list[np.ndarray]) -> None:
        keys = list(self.model.state_dict().keys())
        params_dict = zip(keys, parameters)
        state = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        self.model.load_state_dict(state, strict=True)

    def fit(
        self, parameters: list[np.ndarray], config: dict[str, Any]
    ) -> tuple[list[np.ndarray], int, dict[str, bool | bytes | float | int | str]]:
        _ = config
        self.set_parameters(parameters)
        self.model.train()
        last_loss = torch.tensor(0.0)
        for batch in self.train_loader:
            x, y = self._unpack_batch(batch)
            logits = self.model(x)
            loss = self.loss_fn(logits, y)
            self.optimizer.zero_grad(set_to_none=True)
            loss.backward()
            self.optimizer.step()
            last_loss = loss.detach()
            if self.dp_attached:
                # Opacus Poisson sampling expects optimizer.step per sampled batch without accumulation.
                break
        train_size = int(len(getattr(self.train_loader, "dataset", self.train_loader)))
        return self.get_parameters({}), train_size, {"train_loss": float(last_loss.item())}

    def evaluate(
        self, parameters: list[np.ndarray], config: dict[str, Any]
    ) -> tuple[float, int, dict[str, bool | bytes | float | int | str]]:
        _ = config
        self.set_parameters(parameters)
        self.model.eval()
        total = 0
        correct = 0
        total_loss = 0.0
        with torch.no_grad():
            for batch in self.val_loader:
                x, y = self._unpack_batch(batch)
                logits = self.model(x)
                total_loss += float(self.loss_fn(logits, y).item())
                pred = torch.argmax(logits, dim=1)
                total += int(y.size(0))
                correct += int((pred == y).sum().item())
        avg_loss = total_loss / max(1, len(self.val_loader))
        acc = correct / max(1, total)
        val_size = int(len(getattr(self.val_loader, "dataset", self.val_loader)))
        return float(avg_loss), val_size, {"accuracy": float(acc)}


def build_server_strategy() -> Any:
    if flwr_module is None:
        return None
    return flwr_module.server.strategy.FedAvg(min_available_clients=3)


def start_federated_server(server_address: str = "0.0.0.0:8080") -> None:
    """Stub server start helper using FedAvg strategy."""
    strategy = build_server_strategy()
    if flwr_module is None or strategy is None:
        return
    # TODO: Launch real federated server runtime and lifecycle management.
    _ = (server_address, strategy)

