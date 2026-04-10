from __future__ import annotations

import os
from hashlib import sha256

from chatbot.chat_models import ChatMessage, ChatRequest, ChatResponse, ChatSession
from chatbot.context_builder import build_patient_context
from chatbot.session_store import append_message, create_session, get_session
from chatbot.urgency_detector import detect_urgency
from output.alert_service import AlertSeverity, send_notification
from shared.llm_client import llm_complete_with_history

try:
    import redis as redis_module
except Exception:  # pragma: no cover
    redis_module = None

DISCLAIMER = "This guidance is informational only and does not replace care from a licensed doctor."
NON_MEDICAL_REPLY = "I can only assist with health-related queries."
SAFETY_FALLBACK_REPLY = "I'm designed only for medical assistance."
NO_DATA_REPLY = "No medical data available. Please upload records."


async def get_or_create_session(request: ChatRequest) -> ChatSession:
    if request.session_id is not None:
        existing = await get_session(request.session_id)
        if existing is not None:
            return existing
    return await create_session(request.patient_id)


def _suggested_actions(level: str) -> list[str]:
    if level == "emergency":
        return ["Call 112/911 immediately", "Do not wait"]
    if level == "urgent":
        return ["Visit nearest clinic today", "Contact your doctor"]
    if level == "watch":
        return ["Monitor symptoms", "Rest and hydrate", "Call if worsens"]
    return ["Follow your prescription", "Schedule a routine checkup"]


def _redis_cache_client():
    if redis_module is None:
        return None
    try:
        return redis_module.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    except Exception:
        return None


def _cache_key(patient_id: str, query: str) -> str:
    digest = sha256(f"{patient_id}:{query.strip().lower()}".encode("utf-8")).hexdigest()
    return f"chat:answer:{digest}"


def _is_medical_query(text: str) -> bool:
    t = text.lower()
    medical_terms = (
        "pain",
        "symptom",
        "fever",
        "cough",
        "blood",
        "medicine",
        "medication",
        "dose",
        "diagnosis",
        "treatment",
        "doctor",
        "clinic",
        "hospital",
        "allergy",
        "prescription",
        "health",
    )
    return any(token in t for token in medical_terms)


def _contains_non_medical_content(text: str) -> bool:
    t = text.lower()
    blocked_terms = (
        "crypto",
        "bitcoin",
        "stock",
        "investment",
        "dating",
        "politics",
        "movie",
        "travel",
        "gaming",
        "programming",
    )
    return any(token in t for token in blocked_terms)


def _ensure_disclaimer(reply: str) -> str:
    if "doctor" in reply.lower() or "does not replace" in reply.lower():
        return reply
    return f"{reply}\n\n{DISCLAIMER}"


async def handle_message(request: ChatRequest) -> ChatResponse:
    session = await get_or_create_session(request)
    if not _is_medical_query(request.message):
        reply = _ensure_disclaimer(NON_MEDICAL_REPLY)
        await append_message(session.session_id, ChatMessage(role="user", content=request.message))
        await append_message(session.session_id, ChatMessage(role="assistant", content=reply))
        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            urgency_level="routine",
            urgency_reason="Non-medical request",
            suggested_actions=_suggested_actions("routine"),
        )

    cache = _redis_cache_client()
    key = _cache_key(str(request.patient_id), request.message)
    if cache is not None:
        try:
            cached_reply = cache.get(key)
        except Exception:
            cached_reply = None
        if cached_reply:
            reply = _ensure_disclaimer(cached_reply)
            await append_message(session.session_id, ChatMessage(role="user", content=request.message))
            await append_message(session.session_id, ChatMessage(role="assistant", content=reply))
            urgency = detect_urgency(request.message, reply)
            return ChatResponse(
                session_id=session.session_id,
                reply=reply,
                urgency_level=urgency.level,
                urgency_reason=urgency.reason,
                suggested_actions=_suggested_actions(urgency.level),
            )

    patient_context = await build_patient_context(request.patient_id, request.message)
    if not patient_context.strip():
        reply = _ensure_disclaimer(NO_DATA_REPLY)
        await append_message(session.session_id, ChatMessage(role="user", content=request.message))
        await append_message(session.session_id, ChatMessage(role="assistant", content=reply))
        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            urgency_level="routine",
            urgency_reason="Missing patient context",
            suggested_actions=_suggested_actions("routine"),
        )

    history = session.messages[-10:]
    system_prompt = f"""
You are a clinical AI assistant. You MUST:
* Only answer healthcare-related questions.
* Use ONLY the provided patient medical context.
* If the question is not medical, respond exactly: "I can only assist with health-related queries."
* Never hallucinate facts not present in patient data.
* Never provide a definitive diagnosis.
* Always recommend consulting a doctor.
* Use a calm, nurse-like, reassuring tone and avoid technical jargon.
* If answer is not found in context, say you do not have enough information.

PATIENT MEDICAL CONTEXT:
{patient_context}
"""
    messages_payload = [{"role": m.role, "content": m.content} for m in history] + [
        {"role": "user", "content": request.message}
    ]
    llm_response = await llm_complete_with_history(
        system_prompt=system_prompt, messages=messages_payload, temperature=0.2, max_tokens=350
    )
    reply = llm_response.content.strip()
    if _contains_non_medical_content(reply):
        reply = SAFETY_FALLBACK_REPLY
    reply = _ensure_disclaimer(reply)
    if cache is not None:
        try:
            cache.setex(key, int(os.getenv("CHAT_CACHE_TTL_SECONDS", "300")), reply)
        except Exception:
            pass
    urgency = detect_urgency(request.message, reply)
    if urgency.notify_clinician:
        _ = send_notification(
            AlertSeverity(level="critical", colour_code="#dc2626"),
            summary=f"Patient chatbot emergency flag: {urgency.reason}",
            clinician_id=str(request.patient_id),
        )
    await append_message(session.session_id, ChatMessage(role="user", content=request.message))
    await append_message(session.session_id, ChatMessage(role="assistant", content=reply))
    return ChatResponse(
        session_id=session.session_id,
        reply=reply,
        urgency_level=urgency.level,
        urgency_reason=urgency.reason,
        suggested_actions=_suggested_actions(urgency.level),
    )

