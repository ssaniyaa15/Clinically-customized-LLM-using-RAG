import numpy as np
import pandas as pd
from _pytest.monkeypatch import MonkeyPatch

from monitoring.statistical_drift import (
    compute_psi,
    kl_divergence,
    ks_drift,
    mmd_drift,
    run_all_statistical_tests,
)


def test_ks_drift() -> None:
    ref = np.array([0.1, 0.2, 0.3, 0.4])
    cur = np.array([0.1, 0.2, 0.8, 0.9])
    out = ks_drift(ref, cur)
    assert 0.0 <= out.p_value <= 1.0


def test_compute_psi() -> None:
    ref = np.random.normal(0, 1, 200)
    cur = np.random.normal(0.5, 1, 200)
    out = compute_psi(ref, cur, bins=10)
    assert isinstance(out.psi_score, float)


def test_kl_divergence() -> None:
    p = np.array([0.5, 0.5])
    q = np.array([0.9, 0.1])
    out = kl_divergence(p, q)
    assert out > 0


def test_mmd_fallback(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("monitoring.statistical_drift.alibi_cd", None)
    ref = np.random.normal(0, 1, (64, 2))
    cur = np.random.normal(1, 1, (64, 2))
    out = mmd_drift(ref, cur)
    assert isinstance(out.statistic, float)


def test_run_all_statistical_tests() -> None:
    ref = pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]})
    cur = pd.DataFrame({"a": [1, 2, 10], "b": [2, 4, 6]})
    report = run_all_statistical_tests(ref, cur)
    assert "a" in report.ks_results
    assert "b" in report.psi_results

