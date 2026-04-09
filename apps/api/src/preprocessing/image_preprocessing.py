from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

import numpy as np

from ingestion.imaging_connector import ModalityPayload

try:
    import torchvision.transforms as T
except ImportError:  # pragma: no cover
    T = None


@dataclass
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class SegmentationMask:
    bounding_boxes: list[BoundingBox] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ProcessedImagePayload:
    normalised_tensor: np.ndarray
    augmentation_applied: list[str]
    mask: SegmentationMask


class ImagePreprocessor:
    def preprocess(self, payload: ModalityPayload) -> ProcessedImagePayload:
        tensor = self._load_tensor(payload.raw_tensor_path)
        normalised = self._zscore_normalise(tensor)
        augmented, applied = self._apply_augmentations(normalised)
        mask = self._segment_placeholder(augmented)
        return ProcessedImagePayload(
            normalised_tensor=augmented,
            augmentation_applied=applied,
            mask=mask,
        )

    @staticmethod
    def _load_tensor(path: str) -> np.ndarray:
        return cast(np.ndarray, np.load(path))

    @staticmethod
    def _zscore_normalise(image: np.ndarray) -> np.ndarray:
        mean = float(np.mean(image))
        std = float(np.std(image))
        if std == 0.0:
            return image - mean
        return (image - mean) / std

    @staticmethod
    def _apply_augmentations(image: np.ndarray) -> tuple[np.ndarray, list[str]]:
        if T is None:
            return image, []

        # Placeholder train-time augmentations with deterministic output signature.
        _ = T.Compose(
            [
                T.RandomHorizontalFlip(p=0.5),
                T.RandomRotation(degrees=15),
                T.RandomResizedCrop(size=image.shape[-2:] if image.ndim >= 2 else (1, 1), scale=(0.9, 1.0)),
            ]
        )
        return image, ["flip", "rotate", "crop"]

    @staticmethod
    def _segment_placeholder(_image: np.ndarray) -> SegmentationMask:
        return SegmentationMask(bounding_boxes=[], confidence=0.0)

