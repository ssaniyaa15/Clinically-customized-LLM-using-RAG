from datetime import datetime, timezone

from monitoring.performance_monitor import PerformanceSnapshot
from monitoring.retraining_trigger import ab_validate, check_and_alert
from monitoring.statistical_drift import DriftResult, PSIResult, StatisticalDriftReport


def _report(psi: float) -> StatisticalDriftReport:
    return StatisticalDriftReport(
        ks_results={},
        psi_results={"x": PSIResult(psi_score=psi, is_drift=psi > 0.2, threshold=0.2)},
        mmd_result=DriftResult(statistic=0.0, p_value=1.0, is_drift=False, threshold=0.05),
        kl_results={},
    )


def _snap(auc: float, fairness_gap: float) -> PerformanceSnapshot:
    return PerformanceSnapshot(
        auc=auc,
        f1=0.7,
        ece=0.1,
        fairness_gap=fairness_gap,
        n_samples=20,
        timestamp=datetime.now(timezone.utc),
    )


def test_check_and_alert_triggered() -> None:
    event = check_and_alert(_report(0.3), _snap(0.8, 0.15), baseline_auc=0.9)
    assert event is not None
    assert event.shadow_mode


def test_check_and_alert_none() -> None:
    event = check_and_alert(_report(0.1), _snap(0.89, 0.05), baseline_auc=0.9)
    assert event is None


def test_ab_validate() -> None:
    ok = ab_validate(_snap(0.9, 0.01), _snap(0.8, 0.1))
    assert ok

