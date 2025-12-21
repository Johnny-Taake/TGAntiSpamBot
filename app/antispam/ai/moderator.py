from typing import Optional

from app.antispam.dto import MessageTask
from config import config
from logger import get_logger
from prompts import build_moderation_prompt

log = get_logger(__name__)


class AIModerator:
    """
    Handles AI-based spam moderation logic.
    """

    def __init__(self, ai_service=None):
        self.ai_service = ai_service

    @staticmethod
    def _build_moderation_prompt(task: MessageTask) -> Optional[str]:
        """
        Build moderation prompt for AI with message from task.
        """
        raw_msg = task.text or ""
        from app.antispam.detectors.text_normalizer import normalize_text

        msg = normalize_text(raw_msg).strip()
        if msg == "":
            log.info(
                "Message contains no text - skipping AI moderation: chat_id=%s msg_id=%s",
                task.telegram_chat_id,
                task.telegram_message_id,
            )
            return None
        return build_moderation_prompt(msg)

    async def get_score(self, task: MessageTask) -> Optional[float]:
        """
        Process message using AI scoring.

        Args:
            task: Message task to analyze

        Returns:
            AI score (0.0-1.0) or None if unable to parse
        """
        from ..scoring.ai_scorer import AIScorer

        ai_prompt = self._build_moderation_prompt(task)

        if ai_prompt is None:
            return None  # Not counting as empty message in prompt given

        ai_scorer = AIScorer(self.ai_service)

        ai_response = await ai_scorer.get_score(ai_prompt, self.ai_service)
        log.debug(
            "AI output: chat_id=%s msg_id=%s",
            task.telegram_chat_id,
            task.telegram_message_id,
        )
        score = ai_scorer.extract_score(ai_response)

        if score is None:
            log.warning(
                "AI output not parseable; returning None. chat_id=%s msg_id=%s raw=%r",
                task.telegram_chat_id,
                task.telegram_message_id,
                str(ai_response)[:200] if ai_response else "None",
            )
            return None

        return score

    def is_spam(self, score: Optional[float]) -> bool:
        """
        Determine if a message is spam based on the AI score.

        Args:
            score: AI score (0.0-1.0) or None

        Returns:
            True if message is spam, False otherwise
        """
        if score is None:
            log.debug("Treating message as spam: AI score is None (empty text or parse error)")
            return False  # Treat as not spam - not enough info to determine

        threshold = config.ai.spam_threshold
        is_spam_result = score >= threshold
        log.debug("AI moderation result: score=%.3f, threshold=%.3f, is_spam=%s", score, threshold, is_spam_result)
        return is_spam_result
