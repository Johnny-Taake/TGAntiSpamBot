"""
OpenAI Chat Completions Adapter
"""

from typing import Any, Dict, Optional

from ai_client.models import RequestParts


class OpenAIChatCompletionsAdapter:
    """
    OpenAI-compatible /v1/chat/completions adapter.
    """

    def build(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        user_text: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> RequestParts:
        base = self._normalize_url(base_url)

        # allow passing either ".../v1/chat/completions" or just host
        if base.endswith("/v1/chat/completions"):
            url = base
        elif base.endswith("/v1"):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": user_text}],
        }
        if extra:
            payload.update(extra)

        return RequestParts(url=url, headers=headers, payload=payload)

    def parse(self, data: Dict[str, Any]) -> str:
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception as e:
            from ai_client.models import AIResponseFormatError

            raise AIResponseFormatError(
                "Invalid OpenAI /chat/completions response shape"
            ) from e

        if not isinstance(text, str) or not text.strip():
            from ai_client.models import AIResponseFormatError

            raise AIResponseFormatError("Empty model output")

        return text

    def _normalize_url(self, base_url: str) -> str:
        return (base_url or "").strip().rstrip("/")
