from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from reasoning.differential_diagnosis import Diagnosis, DDxOutput


class Recommendation(BaseModel):
    intervention: str
    guideline_source: str
    evidence_level: str
    contraindications: list[str] = Field(default_factory=list)


class TreatmentPlan(BaseModel):
    recommendations: list[Recommendation] = Field(default_factory=list)
    requires_specialist_review: bool = False


class TreatmentRecommenderHead:
    """Applies ICD-10 prefix matching against local CPG YAML rules to produce treatment plans."""

    def __init__(self, cpg_path: str = "apps/api/data/cpgs.yaml") -> None:
        self.cpg_path = os.getenv("CPG_PATH", cpg_path)
        self.rules = self._load_cpgs()

    def _load_cpgs(self) -> list[dict[str, Any]]:
        if yaml is None:
            return []
        if not os.path.exists(self.cpg_path):
            return []
        with open(self.cpg_path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        rules = data.get("rules", [])
        if not isinstance(rules, list):
            return []
        return [r for r in rules if isinstance(r, dict)]

    @staticmethod
    def _match_rule(diagnosis: Diagnosis, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
        for rule in rules:
            prefix = str(rule.get("icd10_prefix", ""))
            if diagnosis.icd10_code.startswith(prefix):
                return rule
        return None

    def recommend(self, ddx: DDxOutput) -> TreatmentPlan:
        if not ddx.diagnoses:
            return TreatmentPlan(recommendations=[], requires_specialist_review=True)
        top = ddx.diagnoses[0]
        rule = self._match_rule(top, self.rules)
        if rule is None:
            return TreatmentPlan(recommendations=[], requires_specialist_review=True)

        recs: list[Recommendation] = []
        for item in rule.get("recommendations", []):
            if not isinstance(item, dict):
                continue
            recs.append(
                Recommendation(
                    intervention=str(item.get("intervention", "")),
                    guideline_source=str(rule.get("source", "CPG")),
                    evidence_level=str(item.get("evidence_level", "N/A")),
                    contraindications=[str(x) for x in item.get("contraindications", [])],
                )
            )
        return TreatmentPlan(recommendations=recs, requires_specialist_review=False)

