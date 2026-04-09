import pytest
import torch

from fusion.late_fusion import LateFusionEnsembler, ModalityOutput


def test_late_fusion_output_shape_and_weights() -> None:
    model = LateFusionEnsembler(num_classes=3)
    a = ModalityOutput(name="a", logits=torch.randn(2, 3), modality_present=True)
    b = ModalityOutput(name="b", logits=torch.randn(2, 3), modality_present=True)
    c = ModalityOutput(name="c", logits=torch.randn(2, 3), modality_present=True)
    out = model(a, b, c)
    assert out.final_logits.shape == (2, 3)
    assert pytest.approx(sum(out.modality_weights.values()), rel=1e-5) == 1.0


def test_late_fusion_missing_modality_forces_zero_weight() -> None:
    model = LateFusionEnsembler(num_classes=2)
    a = ModalityOutput(name="a", logits=torch.randn(1, 2), modality_present=True)
    b = ModalityOutput(name="b", logits=torch.randn(1, 2), modality_present=False)
    c = ModalityOutput(name="c", logits=torch.randn(1, 2), modality_present=True)
    out = model(a, b, c)
    assert out.modality_weights["b"] == 0.0


def test_late_fusion_requires_at_least_one_modality() -> None:
    model = LateFusionEnsembler(num_classes=2)
    with pytest.raises(ValueError):
        model(None, None, None)

