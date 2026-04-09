from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel, Field

from monitoring.concept_drift import ConceptDriftSuite
from monitoring.performance_monitor import PerformanceSnapshot, RollingEvaluator
from monitoring.retraining_trigger import RetriggerEvent, check_and_alert
from monitoring.statistical_drift import DriftResult, StatisticalDriftReport, run_all_statistical_tests

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MonitoringPayload(BaseModel):
    reference: list[dict[str, float]]
    current: list[dict[str, float]]
    predictions: list[float]
    ground_truth: list[int]
    sensitive_attrs: list[int]
    error_rate: float


class MonitoringIngestResponse(BaseModel):
    drift_report: StatisticalDriftReport
    performance: PerformanceSnapshot
    concept_drift: dict[str, bool]
    retrigger_event: RetriggerEvent | None


_latest_drift: StatisticalDriftReport | None = None
_latest_perf: PerformanceSnapshot | None = None
_concept_suite = ConceptDriftSuite.build()
_rolling_eval = RollingEvaluator()


def _empty_report() -> StatisticalDriftReport:
    return StatisticalDriftReport(
        ks_results={},
        psi_results={},
        mmd_result=DriftResult(statistic=0.0, p_value=1.0, is_drift=False, threshold=0.05),
        kl_results={},
    )


@router.get("/drift", response_model=StatisticalDriftReport)
def get_latest_drift() -> StatisticalDriftReport:
    return _latest_drift or _empty_report()


@router.get("/performance", response_model=PerformanceSnapshot)
def get_latest_performance() -> PerformanceSnapshot:
    return _latest_perf or PerformanceSnapshot(
        auc=0.0,
        f1=0.0,
        ece=0.0,
        fairness_gap=0.0,
        n_samples=0,
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/ingest", response_model=MonitoringIngestResponse)
def ingest_monitoring(payload: MonitoringPayload) -> MonitoringIngestResponse:
    global _latest_drift, _latest_perf
    reference_df = pd.DataFrame(payload.reference)
    current_df = pd.DataFrame(payload.current)
    drift_report = run_all_statistical_tests(reference_df, current_df)
    perf_snapshot = _rolling_eval.evaluate_batch(
        predictions=np.array(payload.predictions, dtype=float),
        ground_truth=np.array(payload.ground_truth, dtype=int),
        sensitive_attrs=np.array(payload.sensitive_attrs, dtype=int),
    )
    concept_flags = _concept_suite.update_all(payload.error_rate)
    event = check_and_alert(drift_report, perf_snapshot)
    _latest_drift = drift_report
    _latest_perf = perf_snapshot
    return MonitoringIngestResponse(
        drift_report=drift_report,
        performance=perf_snapshot,
        concept_drift=concept_flags,
        retrigger_event=event,
    )

