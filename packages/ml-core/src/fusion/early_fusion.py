from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn


@dataclass
class EHREmbedding:
    tensor: Tensor


@dataclass
class OmicsEmbedding:
    tensor: Tensor


@dataclass
class JointEmbedding:
    tensor: Tensor


class EarlyFusionMLP(nn.Module):
    """Projects concatenated EHR+omics vectors into a shared 512-d latent space."""

    def __init__(self, input_dim: int = 512, hidden_dim: int = 1024, output_dim: int = 512) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, ehr_embedding: EHREmbedding, omics_embedding: OmicsEmbedding) -> JointEmbedding:
        if ehr_embedding.tensor.shape[-1] != 256:
            raise ValueError("EHREmbedding must be 256-dim.")
        if omics_embedding.tensor.shape[-1] != 256:
            raise ValueError("OmicsEmbedding must be 256-dim.")
        fused = torch.cat([ehr_embedding.tensor, omics_embedding.tensor], dim=-1)
        return JointEmbedding(tensor=self.network(fused))

