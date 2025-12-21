import asyncio
from typing import Any, Dict, Optional

import httpx

from config import config
from logger import get_logger

from .adapters import OpenAIChatCompletionsAdapter, OllamaChatAdapter
from .models import AIHTTPError, AIResponseFormatError
from .utils import looks_like_ollama

log = get_logger(__name__)


class AIService:
    """
    Single-request AI service. Provider inferred from base_url.

    - Ollama: base_url contains 11434 or ollama or /api/chat
    - Otherwise: OpenAI-compatible /v1/chat/completions
    """

    def __init__(self) -> None:
        log.info(
            "AI service config: %s",
            {
                "concurrency": config.ai.http.concurrency,
                "timeout_s": config.ai.http.timeout_s,
                "max_connections": config.ai.http.max_connections,
                "max_keepalive_connections": config.ai.http.max_keepalive_connections,
                "keepalive_expiry_s": config.ai.http.keepalive_expiry_s,
            },
        )

        self._sem = asyncio.Semaphore(config.ai.http.concurrency)

        limits = httpx.Limits(
            max_connections=config.ai.http.max_connections,
            max_keepalive_connections=config.ai.http.max_keepalive_connections,
            keepalive_expiry=config.ai.http.keepalive_expiry_s,
        )

        self._client = httpx.AsyncClient(
            timeout=config.ai.http.timeout_s, limits=limits
        )

        self._openai = OpenAIChatCompletionsAdapter()
        self._ollama = OllamaChatAdapter()

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self._client.aclose()

    async def one_shot(
        self, user_text: str, *, extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send a single request to the AI service and return the response."""
        base_url = config.ai.base_url
        model = config.ai.model
        api_key = config.ai.api_key

        if looks_like_ollama(base_url):
            req = self._ollama.build(
                base_url=base_url, model=model, user_text=user_text, extra=extra
            )
        else:
            req = self._openai.build(
                base_url=base_url,
                api_key=api_key,
                model=model,
                user_text=user_text,
                extra=extra,
            )

        async with self._sem:
            try:
                response = await self._client.post(
                    req.url, headers=req.headers, json=req.payload
                )
            except httpx.TimeoutException as e:
                raise AIHTTPError(f"Timeout after {config.ai.http.timeout_s}s") from e
            except httpx.HTTPError as e:
                raise AIHTTPError(f"HTTP error: {e!r}") from e

        if response.status_code >= 400:
            body = (response.text or "")[:2000]
            raise AIHTTPError(f"HTTP {response.status_code}: {body}")

        try:
            data = response.json()
        except Exception as e:
            raise AIResponseFormatError("Response is not valid JSON") from e

        if looks_like_ollama(base_url):
            return self._ollama.parse(data)
        return self._openai.parse(data)
