from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    session_id: UUID
    patient_id: UUID
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    last_active: datetime


class ChatRequest(BaseModel):
    patient_id: UUID
    session_id: UUID | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: UUID
    reply: str
    urgency_level: Literal["normal", "watch", "urgent", "emergency"]
    urgency_reason: str | None
    suggested_actions: list[str]
    disclaimer: str = "This is an AI assistant. Always consult your doctor for medical decisions."


class UrgencyFlag(BaseModel):
    level: Literal["normal", "watch", "urgent", "emergency"]
    reason: str
    notify_clinician: bool

