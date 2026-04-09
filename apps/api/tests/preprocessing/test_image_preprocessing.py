from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from _pytest.monkeypatch import MonkeyPatch

from ingestion.imaging_connector import ModalityPayload
from preprocessing.image_preprocessing import ImagePreprocessor


def test_zscore_normalise() -> None:
    image = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=float)
    norm = ImagePreprocessor._zscore_normalise(image)
    assert np.isclose(float(norm.mean()), 0.0, atol=1e-6)
    assert np.isclose(float(norm.std()), 1.0, atol=1e-6)


def test_apply_augmentations(monkeypatch: MonkeyPatch) -> None:
    image = np.ones((8, 8), dtype=float)
    fake_t = SimpleNamespace(
        Compose=lambda items: ("compose", items),
        RandomHorizontalFlip=lambda p: ("flip", p),
        RandomRotation=lambda degrees: ("rot", degrees),
        RandomResizedCrop=lambda size, scale: ("crop", size, scale),
    )
    monkeypatch.setattr("preprocessing.image_preprocessing.T", fake_t)
    augmented, ops = ImagePreprocessor._apply_augmentations(image)
    assert augmented.shape == image.shape
    assert ops == ["flip", "rotate", "crop"]


def test_preprocess_end_to_end(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    processor = ImagePreprocessor()
    raw = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=float)
    path = tmp_path / "tensor.npy"
    np.save(path, raw)

    monkeypatch.setattr(
        "preprocessing.image_preprocessing.T",
        SimpleNamespace(
            Compose=lambda items: ("compose", items),
            RandomHorizontalFlip=lambda p: ("flip", p),
            RandomRotation=lambda degrees: ("rot", degrees),
            RandomResizedCrop=lambda size, scale: ("crop", size, scale),
        ),
    )
    payload = ModalityPayload(
        modality_type="ct",
        patient_id="P1",
        timestamp=datetime.utcnow(),
        raw_tensor_path=str(path),
        metadata={},
    )
    out = processor.preprocess(payload)
    assert out.mask.confidence == 0.0
    assert out.augmentation_applied == ["flip", "rotate", "crop"]

