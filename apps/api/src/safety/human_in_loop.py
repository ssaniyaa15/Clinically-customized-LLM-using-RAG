from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from reasoning.reasoning_orchestrator import ClinicalRecommendation
from shared.llm_client import llm_complete


class GatedRecommendation(BaseModel):
    recommendation: ClinicalRecommendation
    requires_confirmation: bool = True
    escalation_level: Literal["routine", "urgent", "critical"]
    override_allowed: bool = True
    safety_warning: str | None = None
    escalation_message: str = ""


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


async def generate_escalation_message(gated: GatedRecommendation) -> str:
    top_diagnosis = (
        gated.recommendation.ddx.diagnoses[0].name
        if gated.recommendation.ddx.diagnoses
        else "unknown"
    )
    risk_tier = gated.recommendation.risk.readmission.risk_tier
    response = await llm_complete(
        system_prompt=(
            "You are a clinical safety assistant. Write a brief, urgent escalation message "
            "for the clinician based on the recommendation and escalation level."
        ),
        user_prompt=(
            f"Escalation level: {gated.escalation_level}\n"
            f"Top diagnosis: {top_diagnosis}\n"
            f"Uncertainty score: {gated.recommendation.uncertainty_score}\n"
            f"Risk tier: {risk_tier}"
        ),
        temperature=0.2,
        max_tokens=150,
    )
    return response.content


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
    gated = GatedRecommendation(recommendation=rec, escalation_level=escalation)
    try:
        gated.escalation_message = asyncio.run(generate_escalation_message(gated))
    except Exception:
        gated.escalation_message = ""
    return gated


gate_router = APIRouter(prefix="/gate", tags=["human-in-loop"])


@gate_router.post("/confirm", response_model=GateActionResponse)
def confirm_recommendation(payload: ConfirmPayload) -> GateActionResponse:
    _ = payload
    return GateActionResponse(status="confirmed", timestamp=datetime.now(timezone.utc))


@gate_router.post("/override", response_model=GateActionResponse)
def override_recommendation(payload: OverridePayload) -> GateActionResponse:
    _ = payload
    return GateActionResponse(status="overridden", timestamp=datetime.now(timezone.utc))

