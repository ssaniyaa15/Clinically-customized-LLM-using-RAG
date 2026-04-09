from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer


@dataclass
class ImputedDataFrame:
    imputed_df: pd.DataFrame
    outlier_flags: list[str]
    imputation_report: dict[str, Any]


def _fit_imputer(df: pd.DataFrame) -> tuple[pd.DataFrame, IterativeImputer]:
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        return df.copy(), IterativeImputer(random_state=42)

    imputer = IterativeImputer(random_state=42, sample_posterior=False)
    transformed = imputer.fit_transform(df[numeric_cols])
    imputed_df = df.copy()
    imputed_df[numeric_cols] = transformed
    return imputed_df, imputer


def _flag_outliers_iqr(df: pd.DataFrame, threshold: float = 3.0) -> list[str]:
    flags: list[str] = []
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    for col in numeric_cols:
        series = df[col]
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        outlier_idx = series[(series < lower) | (series > upper)].index.tolist()
        for idx in outlier_idx:
            flags.append(f"{col}@row{idx}")
    return flags


def impute_and_qc(df: pd.DataFrame) -> ImputedDataFrame:
    imputed_df, imputer = _fit_imputer(df)
    outlier_flags = _flag_outliers_iqr(imputed_df, threshold=3.0)
    report = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
        "missing_before": int(df.isna().sum().sum()),
        "missing_after": int(imputed_df.isna().sum().sum()),
        "n_outlier_flags": len(outlier_flags),
        "imputer_max_iter": int(getattr(imputer, "max_iter", 0)),
    }
    return ImputedDataFrame(imputed_df=imputed_df, outlier_flags=outlier_flags, imputation_report=report)

