from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field
from shared.llm_client import llm_complete

from reasoning.reasoning_orchestrator import ClinicalRecommendation


@dataclass
class ClinicianFeedback:
    patient_id: str
    recommendation_id: str
    action: Literal["accept", "modify", "reject"]
    free_text: str | None
    timestamp: datetime


class ParsedFeedback(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    key_concerns: list[str] = Field(default_factory=list)
    suggested_correction: str | None = None


async def parse_free_text_feedback(
    free_text: str, recommendation: ClinicalRecommendation
) -> ParsedFeedback:
    top_diagnosis = (
        recommendation.ddx.diagnoses[0].name if recommendation.ddx.diagnoses else "unknown"
    )
    response = await llm_complete(
        system_prompt=(
            "You are a clinical AI trainer. Parse the clinician's free-text override "
            "comment into structured feedback."
        ),
        user_prompt=(
            f"Clinician comment: {free_text}\n"
            f"Original recommendation summary: {top_diagnosis}"
        ),
        json_mode=True,
        temperature=0.0,
    )
    try:
        payload = json.loads(response.content)
        return ParsedFeedback(**payload)
    except Exception:
        return ParsedFeedback(sentiment="neutral", key_concerns=[], suggested_correction=None)


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
                    reward REAL NOT NULL,
                    parsed_sentiment TEXT,
                    parsed_key_concerns TEXT,
                    parsed_suggested_correction TEXT
                )
                """
            )
            cols = {
                row[1] for row in conn.execute("PRAGMA table_info(clinician_feedback)").fetchall()
            }
            if "parsed_sentiment" not in cols:
                conn.execute("ALTER TABLE clinician_feedback ADD COLUMN parsed_sentiment TEXT")
            if "parsed_key_concerns" not in cols:
                conn.execute("ALTER TABLE clinician_feedback ADD COLUMN parsed_key_concerns TEXT")
            if "parsed_suggested_correction" not in cols:
                conn.execute(
                    "ALTER TABLE clinician_feedback ADD COLUMN parsed_suggested_correction TEXT"
                )
            conn.commit()
        finally:
            conn.close()

    def log_feedback(
        self, feedback: ClinicianFeedback, recommendation: ClinicalRecommendation | None = None
    ) -> float:
        reward = float(self.REWARD_MAP[feedback.action])
        parsed: ParsedFeedback | None = None
        if feedback.free_text and recommendation is not None:
            parsed = asyncio.run(parse_free_text_feedback(feedback.free_text, recommendation))
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO clinician_feedback
                (
                    patient_id,
                    recommendation_id,
                    action,
                    free_text,
                    timestamp,
                    reward,
                    parsed_sentiment,
                    parsed_key_concerns,
                    parsed_suggested_correction
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.patient_id,
                    feedback.recommendation_id,
                    feedback.action,
                    feedback.free_text,
                    feedback.timestamp.isoformat(),
                    reward,
                    parsed.sentiment if parsed is not None else None,
                    json.dumps(parsed.key_concerns) if parsed is not None else None,
                    parsed.suggested_correction if parsed is not None else None,
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

