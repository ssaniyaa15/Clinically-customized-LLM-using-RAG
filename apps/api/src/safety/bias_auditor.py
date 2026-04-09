from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class BiasReport(BaseModel):
    subgroup_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    flagged_groups: list[str] = Field(default_factory=list)
    audit_timestamp: datetime


class BiasAuditor:
    """Subgroup fairness auditor with append-only immutable SQLite audit log."""

    def __init__(self, db_path: str = "apps/api/data/bias_audit.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    subgroup TEXT NOT NULL,
                    tpr REAL NOT NULL,
                    fpr REAL NOT NULL,
                    flagged INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS audit_log_no_update
                BEFORE UPDATE ON audit_log
                BEGIN
                    SELECT RAISE(FAIL, 'audit_log is append-only');
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
                BEFORE DELETE ON audit_log
                BEGIN
                    SELECT RAISE(FAIL, 'audit_log is append-only');
                END;
                """
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _rates(y_true: Any, y_pred: Any) -> tuple[float, float]:
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        tpr = float(tp / max(1, tp + fn))
        fpr = float(fp / max(1, fp + tn))
        return tpr, fpr

    def audit_subgroups(
        self,
        predictions_df: pd.DataFrame,
        sensitive_cols: list[str] | None = None,
    ) -> BiasReport:
        sensitive_cols = sensitive_cols or ["age_band", "sex", "race", "ses_quartile"]
        y_true = predictions_df["y_true"].to_numpy(dtype=int)
        y_pred = predictions_df["y_pred"].to_numpy(dtype=int)
        overall_tpr, overall_fpr = self._rates(y_true, y_pred)

        subgroup_metrics: dict[str, dict[str, float]] = {}
        flagged: list[str] = []

        for col in sensitive_cols:
            if col not in predictions_df.columns:
                continue
            for value in predictions_df[col].dropna().unique().tolist():
                mask = predictions_df[col] == value
                sub_true = predictions_df.loc[mask, "y_true"].to_numpy(dtype=int)
                sub_pred = predictions_df.loc[mask, "y_pred"].to_numpy(dtype=int)
                tpr, fpr = self._rates(sub_true, sub_pred)
                key = f"{col}={value}"
                subgroup_metrics[key] = {"tpr": tpr, "fpr": fpr}
                if abs(tpr - overall_tpr) > 0.05 or abs(fpr - overall_fpr) > 0.05:
                    flagged.append(key)
                self._log_row(key, tpr, fpr, key in flagged)

        return BiasReport(
            subgroup_metrics=subgroup_metrics,
            flagged_groups=flagged,
            audit_timestamp=datetime.now(timezone.utc),
        )

    def _log_row(self, subgroup: str, tpr: float, fpr: float, flagged: bool) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO audit_log (timestamp, subgroup, tpr, fpr, flagged) VALUES (?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), subgroup, tpr, fpr, int(flagged)),
            )
            conn.commit()
        finally:
            conn.close()

