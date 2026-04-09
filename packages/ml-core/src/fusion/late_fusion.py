from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor, nn


@dataclass
class ModalityOutput:
    name: str
    logits: Tensor
    modality_present: bool = True


@dataclass
class LateFusionOutput:
    final_logits: Tensor
    modality_weights: dict[str, float]


class LateFusionEnsembler(nn.Module):
    """Learns modality weights with sigmoid gates and renormalizes under missing modalities."""

    def __init__(self, num_classes: int, max_modalities: int = 3) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.max_modalities = max_modalities
        self.gate = nn.Sequential(
            nn.Linear(num_classes, num_classes),
            nn.ReLU(),
            nn.Linear(num_classes, 1),
        )

    def forward(
        self,
        modality_a: ModalityOutput | None,
        modality_b: ModalityOutput | None,
        modality_c: ModalityOutput | None,
    ) -> LateFusionOutput:
        modalities = [m for m in [modality_a, modality_b, modality_c] if m is not None]
        if not modalities:
            raise ValueError("At least one modality output is required.")

        device = modalities[0].logits.device
        logits_acc = torch.zeros_like(modalities[0].logits)
        raw_weights: list[Tensor] = []
        names: list[str] = []

        for modality in modalities:
            names.append(modality.name)
            if not modality.modality_present:
                raw_weights.append(torch.zeros((1, 1), device=device))
                continue
            gate_in = modality.logits.mean(dim=0, keepdim=True)
            raw_weights.append(torch.sigmoid(self.gate(gate_in)))

        weight_tensor = torch.cat(raw_weights, dim=0).squeeze(-1)
        denom = weight_tensor.sum().clamp_min(1e-6)
        norm_weights = weight_tensor / denom

        for idx, modality in enumerate(modalities):
            logits_acc = logits_acc + norm_weights[idx] * modality.logits

        weight_dict = {name: float(norm_weights[idx].detach().cpu().item()) for idx, name in enumerate(names)}
        return LateFusionOutput(final_logits=logits_acc, modality_weights=weight_dict)

