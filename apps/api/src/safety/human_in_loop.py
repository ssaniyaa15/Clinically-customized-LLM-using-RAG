from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from reasoning.reasoning_orchestrator import ClinicalRecommendation


class GatedRecommendation(BaseModel):
    recommendation: ClinicalRecommendation
    requires_confirmation: bool = True
    escalation_level: Literal["routine", "urgent", "critical"]
    override_allowed: bool = True
    safety_warning: str | None = None


class ConfirmPayload(BaseModel):
    clinician_id: str
    recommendation_id: str
    confirmed: bool


class OverridePayload(BaseModel):
    clinician_id: str
    recommendation_id: str
    reason: str


class GateActionResponse(BaseModel):
    status: str
    timestamp: datetime


def gate_recommendation(rec: ClinicalRecommendation) -> GatedRecommendation:
    has_critical_ddx = any(d.confidence > 0.85 for d in rec.ddx.diagnoses)
    is_high_risk = rec.risk.readmission.risk_tier == "high"
    escalation: Literal["routine", "urgent", "critical"]
    if has_critical_ddx and is_high_risk:
        escalation = "critical"
    elif rec.uncertainty_score > 0.4:
        escalation = "urgent"
    else:
        escalation = "routine"
    return GatedRecommendation(recommendation=rec, escalation_level=escalation)


gate_router = APIRouter(prefix="/gate", tags=["human-in-loop"])


@gate_router.post("/confirm", response_model=GateActionResponse)
def confirm_recommendation(payload: ConfirmPayload) -> GateActionResponse:
    _ = payload
    return GateActionResponse(status="confirmed", timestamp=datetime.now(timezone.utc))


@gate_router.post("/override", response_model=GateActionResponse)
def override_recommendation(payload: OverridePayload) -> GateActionResponse:
    _ = payload
    return GateActionResponse(status="overridden", timestamp=datetime.now(timezone.utc))

