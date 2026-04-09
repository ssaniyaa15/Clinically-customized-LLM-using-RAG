from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import log

from reasoning.differential_diagnosis import DDxOutput


@dataclass
class ActiveCase:
    patient_id: str
    uncertainty: float


@dataclass
class LabelingQueue:
    cases: list[ActiveCase] = field(default_factory=list)
    selection_strategy: str = "entropy"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _entropy(probs: list[float]) -> float:
    eps = 1e-12
    return -sum(p * log(max(p, eps)) for p in probs if p > 0)


def select_uncertain_cases(predictions: list[DDxOutput], n: int) -> list[str]:
    scored: list[tuple[str, float]] = []
    for idx, ddx in enumerate(predictions):
        if not ddx.diagnoses:
            scored.append((f"patient-{idx}", float("inf")))
            continue
        confs = [max(0.0, min(1.0, float(d.confidence))) for d in ddx.diagnoses]
        total = sum(confs)
        probs = [c / total for c in confs] if total > 0 else [1.0 / len(confs)] * len(confs)
        scored.append((f"patient-{idx}", _entropy(probs)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [pid for pid, _ in scored[: max(0, n)]]


def build_labeling_queue(predictions: list[DDxOutput], n: int) -> LabelingQueue:
    ids = select_uncertain_cases(predictions, n)
    id_to_unc: dict[str, float] = {}
    for idx, ddx in enumerate(predictions):
        pid = f"patient-{idx}"
        if not ddx.diagnoses:
            id_to_unc[pid] = float("inf")
            continue
        confs = [max(0.0, min(1.0, float(d.confidence))) for d in ddx.diagnoses]
        total = sum(confs)
        probs = [c / total for c in confs] if total > 0 else [1.0 / len(confs)] * len(confs)
        id_to_unc[pid] = _entropy(probs)
    cases = [ActiveCase(patient_id=pid, uncertainty=id_to_unc.get(pid, 0.0)) for pid in ids]
    return LabelingQueue(cases=cases, selection_strategy="entropy")

