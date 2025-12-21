"""
Ollama Chat Adapter
"""

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from ai_client.models import RequestParts


class OllamaChatAdapter:
    """
    Ollama /api/chat adapter (non-stream).
    """

    def build(
        self,
        *,
        base_url: str,
        model: str,
        user_text: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> RequestParts:
        base = self._normalize_url(base_url)

        # accept both "http://host:11434" and ".../api/chat"
        if base.endswith("/api/chat"):
            url = base
        else:
            url = f"{base}/api/chat"

        url = self._fix_localhost_for_docker(url)

        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": user_text}],
            "stream": False,
            # NOTE: If 5 min no request, Ollama will shut down the model and
            #   free resources - next request will take 2-5 seconds to start the model
            "keep_alive": "5m",
        }
        if extra:
            payload.update(extra)

        return RequestParts(url=url, headers=headers, payload=payload)

    def parse(self, data: Dict[str, Any]) -> str:
        try:
            text = data["message"]["content"]
        except Exception as e:
            from ai_client.models import AIResponseFormatError

            raise AIResponseFormatError(
                "Invalid Ollama /api/chat response shape"
            ) from e

        if not isinstance(text, str) or not text.strip():
            from ai_client.models import AIResponseFormatError

            raise AIResponseFormatError("Empty model output")

        return text

    def _normalize_url(self, base_url: str) -> str:
        return (base_url or "").strip().rstrip("/")

    def _is_running_inside_docker(self) -> bool:
        try:
            with open("/.dockerenv", "rb"):
                return True
        except Exception:
            return False

    def _fix_localhost_for_docker(self, url: str) -> str:
        """
        If app runs in docker and base_url uses localhost -> point to compose service 'ollama'.
        """
        if not self._is_running_inside_docker():
            return url

        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if host in ("localhost", "127.0.0.1"):
            scheme = parsed.scheme or "http"
            port = parsed.port or 11434
            path = parsed.path or ""
            query = f"?{parsed.query}" if parsed.query else ""
            return f"{scheme}://ollama:{port}{path}{query}"
        return url
