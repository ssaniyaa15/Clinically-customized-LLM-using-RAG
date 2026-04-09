from reasoning.differential_diagnosis import DDxOutput, Diagnosis
from learning.active_learning import build_labeling_queue, select_uncertain_cases


def test_select_uncertain_cases_entropy() -> None:
    preds = [
        DDxOutput(diagnoses=[Diagnosis(name="A", icd10_code="A", confidence=0.99, evidence_snippets=[])]),
        DDxOutput(
            diagnoses=[
                Diagnosis(name="A", icd10_code="A", confidence=0.5, evidence_snippets=[]),
                Diagnosis(name="B", icd10_code="B", confidence=0.5, evidence_snippets=[]),
            ]
        ),
    ]
    selected = select_uncertain_cases(preds, n=1)
    assert selected == ["patient-1"]


def test_build_labeling_queue() -> None:
    preds = [DDxOutput(diagnoses=[])]
    queue = build_labeling_queue(preds, n=1)
    assert queue.selection_strategy == "entropy"
    assert len(queue.cases) == 1
    assert queue.cases[0].patient_id == "patient-0"

