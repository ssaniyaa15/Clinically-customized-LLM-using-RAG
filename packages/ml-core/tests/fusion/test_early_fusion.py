import pytest
import torch

from fusion.early_fusion import EHREmbedding, EarlyFusionMLP, OmicsEmbedding


def test_early_fusion_shape() -> None:
    model = EarlyFusionMLP()
    ehr = EHREmbedding(tensor=torch.randn(2, 256))
    omics = OmicsEmbedding(tensor=torch.randn(2, 256))
    out = model(ehr, omics)
    assert out.tensor.shape == (2, 512)


def test_early_fusion_rejects_bad_dims() -> None:
    model = EarlyFusionMLP()
    ehr = EHREmbedding(tensor=torch.randn(1, 128))
    omics = OmicsEmbedding(tensor=torch.randn(1, 256))
    with pytest.raises(ValueError):
        model(ehr, omics)

