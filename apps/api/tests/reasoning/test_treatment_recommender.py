from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from reasoning.differential_diagnosis import DDxOutput, Diagnosis
from reasoning.treatment_recommender import TreatmentRecommenderHead


async def _fake_explain_treatment(plan: object, top_diagnosis: object) -> str:
    _ = (plan, top_diagnosis)
    return "CPG match rationale."


def test_recommend_with_matching_rule(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cpg = tmp_path / "cpgs.yaml"
    cpg.write_text(
        "rules:\n"
        "  - icd10_prefix: J18\n"
        "    source: IDSA-2023\n"
        "    recommendations:\n"
        "      - intervention: Start empiric antibiotics\n"
        "        evidence_level: A\n"
        "        contraindications: [allergy]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("reasoning.treatment_recommender.explain_treatment", _fake_explain_treatment)
    head = TreatmentRecommenderHead(cpg_path=str(cpg))
    ddx = DDxOutput(
        diagnoses=[Diagnosis(name="Pneumonia", icd10_code="J18.9", confidence=0.9, evidence_snippets=[])]
    )
    plan = head.recommend(ddx)
    assert not plan.requires_specialist_review
    assert plan.recommendations[0].guideline_source == "IDSA-2023"
    assert plan.treatment_rationale == "CPG match rationale."


def test_recommend_no_match_requires_review(tmp_path: Path) -> None:
    cpg = tmp_path / "cpgs.yaml"
    cpg.write_text("rules: []\n", encoding="utf-8")
    head = TreatmentRecommenderHead(cpg_path=str(cpg))
    ddx = DDxOutput(diagnoses=[Diagnosis(name="Dx", icd10_code="A00", confidence=0.5, evidence_snippets=[])])
    plan = head.recommend(ddx)
    assert plan.requires_specialist_review
    assert plan.recommendations == []
    assert plan.treatment_rationale == ""

