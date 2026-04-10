from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel


def get_llm_base_url() -> str:
    return os.environ.get("LLM_BASE_URL", "http://localhost:11434").rstrip("/")


LLM_MODEL: str = os.environ.get("LLM_MODEL", "llama3")
MAX_TOKENS: int = int(os.environ.get("LLM_MAX_TOKENS", "1024"))
TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE", "0.2"))


class LLMResponse(BaseModel):
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


async def llm_complete(
    system_prompt: str,
    user_prompt: str,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    json_mode: bool = False,
) -> LLMResponse:
    payload_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return await llm_complete_with_history(
        system_prompt="",
        messages=payload_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=json_mode,
    )


async def llm_complete_with_history(
    system_prompt: str,
    messages: list[dict[str, str]],
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    json_mode: bool = False,
) -> LLMResponse:
    payload_messages: list[dict[str, str]] = messages
    if system_prompt.strip():
        payload_messages = [{"role": "system", "content": system_prompt}] + messages
    url = f"{get_llm_base_url()}/api/chat"
    body: dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": payload_messages,
        "stream": False,
    }
    if json_mode:
        body["format"] = "json"
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError:
        return LLMResponse(
            content="Local AI model is not running. Please start Ollama.",
            model=LLM_MODEL,
            prompt_tokens=0,
            completion_tokens=0,
            finish_reason="error",
        )
    content = str(data.get("message", {}).get("content", ""))
    return LLMResponse(
        content=content,
        model=str(data.get("model", LLM_MODEL)),
        prompt_tokens=0,
        completion_tokens=0,
        finish_reason="stop",
    )

