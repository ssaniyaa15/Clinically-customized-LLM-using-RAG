import numpy as np
from _pytest.monkeypatch import MonkeyPatch
from pathlib import Path

from monitoring.performance_monitor import RollingEvaluator, compute_ece, equalized_odds_gap


def test_compute_ece() -> None:
    probs = np.array([0.1, 0.8, 0.6, 0.2])
    labels = np.array([0, 1, 1, 0])
    ece = compute_ece(probs, labels, n_bins=5)
    assert ece >= 0.0


def test_equalized_odds_gap_fallback(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("monitoring.performance_monitor.fairlearn_eod", None)
    gap = equalized_odds_gap(np.array([0, 1]), np.array([0, 1]), np.array([0, 1]))
    assert gap == 0.0


def test_rolling_evaluator_persist(tmp_path: Path) -> None:
    db = tmp_path / "metrics.db"
    evaluator = RollingEvaluator(window_size=10, db_url=f"sqlite:///{db}")
    snap = evaluator.evaluate_batch(
        predictions=np.array([0.1, 0.9, 0.8, 0.2]),
        ground_truth=np.array([0, 1, 1, 0]),
        sensitive_attrs=np.array([0, 0, 1, 1]),
    )
    assert snap.n_samples == 4
    assert 0.0 <= snap.auc <= 1.0

