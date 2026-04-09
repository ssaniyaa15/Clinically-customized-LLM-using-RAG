import torch
from torch import nn
from _pytest.monkeypatch import MonkeyPatch
from typing import cast

from learning.continual_learning import (
    ExperienceReplayBuffer,
    ReplaySample,
    apply_lora,
    compute_fisher,
    continual_train_step,
    ewc_loss,
)


class TinyNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Linear(4, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.net(x))


def _loader() -> list[dict[str, torch.Tensor]]:
    batch = {"inputs": torch.randn(8, 4), "targets": torch.randint(0, 2, (8,))}
    return [batch, batch]


def test_compute_fisher_shapes() -> None:
    model = TinyNet()
    fisher = compute_fisher(model, _loader())
    assert fisher
    for n, p in model.named_parameters():
        if p.requires_grad:
            assert fisher[n].shape == p.shape


def test_ewc_loss_non_negative() -> None:
    model = TinyNet()
    fisher = {n: torch.ones_like(p) for n, p in model.named_parameters()}
    optimal = {n: p.detach().clone() for n, p in model.named_parameters()}
    loss = ewc_loss(model, fisher=fisher, optimal_params=optimal)
    assert float(loss.item()) >= 0.0


def test_replay_buffer_add_and_sample() -> None:
    buf = ExperienceReplayBuffer(max_size=5)
    for _ in range(20):
        buf.add(ReplaySample(inputs=torch.randn(1, 4), targets=torch.randint(0, 2, (1,))))
    batch = buf.sample_batch(3)
    assert len(batch) == 3


def test_apply_lora_fallback(monkeypatch: MonkeyPatch) -> None:
    model = TinyNet()
    monkeypatch.setattr("learning.continual_learning.peft_module", None)
    out = apply_lora(model, rank=8, alpha=16)
    assert out is model


def test_continual_train_step_runs() -> None:
    model = TinyNet()
    buf = ExperienceReplayBuffer(max_size=10)
    sample = ReplaySample(inputs=torch.randn(4, 4), targets=torch.randint(0, 2, (4,)))
    fisher = {n: torch.zeros_like(p) for n, p in model.named_parameters()}
    optimal = {n: p.detach().clone() for n, p in model.named_parameters()}
    loss = continual_train_step(model, sample, buf, fisher=fisher, optimal_params=optimal)
    assert isinstance(loss, float)

