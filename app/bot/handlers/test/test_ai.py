from typing import Any

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.antispam import MessageTask
from app.antispam.ai import AIModerator
from app.bot.filters import PrivateChatFilter, MainAdminFilter
from logger import get_logger

log = get_logger(__name__)

router = Router()


class TestAIStates(StatesGroup):
    waiting_for_message = State()


@router.message(Command("test_ai"), PrivateChatFilter(), MainAdminFilter())
async def test_ai(message: types.Message, state: FSMContext, **kwargs: Any):
    from app.container import get_container
    from config import config

    # Check if global AI is enabled
    if not config.bot.ai_enabled:
        await message.answer("❌ AI testing is disabled. APP_AI_ENABLED is set to False.")  # noqa: E501
        return

    container = get_container()
    if container.ai_service is None:
        await message.answer("❌ AI service is not configured. Please check your AI configuration.")  # noqa: E501
        return

    await message.answer(
        "Test AI. Please enter the message you want to review for scam/fraud/inappropriate "  # noqa: E501
        "content, you will get a response from 0 to 1 where 0 is clean and 1 is a possible "  # noqa: E501
        "unwanted content:"
    )
    await state.set_state(TestAIStates.waiting_for_message)


@router.message(TestAIStates.waiting_for_message, F.text)
async def process_test_message(
    message: types.Message, state: FSMContext, **kwargs: Any
):
    from app.container import get_container
    from config import config

    # Check if global AI is enabled
    if not config.bot.ai_enabled:
        await message.answer("❌ AI testing is disabled. APP_AI_ENABLED is set to False.")  # noqa: E501
        await state.clear()
        return

    container = get_container()
    if container.ai_service is None:
        await message.answer("❌ AI service is not configured. Please check your AI configuration.")  # noqa: E501
        await state.clear()
        return

    try:
        moderator = AIModerator(ai_service=container.ai_service)

        task = MessageTask(
            telegram_chat_id=message.chat.id,
            telegram_message_id=message.message_id,
            text=message.text,
            telegram_user_id=message.from_user.id,
        )

        hit = await moderator.first_score_over_threshold(task)

        if hit:
            await message.answer(
                f"Hit: score={hit.score:} (>= {config.ai.spam_threshold}) on prompt #{hit.prompt_index}"  # noqa: E501
            )
        else:
            await message.answer(f"No hits. All prompts < {config.ai.spam_threshold}")  # noqa: E501

    except Exception as e:
        log.error("AI processing error: %s", e)
        await message.answer("Error processing message. Please try again.")
    finally:
        await state.clear()
