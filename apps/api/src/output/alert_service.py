from __future__ import annotations

import asyncio
from pydantic import BaseModel
from typing import Literal

from reasoning.reasoning_orchestrator import ClinicalRecommendation
from safety.human_in_loop import GatedRecommendation
from shared.llm_client import llm_complete


class AlertSeverity(BaseModel):
    level: Literal["info", "warning", "critical"]
    colour_code: str


def summarise_recommendation(rec: ClinicalRecommendation) -> str:
    response = asyncio.run(
        llm_complete(
            system_prompt=(
                "You are a clinical communication assistant. Summarise the recommendation "
                "in 3 plain-English sentences for a busy clinician. Be concise and specific."
            ),
            user_prompt=f"Recommendation:\n{rec.model_dump_json(indent=2)}",
            temperature=0.3,
            max_tokens=200,
        )
    )
    return response.content


def rank_alert(gated: GatedRecommendation) -> AlertSeverity:
    if gated.escalation_level == "critical":
        return AlertSeverity(level="critical", colour_code="#dc2626")
    if gated.escalation_level == "urgent":
        return AlertSeverity(level="warning", colour_code="#f59e0b")
    return AlertSeverity(level="info", colour_code="#2563eb")


def send_notification(alert: AlertSeverity, summary: str, clinician_id: str) -> bool:
    print(
        f"[alert] clinician_id={clinician_id} level={alert.level} color={alert.colour_code} summary={summary}"
    )
    return True

