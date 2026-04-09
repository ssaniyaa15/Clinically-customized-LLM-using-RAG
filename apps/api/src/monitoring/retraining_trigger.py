from __future__ import annotations

import os
from datetime import datetime, timezone
from pydantic import BaseModel

from monitoring.performance_monitor import PerformanceSnapshot
from monitoring.statistical_drift import StatisticalDriftReport


class RetriggerEvent(BaseModel):
    trigger_reason: str
    shadow_mode: bool = True
    alert_timestamp: datetime


def ab_validate(shadow_metrics: PerformanceSnapshot, production_metrics: PerformanceSnapshot) -> bool:
    return bool(shadow_metrics.auc >= production_metrics.auc and shadow_metrics.f1 >= production_metrics.f1)


def check_and_alert(
    drift_report: StatisticalDriftReport,
    perf_snapshot: PerformanceSnapshot,
    baseline_auc: float = 0.9,
) -> RetriggerEvent | None:
    psi_thresh = float(os.getenv("RETRAIN_PSI_THRESHOLD", "0.2"))
    auc_drop_thresh = float(os.getenv("RETRAIN_AUC_DROP_THRESHOLD", "0.05"))
    fairness_thresh = float(os.getenv("RETRAIN_FAIRNESS_GAP_THRESHOLD", "0.1"))

    reasons: list[str] = []
    if any(item.psi_score > psi_thresh for item in drift_report.psi_results.values()):
        reasons.append("psi_drift")
    if (baseline_auc - perf_snapshot.auc) > auc_drop_thresh:
        reasons.append("auc_drop")
    if perf_snapshot.fairness_gap > fairness_thresh:
        reasons.append("fairness_gap")

    if not reasons:
        return None
    return RetriggerEvent(
        trigger_reason=",".join(reasons),
        shadow_mode=True,
        alert_timestamp=datetime.now(timezone.utc),
    )

