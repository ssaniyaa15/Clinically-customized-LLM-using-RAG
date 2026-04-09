import numpy as np
from _pytest.monkeypatch import MonkeyPatch
from typing import Any

from reasoning.explainability import ExplainabilityHead


def test_explain_tabular_fallback(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("reasoning.explainability.shap_module", None)
    head = ExplainabilityHead()
    out = head.explain("tabular", {"a": 1.0, "b": 2.0})
    assert out.shap is not None
    assert "a" in out.shap.feature_importances


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

