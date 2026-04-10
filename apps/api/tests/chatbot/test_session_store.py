from __future__ import annotations

import asyncio
from typing import Set
from uuid import uuid4

from _pytest.monkeypatch import MonkeyPatch
from chatbot.chat_models import ChatMessage
from chatbot import session_store


class FakeRedis:
    def __init__(self) -> None:
        self.kv: dict[str, str] = {}
        self.sets: dict[str, set[str]] = {}

    async def ping(self) -> bool:
        return True

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        _ = ex
        self.kv[key] = value

    async def get(self, key: str) -> str | None:
        return self.kv.get(key)

    async def sadd(self, key: str, value: str) -> None:
        self.sets.setdefault(key, set()).add(value)

    async def smembers(self, key: str) -> Set[str]:
        return self.sets.get(key, set())

    async def expire(self, key: str, ex: int) -> None:
        _ = (key, ex)

    async def srem(self, key: str, value: str) -> None:
        self.sets.setdefault(key, set()).discard(value)

    async def delete(self, key: str) -> None:
        self.kv.pop(key, None)


def test_session_store_roundtrip(monkeypatch: MonkeyPatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(session_store, "_fallback", False)
    monkeypatch.setattr(session_store, "_redis_client", fake)
    patient_id = uuid4()
    session = asyncio.run(session_store.create_session(patient_id))
    updated = asyncio.run(
        session_store.append_message(session.session_id, ChatMessage(role="user", content="hello"))
    )
    assert len(updated.messages) == 1
    fetched = asyncio.run(session_store.get_session(session.session_id))
    assert fetched is not None
    assert fetched.messages[0].content == "hello"

