from __future__ import annotations

from chatbot.chat_models import UrgencyFlag

URGENCY_KEYWORDS = {
    "emergency": [
        "chest pain",
        "can't breathe",
        "difficulty breathing",
        "stroke",
        "unconscious",
        "seizure",
        "severe bleeding",
        "heart attack",
        "suicidal",
        "overdose",
    ],
    "urgent": [
        "high fever",
        "vomiting blood",
        "severe pain",
        "confusion",
        "fainting",
        "allergic reaction",
        "swelling throat",
        "vision loss",
    ],
    "watch": ["mild fever", "headache", "nausea", "dizziness", "rash", "cough", "sore throat"],
}


def detect_urgency(message: str, llm_reply: str) -> UrgencyFlag:
    text = f"{message}\n{llm_reply}".lower()
    for level in ("emergency", "urgent", "watch"):
        for kw in URGENCY_KEYWORDS[level]:
            if kw in text:
                return UrgencyFlag(
                    level=level, reason=f"Matched keyword: {kw}", notify_clinician=(level == "emergency")
                )
    return UrgencyFlag(level="normal", reason="No critical keywords found", notify_clinician=False)

