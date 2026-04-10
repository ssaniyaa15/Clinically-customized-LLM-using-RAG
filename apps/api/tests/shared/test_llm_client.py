from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from shared.llm_client import LLMResponse, get_llm_base_url, llm_complete


@pytest.mark.asyncio
async def test_llm_complete_returns_typed_response() -> None:
    response_mock = AsyncMock()
    response_mock.json.return_value = {"model": "llama3", "message": {"content": "clinical answer"}}
    response_mock.raise_for_status.return_value = None
    post_mock = AsyncMock(return_value=response_mock)
    with patch("shared.llm_client.httpx.AsyncClient.post", post_mock):
        out = await llm_complete(system_prompt="sys", user_prompt="usr")
    assert isinstance(out, LLMResponse)
    assert out.content == "clinical answer"
    assert out.model == "llama3"
    assert out.prompt_tokens == 0
    assert out.completion_tokens == 0
    assert out.finish_reason == "stop"


@pytest.mark.asyncio
async def test_llm_complete_json_mode_adds_format() -> None:
    response_mock = AsyncMock()
    response_mock.json.return_value = {"model": "llama3", "message": {"content": "{}"}}
    response_mock.raise_for_status.return_value = None
    post_mock = AsyncMock(return_value=response_mock)
    with patch("shared.llm_client.httpx.AsyncClient.post", post_mock):
        await llm_complete(system_prompt="sys", user_prompt="usr", json_mode=True)
    assert post_mock.await_args is not None
    payload = post_mock.await_args.kwargs["json"]
    assert payload.get("format") == "json"


def test_get_llm_base_url_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    assert get_llm_base_url() == "http://localhost:11434"


@pytest.mark.asyncio
async def test_llm_complete_handles_ollama_connection_error() -> None:
    post_mock = AsyncMock(side_effect=httpx.ConnectError("down"))
    with patch("shared.llm_client.httpx.AsyncClient.post", post_mock):
        out = await llm_complete(system_prompt="sys", user_prompt="usr")
    assert out.finish_reason == "error"
    assert out.content == "Local AI model is not running. Please start Ollama."

