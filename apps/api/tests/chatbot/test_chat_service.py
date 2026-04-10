from __future__ import annotations

from uuid import uuid4

import pytest
from _pytest.monkeypatch import MonkeyPatch
from typing import Any

from chatbot.chat_models import ChatRequest, ChatSession
from chatbot.chat_service import handle_message


@pytest.mark.asyncio
async def test_handle_message_routes_urgency(monkeypatch: MonkeyPatch) -> None:
    patient_id = uuid4()
    from datetime import datetime

    session = ChatSession(
        session_id=uuid4(),
        patient_id=patient_id,
        messages=[],
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
    )

    async def _get_or_create_session(request: ChatRequest) -> ChatSession:
        _ = request
        return session

    async def _build_patient_context(patient_id_v: Any, user_query: str) -> str:
        _ = (patient_id_v, user_query)
        return "ctx"

    async def _llm_complete_with_history(**kwargs: Any) -> object:
        _ = kwargs
        return type("Resp", (), {"content": "You may have chest pain; call emergency."})()

    async def _append_message(session_id: Any, message: Any) -> ChatSession:
        _ = (session_id, message)
        return session

    monkeypatch.setattr("chatbot.chat_service.get_or_create_session", _get_or_create_session)
    monkeypatch.setattr("chatbot.chat_service.build_patient_context", _build_patient_context)
    monkeypatch.setattr("chatbot.chat_service.llm_complete_with_history", _llm_complete_with_history)
    monkeypatch.setattr("chatbot.chat_service.append_message", _append_message)
    notified: dict[str, bool] = {"v": False}

    def _notify(*args: Any, **kwargs: Any) -> bool:
        notified["v"] = True
        return True

    monkeypatch.setattr("chatbot.chat_service.send_notification", _notify)
    out = await handle_message(ChatRequest(patient_id=patient_id, session_id=session.session_id, message="chest pain"))
    assert out.urgency_level == "emergency"
    assert notified["v"] is True
    assert "Call 112/911" in out.suggested_actions[0]


@pytest.mark.asyncio
async def test_handle_message_non_medical_query_is_blocked(monkeypatch: MonkeyPatch) -> None:
    patient_id = uuid4()
    from datetime import datetime

    session = ChatSession(
        session_id=uuid4(),
        patient_id=patient_id,
        messages=[],
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
    )

    async def _get_or_create_session(request: ChatRequest) -> ChatSession:
        _ = request
        return session

    async def _append_message(session_id: Any, message: Any) -> ChatSession:
        _ = (session_id, message)
        return session

    monkeypatch.setattr("chatbot.chat_service.get_or_create_session", _get_or_create_session)
    monkeypatch.setattr("chatbot.chat_service.append_message", _append_message)
    out = await handle_message(
        ChatRequest(patient_id=patient_id, session_id=session.session_id, message="what is the bitcoin price")
    )
    assert "I can only assist with health-related queries." in out.reply


@pytest.mark.asyncio
async def test_handle_message_requires_patient_context(monkeypatch: MonkeyPatch) -> None:
    patient_id = uuid4()
    from datetime import datetime

    session = ChatSession(
        session_id=uuid4(),
        patient_id=patient_id,
        messages=[],
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
    )

    async def _get_or_create_session(request: ChatRequest) -> ChatSession:
        _ = request
        return session

    async def _build_patient_context(patient_id_v: Any, user_query: str) -> str:
        _ = (patient_id_v, user_query)
        return ""

    async def _append_message(session_id: Any, message: Any) -> ChatSession:
        _ = (session_id, message)
        return session

    monkeypatch.setattr("chatbot.chat_service.get_or_create_session", _get_or_create_session)
    monkeypatch.setattr("chatbot.chat_service.build_patient_context", _build_patient_context)
    monkeypatch.setattr("chatbot.chat_service.append_message", _append_message)
    out = await handle_message(ChatRequest(patient_id=patient_id, session_id=session.session_id, message="chest pain"))
    assert "No medical data available. Please upload records." in out.reply

