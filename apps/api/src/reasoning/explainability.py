from __future__ import annotations

import asyncio
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field
from reasoning.differential_diagnosis import DDxOutput
from shared.llm_client import llm_complete

try:
    import shap as shap_module
except Exception:  # pragma: no cover
    shap_module = None

try:
    from lime import lime_text as lime_text_module
except Exception:  # pragma: no cover
    lime_text_module = None


class ShapOutput(BaseModel):
    feature_importances: dict[str, float] = Field(default_factory=dict)
    base_value: float = 0.0


class LimeOutput(BaseModel):
    top_words: list[tuple[str, float]] = Field(default_factory=list)


class GradCamOutput(BaseModel):
    heatmap_path: str = ""
    confidence: float = 0.0


class ExplanationBundle(BaseModel):
    shap: ShapOutput | None = None
    lime: LimeOutput | None = None
    gradcam: GradCamOutput | None = None
    natural_language_rationale: str = ""


async def explain_in_natural_language(shap_output: ShapOutput, ddx: DDxOutput) -> str:
    top_diagnosis = ddx.diagnoses[0].name if ddx.diagnoses else "unknown"
    response = await llm_complete(
        system_prompt=(
            "You are a clinical AI assistant. You MUST:\n"
            "* Only answer healthcare-related questions.\n"
            "* Use ONLY the provided patient medical context.\n"
            "* If the question is not medical, respond exactly: "
            "'I can only assist with health-related queries.'\n"
            "* Never hallucinate facts not present in patient data.\n"
            "* Never provide a definitive diagnosis.\n"
            "* Always recommend consulting a doctor.\n"
            "Use simple, calm language."
        ),
        user_prompt=(
            f"Top diagnosis: {top_diagnosis}\n"
            f"Feature importances: {shap_output.feature_importances}\n"
            f"Base value: {shap_output.base_value}\n\n"
            "Explain in 2-3 short sentences why the model leaned toward this diagnosis. "
            "Do not overstate certainty."
        ),
        temperature=0.1,
        max_tokens=300,
    )
    return response.content


class ExplainabilityHead:
    """Generates SHAP/LIME explanations with a GradCAM placeholder for imaging inputs."""

    @staticmethod
    def _compute_shap(data: Any) -> ShapOutput:
        if isinstance(data, dict):
            features = list(data.keys())
            values = np.array([float(v) for v in data.values()], dtype=float).reshape(1, -1)
        else:
            arr = np.array(data, dtype=float).reshape(1, -1)
            features = [f"f{i}" for i in range(arr.shape[1])]
            values = arr

        if shap_module is None:
            return ShapOutput(feature_importances={k: 0.0 for k in features}, base_value=0.0)

        explainer = shap_module.Explainer(lambda x: np.sum(x, axis=1), values)
        shap_values = explainer(values)
        vals = np.array(shap_values.values).reshape(-1)
        importances = {features[i]: float(vals[i]) for i in range(min(len(features), len(vals)))}
        base = float(np.array(shap_values.base_values).reshape(-1)[0]) if len(vals) > 0 else 0.0
        return ShapOutput(feature_importances=importances, base_value=base)

    @staticmethod
    def _compute_lime(text: str) -> LimeOutput:
        if lime_text_module is None:
            words = text.split()[:5]
            return LimeOutput(top_words=[(w, 0.0) for w in words])

        explainer = lime_text_module.LimeTextExplainer(class_names=["neg", "pos"])
        exp = explainer.explain_instance(text, classifier_fn=lambda docs: np.tile([[0.5, 0.5]], (len(docs), 1)))
        return LimeOutput(top_words=[(word, float(weight)) for word, weight in exp.as_list()])

    @staticmethod
    def _compute_gradcam_placeholder() -> GradCamOutput:
        return GradCamOutput(heatmap_path="", confidence=0.0)

    def explain(
        self, input_type: Literal["tabular", "text", "image"], data: Any, ddx: DDxOutput | None = None
    ) -> ExplanationBundle:
        if input_type == "tabular":
            shap_output = self._compute_shap(data)
            rationale = ""
            if ddx is not None:
                try:
                    rationale = asyncio.run(explain_in_natural_language(shap_output, ddx))
                except Exception:
                    rationale = ""
            return ExplanationBundle(shap=shap_output, natural_language_rationale=rationale)
        if input_type == "text":
            return ExplanationBundle(lime=self._compute_lime(str(data)))
        return ExplanationBundle(gradcam=self._compute_gradcam_placeholder())

