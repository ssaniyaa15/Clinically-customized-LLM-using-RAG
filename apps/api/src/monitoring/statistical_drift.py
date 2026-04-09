from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pydantic import BaseModel, Field
from scipy.stats import ks_2samp

try:
    from alibi_detect.cd import MMDDrift as alibi_cd
except Exception:  # pragma: no cover
    alibi_cd = None


class DriftResult(BaseModel):
    statistic: float
    p_value: float
    is_drift: bool
    threshold: float = 0.05


class PSIResult(BaseModel):
    psi_score: float
    is_drift: bool
    threshold: float = 0.2


class StatisticalDriftReport(BaseModel):
    ks_results: dict[str, DriftResult] = Field(default_factory=dict)
    psi_results: dict[str, PSIResult] = Field(default_factory=dict)
    mmd_result: DriftResult
    kl_results: dict[str, float] = Field(default_factory=dict)


def ks_drift(reference: NDArray[np.float64], current: NDArray[np.float64], threshold: float = 0.05) -> DriftResult:
    statistic, p_value = ks_2samp(reference, current)
    return DriftResult(
        statistic=float(statistic),
        p_value=float(p_value),
        is_drift=bool(p_value < threshold),
        threshold=threshold,
    )


def compute_psi(
    reference: NDArray[np.float64], current: NDArray[np.float64], bins: int = 10, threshold: float = 0.2
) -> PSIResult:
    r_hist, bin_edges = np.histogram(reference, bins=bins)
    c_hist, _ = np.histogram(current, bins=bin_edges)
    r = np.where(r_hist == 0, 1e-6, r_hist) / max(1, np.sum(r_hist))
    c = np.where(c_hist == 0, 1e-6, c_hist) / max(1, np.sum(c_hist))
    psi = float(np.sum((c - r) * np.log(c / r)))
    return PSIResult(psi_score=psi, is_drift=psi > threshold, threshold=threshold)


def mmd_drift(reference: NDArray[np.float64], current: NDArray[np.float64], kernel: str = "rbf") -> DriftResult:
    if alibi_cd is None:
        # Fallback proxy when detector unavailable.
        statistic = float(abs(np.mean(reference) - np.mean(current)))
        p_value = float(np.exp(-statistic))
        return DriftResult(statistic=statistic, p_value=p_value, is_drift=p_value < 0.05, threshold=0.05)
    detector = alibi_cd(reference, backend="pytorch")
    pred = detector.predict(current)
    data = pred.get("data", {})
    p_val = float(data.get("p_val", 1.0))
    distance = float(data.get("distance", 0.0))
    thresh = float(data.get("threshold", 0.05))
    return DriftResult(statistic=distance, p_value=p_val, is_drift=p_val < thresh, threshold=thresh)


def kl_divergence(p: NDArray[np.float64], q: NDArray[np.float64]) -> float:
    p = p.astype(float)
    q = q.astype(float)
    p = np.where(p <= 0, 1e-12, p)
    q = np.where(q <= 0, 1e-12, q)
    p = p / np.sum(p)
    q = q / np.sum(q)
    return float(np.sum(p * np.log(p / q)))


def run_all_statistical_tests(reference_df: pd.DataFrame, current_df: pd.DataFrame) -> StatisticalDriftReport:
    common_cols = [c for c in reference_df.columns if c in current_df.columns]
    ks_results: dict[str, DriftResult] = {}
    psi_results: dict[str, PSIResult] = {}
    kl_results: dict[str, float] = {}

    for col in common_cols:
        ref = reference_df[col].to_numpy(dtype=float)
        cur = current_df[col].to_numpy(dtype=float)
        ks_results[col] = ks_drift(ref, cur)
        psi_results[col] = compute_psi(ref, cur)
        ref_hist, bin_edges = np.histogram(ref, bins=10)
        cur_hist, _ = np.histogram(cur, bins=bin_edges)
        kl_results[col] = kl_divergence(ref_hist.astype(float), cur_hist.astype(float))

    mmd_ref = reference_df[common_cols].to_numpy(dtype=float) if common_cols else np.zeros((1, 1))
    mmd_cur = current_df[common_cols].to_numpy(dtype=float) if common_cols else np.zeros((1, 1))
    mmd_result = mmd_drift(mmd_ref, mmd_cur)
    return StatisticalDriftReport(
        ks_results=ks_results,
        psi_results=psi_results,
        mmd_result=mmd_result,
        kl_results=kl_results,
    )

