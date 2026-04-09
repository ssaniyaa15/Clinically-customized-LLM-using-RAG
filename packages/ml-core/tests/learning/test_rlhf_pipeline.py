import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from learning.rlhf_pipeline import ClinicianFeedback, RLHFPipeline


def test_log_feedback_reward_and_db_write(tmp_path: Path) -> None:
    db_path = tmp_path / "fb.db"
    pipe = RLHFPipeline(db_path=str(db_path))
    fb = ClinicianFeedback(
        patient_id="p1",
        recommendation_id="r1",
        action="accept",
        free_text=None,
        timestamp=datetime.now(timezone.utc),
    )
    reward = pipe.log_feedback(fb)
    assert reward == 1.0

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT COUNT(*) FROM clinician_feedback").fetchone()
        assert rows is not None
        assert rows[0] == 1
    finally:
        conn.close()


def test_collect_episode_mean_reward(tmp_path: Path) -> None:
    db_path = tmp_path / "fb.db"
    pipe = RLHFPipeline(db_path=str(db_path))
    fbs = [
        ClinicianFeedback("p1", "r1", "accept", None, datetime.now(timezone.utc)),
        ClinicianFeedback("p2", "r2", "modify", None, datetime.now(timezone.utc)),
        ClinicianFeedback("p3", "r3", "reject", None, datetime.now(timezone.utc)),
    ]
    mean_reward = pipe.collect_episode(fbs)
    assert mean_reward == (1.0 + 0.3 - 1.0) / 3.0

