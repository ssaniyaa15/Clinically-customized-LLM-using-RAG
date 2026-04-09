import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from safety.bias_auditor import BiasAuditor


def test_audit_subgroups_and_append_only(tmp_path: Path) -> None:
    db = tmp_path / "audit.db"
    auditor = BiasAuditor(db_path=str(db))
    df = pd.DataFrame(
        [
            {"y_true": 1, "y_pred": 1, "age_band": "60-64", "sex": "F", "race": "A", "ses_quartile": 1},
            {"y_true": 0, "y_pred": 1, "age_band": "60-64", "sex": "M", "race": "B", "ses_quartile": 2},
            {"y_true": 1, "y_pred": 0, "age_band": "30-34", "sex": "F", "race": "B", "ses_quartile": 3},
        ]
    )
    report = auditor.audit_subgroups(df)
    assert isinstance(report.flagged_groups, list)

    conn = sqlite3.connect(str(db))
    try:
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("DELETE FROM audit_log")
    finally:
        conn.close()

