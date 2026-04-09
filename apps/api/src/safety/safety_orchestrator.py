from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel
from torch import Tensor, nn

from reasoning.reasoning_orchestrator import ClinicalRecommendation
from safety.bias_auditor import BiasAuditor, BiasReport
from safety.human_in_loop import GatedRecommendation, gate_recommendation
from safety.regulatory_compliance import AuditEntry, AuditTrail
from safety.uncertainty_quantification import UncertaintyBundle, quantify_uncertainty


class SafetyBundle(BaseModel):
    uncertainty: UncertaintyBundle
    bias_flags: list[str]
    audit_entry: AuditEntry
    gated_recommendation: GatedRecommendation


class SafetyOrchestrator:
    def __init__(self, auditor: BiasAuditor | None = None, audit_trail: AuditTrail | None = None) -> None:
        self.auditor = auditor or BiasAuditor()
        self.audit_trail = audit_trail or AuditTrail()

    def run_safety_checks(
        self,
        model: nn.Module,
        input_tensor: Tensor,
        recommendation: ClinicalRecommendation,
    ) -> SafetyBundle:
        uncertainty = quantify_uncertainty(model, input_tensor)

        # Placeholder subgroup batch; in production this comes from monitoring/serving batch context.
        sample_df = pd.DataFrame(
            [
                {"y_true": 1, "y_pred": 1, "age_band": "60-64", "sex": "F", "race": "A", "ses_quartile": 3},
                {"y_true": 0, "y_pred": 1, "age_band": "60-64", "sex": "M", "race": "B", "ses_quartile": 1},
            ]
        )
        bias: BiasReport = self.auditor.audit_subgroups(sample_df)
        audit_entry = self.audit_trail.log_prediction(
            patient_id="unknown",
            recommendation=recommendation,
            clinician_id="system",
            action_taken="generated",
        )
        gated = gate_recommendation(recommendation)

        if uncertainty.is_high_uncertainty or bool(bias.flagged_groups):
            gated.safety_warning = (
                "Safety warning: high uncertainty and/or subgroup fairness flags detected."
            )
        return SafetyBundle(
            uncertainty=uncertainty,
            bias_flags=bias.flagged_groups,
            audit_entry=audit_entry,
            gated_recommendation=gated,
        )

