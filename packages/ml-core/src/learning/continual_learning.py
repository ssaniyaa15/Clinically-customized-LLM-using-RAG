from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, cast

import torch
from torch import Tensor, nn

peft_module: Any
try:
    import peft as peft_module
except Exception:  # pragma: no cover
    peft_module = None


def compute_fisher(model: nn.Module, dataloader: Any) -> dict[str, Tensor]:
    """Estimate diagonal Fisher information from gradients over a dataloader."""
    fisher: dict[str, Tensor] = {
        n: torch.zeros_like(p, device=p.device) for n, p in model.named_parameters() if p.requires_grad
    }
    model.eval()
    for batch in dataloader:
        inputs = batch["inputs"]
        targets = batch["targets"]
        logits = model(inputs)
        loss = nn.CrossEntropyLoss()(logits, targets)
        model.zero_grad(set_to_none=True)
        loss.backward()
        for n, p in model.named_parameters():
            if p.requires_grad and p.grad is not None:
                fisher[n] += p.grad.detach() ** 2
    denom = max(1, len(dataloader))
    for n in fisher:
        fisher[n] /= float(denom)
    return fisher


def ewc_loss(
    model: nn.Module,
    fisher: dict[str, Tensor],
    optimal_params: dict[str, Tensor],
    lambda_: float = 400.0,
) -> Tensor:
    """Compute EWC regularization term penalizing drift from previous optimal parameters."""
    penalty = torch.tensor(0.0, device=next(model.parameters()).device)
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if n in fisher and n in optimal_params:
            penalty = penalty + (fisher[n] * (p - optimal_params[n]) ** 2).sum()
    return 0.5 * lambda_ * penalty


@dataclass
class ReplaySample:
    inputs: Tensor
    targets: Tensor


class ExperienceReplayBuffer:
    """Reservoir-sampling replay buffer for continual learning."""

    def __init__(self, max_size: int = 10000) -> None:
        self.max_size = max_size
        self._buffer: list[ReplaySample] = []
        self._seen = 0

    def add(self, sample: ReplaySample) -> None:
        self._seen += 1
        if len(self._buffer) < self.max_size:
            self._buffer.append(sample)
            return
        idx = random.randint(0, self._seen - 1)
        if idx < self.max_size:
            self._buffer[idx] = sample

    def sample_batch(self, n: int) -> list[ReplaySample]:
        if not self._buffer:
            return []
        k = min(n, len(self._buffer))
        return random.sample(self._buffer, k)


def apply_lora(model: nn.Module, rank: int = 8, alpha: int = 16) -> nn.Module:
    """Attach LoRA adapters via peft and return the adapted model."""
    if peft_module is None:
        return model
    config = peft_module.LoraConfig(
        r=rank,
        lora_alpha=alpha,
        target_modules="all-linear",
        lora_dropout=0.0,
        bias="none",
    )
    return cast(nn.Module, peft_module.get_peft_model(model, config))


def continual_train_step(
    model: nn.Module,
    new_batch: ReplaySample,
    replay_buffer: ExperienceReplayBuffer,
    fisher: dict[str, Tensor],
    optimal_params: dict[str, Tensor],
) -> float:
    """Single continual-learning step with replay + EWC regularization."""
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    replay = replay_buffer.sample_batch(4)
    all_inputs = [new_batch.inputs] + [s.inputs for s in replay]
    all_targets = [new_batch.targets] + [s.targets for s in replay]
    x = torch.cat(all_inputs, dim=0)
    y = torch.cat(all_targets, dim=0)

    logits = model(x)
    ce = nn.CrossEntropyLoss()(logits, y)
    loss = ce + ewc_loss(model, fisher=fisher, optimal_params=optimal_params, lambda_=400.0)

    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()

    replay_buffer.add(new_batch)
    return float(loss.detach().cpu().item())

