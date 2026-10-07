"""Chat completion behind one interface. Empty key → no client."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system_v1.txt"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


class LlmError(Exception):
    pass


class LlmClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class OpenAICompatibleChat:
    def __init__(self, *, base_url: str, api_key: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model

    def complete(self, system: str, user: str) -> str:
        import httpx

        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=20.0,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as exc:
            raise LlmError("llm request failed") from exc
        except ValueError as exc:
            raise LlmError("llm returned non-json") from exc
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError("llm returned an unexpected body") from exc
        if not isinstance(content, str) or content.strip() == "":
            raise LlmError("llm returned an empty answer")
        return content.strip()


def load_llm(base_url: str | None, api_key: str | None, model: str) -> LlmClient | None:
    if not base_url or not api_key:
        return None
    logger.info("assistant llm configured model=%s", model)
    return OpenAICompatibleChat(base_url=base_url, api_key=api_key, model=model)
