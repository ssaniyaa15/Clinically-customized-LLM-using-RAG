import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from amca_api.main import app
from output.feedback_capture import FeedbackPayload, FeedbackStore


def test_feedback_store_persist_and_rlhf(tmp_path: Path) -> None:
    store = FeedbackStore(db_path=str(tmp_path / "feedback.db"))
    payload = FeedbackPayload(
        recommendation_id="rec-1",
        clinician_id="c1",
        action="accept",
        free_text="ok",
        patient_id="p1",
    )
    store.persist_feedback(payload)
    reward = store.forward_rlhf(payload)
    assert reward == 1.0
    conn = sqlite3.connect(str(tmp_path / "feedback.db"))
    try:
        count = conn.execute("SELECT COUNT(*) FROM clinician_feedback").fetchone()
        assert count is not None and count[0] == 1
    finally:
        conn.close()


def test_feedback_endpoint() -> None:
    client = TestClient(app)
    resp = client.post(
        "/feedback",
        json={
            "recommendation_id": "rec-2",
            "clinician_id": "c2",
            "action": "modify",
            "free_text": "adjusted",
            "patient_id": "p2",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["saved"] is True

