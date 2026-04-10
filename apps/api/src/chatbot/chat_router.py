from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from chatbot.chat_models import ChatRequest, ChatResponse, ChatSession
from chatbot.chat_service import handle_message
from chatbot.session_store import clear_session, get_session, list_sessions_for_patient

router = APIRouter(prefix="/chat", tags=["chatbot"])


@router.post("/message", response_model=ChatResponse)
async def post_message(payload: ChatRequest) -> ChatResponse:
    return await handle_message(payload)


@router.get("/session/{session_id}", response_model=ChatSession)
async def get_session_history(session_id: UUID) -> ChatSession:
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/session/{session_id}")
async def delete_session(session_id: UUID) -> dict[str, bool]:
    ok = await clear_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@router.get("/sessions/{patient_id}", response_model=list[ChatSession])
async def list_patient_sessions(patient_id: UUID) -> list[ChatSession]:
    return await list_sessions_for_patient(patient_id)

