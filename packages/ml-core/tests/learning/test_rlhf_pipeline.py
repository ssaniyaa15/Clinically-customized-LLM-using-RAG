import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from learning.rlhf_pipeline import ClinicianFeedback, ParsedFeedback, RLHFPipeline
from reasoning.differential_diagnosis import DDxOutput, Diagnosis
from reasoning.explainability import ExplanationBundle
from reasoning.reasoning_orchestrator import ClinicalRecommendation
from reasoning.risk_prognosis import (
    ComplicationRisks,
    ReadmissionRisk,
    RiskPrognosisOutput,
    SurvivalCurve,
)
from reasoning.treatment_recommender import TreatmentPlan


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


def _rec() -> ClinicalRecommendation:
    return ClinicalRecommendation(
        ddx=DDxOutput(
            diagnoses=[Diagnosis(name="Pneumonia", icd10_code="J18.9", confidence=0.9, evidence_snippets=[])]
        ),
        treatment=TreatmentPlan(recommendations=[], requires_specialist_review=False),
        risk=RiskPrognosisOutput(
            readmission=ReadmissionRisk(probability=0.8, risk_tier="high"),
            survival=SurvivalCurve(time_points=[0.0], survival_probabilities=[1.0]),
            complications=ComplicationRisks(risks={}),
        ),
        explanations={"tabular": ExplanationBundle()},
        generated_at=datetime.now(timezone.utc),
        uncertainty_score=0.2,
    )


async def _fake_parse_feedback(free_text: str, recommendation: ClinicalRecommendation) -> ParsedFeedback:
    _ = (free_text, recommendation)
    return ParsedFeedback(
        sentiment="negative",
        key_concerns=["dose mismatch", "contraindication risk"],
        suggested_correction="reduce empiric dose and re-evaluate interactions",
    )


def test_log_feedback_stores_parsed_feedback(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    db_path = tmp_path / "fb.db"
    pipe = RLHFPipeline(db_path=str(db_path))
    monkeypatch.setattr("learning.rlhf_pipeline.parse_free_text_feedback", _fake_parse_feedback)
    fb = ClinicianFeedback(
        patient_id="p4",
        recommendation_id="r4",
        action="modify",
        free_text="Dose too high for this patient profile.",
        timestamp=datetime.now(timezone.utc),
    )
    reward = pipe.log_feedback(fb, recommendation=_rec())
    assert reward == 0.3

    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT parsed_sentiment, parsed_key_concerns, parsed_suggested_correction "
            "FROM clinician_feedback WHERE recommendation_id = 'r4'"
        ).fetchone()
        assert row is not None
        assert row[0] == "negative"
        assert "dose mismatch" in str(row[1])
        assert "reduce empiric dose" in str(row[2])
    finally:
        conn.close()

