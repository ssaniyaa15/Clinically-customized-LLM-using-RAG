from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Any

from fastapi import APIRouter
from pydantic import BaseModel

from learning.rlhf_pipeline import ClinicianFeedback, RLHFPipeline

confluent_kafka: Any
try:
    import confluent_kafka
except Exception:  # pragma: no cover
    confluent_kafka = None

Producer: Any = getattr(confluent_kafka, "Producer", None)

router = APIRouter(tags=["feedback"])


class FeedbackPayload(BaseModel):
    recommendation_id: str
    clinician_id: str
    action: Literal["accept", "modify", "reject"]
    free_text: str | None = None
    patient_id: str = "unknown"


class FeedbackResponse(BaseModel):
    saved: bool
    kafka_published: bool
    reward: float


class FeedbackStore:
    def __init__(self, db_path: str = "apps/api/data/feedback_capture.db") -> None:
        self.db_path = db_path
        db_parent = Path(db_path).parent
        db_parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.rlhf = RLHFPipeline(db_path=str(db_parent / "feedback_rlhf.db"))
        self.producer = None

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clinician_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recommendation_id TEXT NOT NULL,
                    clinician_id TEXT NOT NULL,
                    patient_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    free_text TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def persist_feedback(self, payload: FeedbackPayload) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO clinician_feedback
                (recommendation_id, clinician_id, patient_id, action, free_text, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.recommendation_id,
                    payload.clinician_id,
                    payload.patient_id,
                    payload.action,
                    payload.free_text,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def publish_kafka(self, payload: FeedbackPayload) -> bool:
        if self.producer is None and Producer is not None:
            try:
                self.producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")})
            except Exception:
                self.producer = None
        if self.producer is None:
            return False
        try:
            self.producer.produce("clinician.feedback", value=payload.model_dump_json().encode("utf-8"))
            self.producer.poll(0)
            return True
        except Exception:
            return False

    def forward_rlhf(self, payload: FeedbackPayload) -> float:
        feedback = ClinicianFeedback(
            patient_id=payload.patient_id,
            recommendation_id=payload.recommendation_id,
            action=payload.action,
            free_text=payload.free_text,
            timestamp=datetime.now(timezone.utc),
        )
        return self.rlhf.log_feedback(feedback)


_store = FeedbackStore()


@router.post("/feedback", response_model=FeedbackResponse)
def post_feedback(payload: FeedbackPayload) -> FeedbackResponse:
    _store.persist_feedback(payload)
    kafka_ok = _store.publish_kafka(payload)
    reward = _store.forward_rlhf(payload)
    return FeedbackResponse(saved=True, kafka_published=kafka_ok, reward=reward)

