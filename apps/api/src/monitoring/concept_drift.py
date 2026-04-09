from __future__ import annotations

from dataclasses import dataclass
from typing import Any

river_drift: Any
try:
    from river import drift as river_drift
except Exception:  # pragma: no cover
    river_drift = None


class _BaseDriftMonitor:
    def __init__(self, detector: Any) -> None:
        self.detector = detector

    def update(self, value: float) -> bool:
        if self.detector is None:
            return False
        self.detector.update(value)
        return bool(getattr(self.detector, "drift_detected", False))


class ConceptDriftMonitor(_BaseDriftMonitor):
    def __init__(self) -> None:
        detector = river_drift.ADWIN() if river_drift is not None else None
        super().__init__(detector=detector)


class DDMMonitor(_BaseDriftMonitor):
    def __init__(self) -> None:
        detector = river_drift.binary.DDM() if river_drift is not None else None
        super().__init__(detector=detector)


class EDDMMonitor(_BaseDriftMonitor):
    def __init__(self) -> None:
        detector = river_drift.binary.EDDM() if river_drift is not None else None
        super().__init__(detector=detector)


@dataclass
class ConceptDriftSuite:
    adwin: ConceptDriftMonitor
    ddm: DDMMonitor
    eddm: EDDMMonitor

    @classmethod
    def build(cls) -> "ConceptDriftSuite":
        return cls(adwin=ConceptDriftMonitor(), ddm=DDMMonitor(), eddm=EDDMMonitor())

    def update_all(self, error_rate: float) -> dict[str, bool]:
        return {
            "adwin": self.adwin.update(error_rate),
            "ddm": self.ddm.update(error_rate),
            "eddm": self.eddm.update(error_rate),
        }

