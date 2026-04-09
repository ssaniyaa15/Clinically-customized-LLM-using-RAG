from __future__ import annotations

import os
from pydantic import BaseModel
from typing import Literal, Any

import openai as openai_module

from reasoning.reasoning_orchestrator import ClinicalRecommendation
from safety.human_in_loop import GatedRecommendation


class AlertSeverity(BaseModel):
    level: Literal["info", "warning", "critical"]
    colour_code: str


def summarise_recommendation(rec: ClinicalRecommendation) -> str:
    llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:8001/v1")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_api_key = os.getenv("LLM_API_KEY", "dummy")
    prompt = (
        "Summarise this clinical recommendation in plain English, max 3 sentences:\n"
        f"{rec.model_dump_json()}"
    )
    try:
        client = openai_module.OpenAI(base_url=llm_base_url, api_key=llm_api_key)
        resp = client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = str(resp.choices[0].message.content or "").strip()
    except Exception:
        top = rec.ddx.diagnoses[0] if rec.ddx.diagnoses else None
        text = (
            f"Top diagnosis is {top.name} with confidence {top.confidence:.2f}. "
            f"Readmission risk is {rec.risk.readmission.risk_tier}. "
            f"Please review and confirm treatment plan."
            if top
            else "No diagnosis found. Please review the recommendation details."
        )
    # Hard cap to roughly 3 sentences if model over-produces.
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    return ". ".join(sentences[:3]) + ("." if sentences else "")


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

