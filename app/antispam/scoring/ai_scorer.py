import re
from typing import Optional

from ai_client.service import AIService
from logger import get_logger
from config import config

log = get_logger(__name__)


class AIScorer:
    """
    Handles AI-based scoring of messages for spam detection.
    """

    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service: Optional[AIService] = ai_service

    async def get_score(
        self, prompt: str, ai_service: Optional[AIService] = None
    ) -> str:
        """
        Get AI score for a message.

        Args:
            prompt: The prompt to send to the AI
            ai_service: The AI service instance to use

        Returns:
            The AI's response as a string
        """
        service = ai_service or self.ai_service
        if service is None:
            log.warning("( ! ) AI service not configured - AI check will always pass with score 0.0 ( ! )")  # noqa: E501
            return "0.0"

        from config import config

        response = await service.one_shot(
            prompt,
            extra={
                "temperature": config.ai.temperature,
            },
        )
        return response

    @staticmethod
    def extract_score(response: str) -> Optional[float]:
        """
        Extract a numeric score from AI output.
        Accept only values already in [0, 1].
        """
        s = (response or "").strip()

        try:
            fs = float(s)
        except ValueError:
            fs = None

        if fs is not None:
            if fs >= config.ai.spam_threshold:
                log.warning("AI response: %s (threshold: %s)", s, config.ai.spam_threshold)
            else:
                log.info("AI response: %s (threshold: %s)", s, config.ai.spam_threshold)
        else:
            log.warning("AI response (non-float raw): %r", s[:200])

        # Fast path
        try:
            v = float(s)
            if 0.0 <= v <= 1.0:
                return v
        except ValueError:
            pass

        # Fallback: pick first float token and validate range
        m = re.search(r"(-?\d+(?:\.\d+)?)", s)
        if not m:
            return None

        try:
            v = float(m.group(1))
        except ValueError:
            return None

        if 0.0 <= v <= 1.0:
            return v
        return None
