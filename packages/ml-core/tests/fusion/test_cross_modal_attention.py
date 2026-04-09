from typing import Any

import torch
from _pytest.monkeypatch import MonkeyPatch
from torch import nn

from fusion.cross_modal_attention import (
    ClinicalTextEncoder,
    CrossModalAttentionFusion,
    ImagingEncoder,
)


class DummyBert(nn.Module):
    def forward(self, **kwargs: Any) -> Any:
        input_ids = kwargs["input_ids"]
        b, t = input_ids.shape
        return type("Output", (), {"last_hidden_state": torch.randn(b, t, 768)})()


def test_clinical_text_encoder_fallback() -> None:
    enc = ClinicalTextEncoder()
    out = enc(["hello", "world"])
    assert out.shape[0] == 2
    assert out.shape[-1] == 768


def test_imaging_encoder_shape() -> None:
    enc = ImagingEncoder()
    images = torch.randn(2, 3, 224, 224)
    out = enc(images)
    assert out.shape[0] == 2
    assert out.shape[-1] == 768


def test_cross_modal_attention_forward(monkeypatch: MonkeyPatch) -> None:
    model = CrossModalAttentionFusion()

    monkeypatch.setattr(model, "_flash_available", lambda: False)
    texts = ["clinical note"]
    images = torch.randn(1, 3, 224, 224)
    out = model(texts, images)
    assert out.tensor.shape == (1, 768)

