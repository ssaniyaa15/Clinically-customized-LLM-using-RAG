from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


@dataclass
class ClinicianFeedback:
    patient_id: str
    recommendation_id: str
    action: Literal["accept", "modify", "reject"]
    free_text: str | None
    timestamp: datetime


class RLHFPipeline:
    """Logs clinician feedback and maps actions to scalar rewards for PPO-style training."""

    REWARD_MAP = {"accept": 1.0, "modify": 0.3, "reject": -1.0}

    def __init__(self, db_path: str = "apps/api/data/feedback.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clinician_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    recommendation_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    free_text TEXT,
                    timestamp TEXT NOT NULL,
                    reward REAL NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def log_feedback(self, feedback: ClinicianFeedback) -> float:
        reward = float(self.REWARD_MAP[feedback.action])
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO clinician_feedback
                (patient_id, recommendation_id, action, free_text, timestamp, reward)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.patient_id,
                    feedback.recommendation_id,
                    feedback.action,
                    feedback.free_text,
                    feedback.timestamp.isoformat(),
                    reward,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return reward

    def collect_episode(self, feedbacks: list[ClinicianFeedback]) -> float:
        if not feedbacks:
            return 0.0
        rewards = [self.log_feedback(fb) for fb in feedbacks]
        mean_reward = sum(rewards) / len(rewards)
        # TODO: Implement PPO update step over collected episode trajectories.
        return float(mean_reward)

