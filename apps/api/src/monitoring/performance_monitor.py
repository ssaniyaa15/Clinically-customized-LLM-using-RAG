from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel
from sklearn.metrics import f1_score, roc_auc_score
from sqlalchemy import Column, DateTime, Float, Integer, MetaData, Table, create_engine
from sqlalchemy.engine import Engine

fairlearn_metrics: Any
try:
    from fairlearn.metrics import equalized_odds_difference as fairlearn_eod
except Exception:  # pragma: no cover
    fairlearn_eod = None


class PerformanceSnapshot(BaseModel):
    auc: float
    f1: float
    ece: float
    fairness_gap: float
    n_samples: int
    timestamp: datetime


def compute_ece(probs: NDArray[np.float64], labels: NDArray[np.int_], n_bins: int = 10) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (probs >= bins[i]) & (probs < bins[i + 1])
        if not np.any(mask):
            continue
        acc = np.mean(labels[mask] == (probs[mask] >= 0.5))
        conf = np.mean(probs[mask])
        ece += np.abs(acc - conf) * (np.sum(mask) / len(probs))
    return float(ece)


def equalized_odds_gap(
    y_true: NDArray[np.int_], y_pred: NDArray[np.int_], sensitive_attr: NDArray[np.int_]
) -> float:
    if fairlearn_eod is None:
        return 0.0
    return float(fairlearn_eod(y_true=y_true, y_pred=y_pred, sensitive_features=sensitive_attr))


class RollingEvaluator:
    """Rolling performance monitor with DB persistence for model governance metrics."""

    def __init__(
        self,
        window_size: int = 500,
        db_url: str = "sqlite:///apps/api/data/monitoring_metrics.db",
    ) -> None:
        self.window_size = window_size
        self.probs: deque[float] = deque(maxlen=window_size)
        self.labels: deque[int] = deque(maxlen=window_size)
        self.sensitive: deque[int] = deque(maxlen=window_size)
        if db_url.startswith("sqlite:///"):
            raw_path = db_url.replace("sqlite:///", "", 1)
            db_parent = Path(raw_path).parent
            if str(db_parent) and str(db_parent) != ".":
                db_parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(db_url, future=True)
        self.metadata = MetaData()
        self.metrics_table = Table(
            "monitoring_metrics",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("timestamp", DateTime(timezone=True), nullable=False),
            Column("auc", Float, nullable=False),
            Column("f1", Float, nullable=False),
            Column("ece", Float, nullable=False),
            Column("fairness_gap", Float, nullable=False),
            Column("n_samples", Integer, nullable=False),
        )
        self.metadata.create_all(self.engine)

    def evaluate_batch(
        self,
        predictions: NDArray[np.float64],
        ground_truth: NDArray[np.int_],
        sensitive_attrs: NDArray[np.int_],
    ) -> PerformanceSnapshot:
        for p, y, s in zip(predictions.tolist(), ground_truth.tolist(), sensitive_attrs.tolist()):
            self.probs.append(float(p))
            self.labels.append(int(y))
            self.sensitive.append(int(s))

        probs = np.array(self.probs, dtype=float)
        labels = np.array(self.labels, dtype=int)
        sensitive = np.array(self.sensitive, dtype=int)
        pred_labels = (probs >= 0.5).astype(int)

        if len(np.unique(labels)) > 1:
            auc = float(roc_auc_score(labels, probs))
        else:
            auc = 0.5
        f1 = float(f1_score(labels, pred_labels, zero_division=0))
        ece = compute_ece(probs, labels)
        fairness_gap = equalized_odds_gap(labels, pred_labels, sensitive)
        snapshot = PerformanceSnapshot(
            auc=auc,
            f1=f1,
            ece=ece,
            fairness_gap=fairness_gap,
            n_samples=int(len(labels)),
            timestamp=datetime.now(timezone.utc),
        )
        self._persist(snapshot)
        return snapshot

    def _persist(self, snapshot: PerformanceSnapshot) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                self.metrics_table.insert(),
                {
                    "timestamp": snapshot.timestamp,
                    "auc": snapshot.auc,
                    "f1": snapshot.f1,
                    "ece": snapshot.ece,
                    "fairness_gap": snapshot.fairness_gap,
                    "n_samples": snapshot.n_samples,
                },
            )

