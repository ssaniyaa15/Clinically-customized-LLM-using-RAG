import numpy as np
from _pytest.monkeypatch import MonkeyPatch
from typing import Any

from reasoning.differential_diagnosis import DDxOutput, Diagnosis
from reasoning.explainability import ExplainabilityHead, explain_in_natural_language


async def _fake_rationale(shap_output: object, ddx: object) -> str:
    _ = (shap_output, ddx)
    return "Fallback rationale"


def test_explain_tabular_fallback(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("reasoning.explainability.shap_module", None)
    monkeypatch.setattr(
        "reasoning.explainability.explain_in_natural_language",
        _fake_rationale,
    )
    head = ExplainabilityHead()
    out = head.explain(
        "tabular",
        {"a": 1.0, "b": 2.0},
        ddx=DDxOutput(diagnoses=[Diagnosis(name="Test", icd10_code="A00", confidence=0.8)]),
    )
    assert out.shap is not None
    assert "a" in out.shap.feature_importances
    assert out.natural_language_rationale == "Fallback rationale"


def test_explain_text_with_mocked_lime(monkeypatch: MonkeyPatch) -> None:
    class FakeExp:
        @staticmethod
        def as_list() -> list[tuple[str, float]]:
            return [("fever", 0.42)]

    class FakeLime:
        class LimeTextExplainer:
            def __init__(self, class_names: list[str]) -> None:
                self.class_names = class_names

            def explain_instance(self, text: str, classifier_fn: Any) -> FakeExp:
                _ = classifier_fn([text])
                return FakeExp()

    monkeypatch.setattr("reasoning.explainability.lime_text_module", FakeLime)
    out = ExplainabilityHead().explain("text", "fever and cough")
    assert out.lime is not None
    assert out.lime.top_words[0][0] == "fever"


def test_explain_image_placeholder() -> None:
    out = ExplainabilityHead().explain("image", np.zeros((4, 4)))
    assert out.gradcam is not None
    assert out.gradcam.confidence == 0.0


async def _fake_llm_complete(**kwargs: object) -> object:
    class _Resp:
        content = "Feature contributions support the top diagnosis."

    return _Resp()


def test_explain_in_natural_language(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("reasoning.explainability.llm_complete", _fake_llm_complete)
    shap = ExplainabilityHead._compute_shap({"bp": 1.2, "hr": -0.6})
    ddx = DDxOutput(diagnoses=[Diagnosis(name="Pneumonia", icd10_code="J18.9", confidence=0.91)])
    import asyncio

    result = asyncio.run(explain_in_natural_language(shap, ddx))
    assert "feature" in result.lower()

