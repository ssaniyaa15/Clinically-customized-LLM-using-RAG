from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from chatbot.chat_models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

_memory_store: dict[str, str] = {}
_memory_patient_sessions: dict[str, set[str]] = {}
_fallback = False
_redis_client: Any = None

try:
    import redis.asyncio as redis_async_module
    redis_async: Any = redis_async_module
except Exception:  # pragma: no cover
    redis_async = None

TTL_SECONDS = int(timedelta(hours=24).total_seconds())


async def _get_client() -> Any:
    global _fallback, _redis_client
    if _fallback or redis_async is None:
        return None
    if _redis_client is None:
        try:
            _redis_client = redis_async.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
            await _redis_client.ping()
        except Exception:
            _fallback = True
            logger.warning("Redis unavailable; falling back to in-memory chat session store.")
            return None
    return _redis_client


def _session_key(session_id: UUID) -> str:
    return f"chat:session:{session_id}"


def _patient_sessions_key(patient_id: UUID) -> str:
    return f"chat:patient:{patient_id}:sessions"


async def save_session(session: ChatSession) -> None:
    payload = session.model_dump_json()
    client = await _get_client()
    if client is None:
        _memory_store[str(session.session_id)] = payload
        _memory_patient_sessions.setdefault(str(session.patient_id), set()).add(str(session.session_id))
        return
    await client.set(_session_key(session.session_id), payload, ex=TTL_SECONDS)
    await client.sadd(_patient_sessions_key(session.patient_id), str(session.session_id))
    await client.expire(_patient_sessions_key(session.patient_id), TTL_SECONDS)


async def get_session(session_id: UUID) -> ChatSession | None:
    client = await _get_client()
    raw = None
    if client is None:
        raw = _memory_store.get(str(session_id))
    else:
        raw = await client.get(_session_key(session_id))
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return ChatSession.model_validate_json(raw)


async def create_session(patient_id: UUID) -> ChatSession:
    now = datetime.now(timezone.utc)
    session = ChatSession(session_id=uuid4(), patient_id=patient_id, created_at=now, last_active=now, messages=[])
    await save_session(session)
    return session


async def append_message(session_id: UUID, message: ChatMessage) -> ChatSession:
    session = await get_session(session_id)
    if session is None:
        raise KeyError("Session not found")
    session.messages.append(message)
    session.last_active = datetime.now(timezone.utc)
    await save_session(session)
    return session


async def clear_session(session_id: UUID) -> bool:
    session = await get_session(session_id)
    if session is None:
        return False
    client = await _get_client()
    if client is None:
        _memory_store.pop(str(session_id), None)
        ids = _memory_patient_sessions.get(str(session.patient_id), set())
        ids.discard(str(session_id))
        return True
    await client.delete(_session_key(session_id))
    await client.srem(_patient_sessions_key(session.patient_id), str(session_id))
    return True


async def list_sessions_for_patient(patient_id: UUID) -> list[ChatSession]:
    client = await _get_client()
    ids: list[str] = []
    if client is None:
        ids = list(_memory_patient_sessions.get(str(patient_id), set()))
    else:
        raw_ids = await client.smembers(_patient_sessions_key(patient_id))
        ids = [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in raw_ids]
    out: list[ChatSession] = []
    for sid in ids:
        try:
            session = await get_session(UUID(sid))
        except Exception:
            session = None
        if session is not None:
            out.append(session)
    out.sort(key=lambda x: x.last_active, reverse=True)
    return out

