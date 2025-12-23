from dataclasses import dataclass
from typing import Optional

from app.antispam.scoring import AIScorer
from app.antispam.dto import MessageTask
from config import config
from logger import get_logger
from prompts import PROMPTS

log = get_logger(__name__)


@dataclass(frozen=True)
class ModerationHit:
    """
    Represents a successful spam detection by the AI moderator.

    Attributes:
        prompt_index: The index of the prompt that detected the spam
        score: The numerical score (0.0-1.0) that exceeded the threshold
    """
    prompt_index: int
    score: float


class AIModerator:
    """
    Handles AI-based spam moderation logic.
    """

    def __init__(self, ai_service=None):
        self.ai_service = ai_service

    @staticmethod
    def _normalize_task_text(task: MessageTask) -> Optional[str]:
        raw_msg = task.text or ""
        from app.antispam.detectors.text_normalizer import normalize_text

        msg = normalize_text(raw_msg).strip()
        if not msg:
            log.info(
                "Message contains no text - skipping AI moderation: chat_id=%s msg_id=%s",
                task.telegram_chat_id,
                task.telegram_message_id,
            )
            return None
        return msg

    async def first_score_over_threshold(
        self, task: MessageTask
    ) -> Optional[ModerationHit]:
        """
        Run prompts sequentially. If ANY score >= threshold ->
        return hit immediately. If message has no text ->
        return None (treat as not spam by AI).
        """
        msg = self._normalize_task_text(task)
        if msg is None:
            return None

        threshold = config.ai.spam_threshold

        ai_scorer = AIScorer(self.ai_service)

        for i in range(len(PROMPTS)):
            ai_prompt = PROMPTS.build_moderation_prompt(msg, i)

            ai_response = await ai_scorer.get_score(ai_prompt, self.ai_service)
            score = ai_scorer.extract_score(ai_response)

            if score is None:
                log.warning(
                    "AI output not parseable; continue next prompt. chat_id=%s msg_id=%s prompt=%s raw=%r",
                    task.telegram_chat_id,
                    task.telegram_message_id,
                    i,
                    str(ai_response)[:200] if ai_response else "None",
                )
                continue

            log.debug(
                "AI score: chat_id=%s msg_id=%s prompt=%s score=%.3f threshold=%.3f",
                task.telegram_chat_id,
                task.telegram_message_id,
                i,
                score,
                threshold,
            )

            if score >= threshold:
                return ModerationHit(prompt_index=i, score=score)

        return None
