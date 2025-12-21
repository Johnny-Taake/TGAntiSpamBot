from typing import Any
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.bot.filters import PrivateChatFilter, MainAdminFilter
from ai_client.service import AIService
from logger import get_logger
from prompts import build_moderation_prompt

log = get_logger(__name__)

router = Router()


class TestAIStates(StatesGroup):
    waiting_for_message = State()


@router.message(Command("test_ai"), PrivateChatFilter(), MainAdminFilter())
async def test_ai(message: types.Message, state: FSMContext, **kwargs: Any):
    await message.answer(
        "Test AI. Please enter the message you want to review for scum/fraud/inappropriate "
        "content, you will get a response from 0 to 1 where 0 is clean and 1 is a possible "
        "unwanted content:"
    )
    await state.set_state(TestAIStates.waiting_for_message)


@router.message(TestAIStates.waiting_for_message, F.text)
async def process_test_message(
    message: types.Message, state: FSMContext, **kwargs: Any
):
    ai = AIService()
    try:
        from config import config
        text = await ai.one_shot(build_moderation_prompt(message.text), extra={"temperature": config.ai.temperature})
        log.debug("Input: %s", message.text)
        log.info("Result: %s", text)
        await message.answer(text)
    except Exception as e:
        log.error("AI processing error: %s", e)
        await message.answer("Error processing message. Please try again.")
    finally:
        await ai.close()
        await state.clear()
