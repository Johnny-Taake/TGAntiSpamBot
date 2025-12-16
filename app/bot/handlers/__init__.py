__all__ = [
    "router",
]

from aiogram import Router


router = Router()

from .dice import router as dice_router  # noqa: E402
router.include_router(dice_router)

from .anti_spam import router as anti_spam_router  # noqa: E402
router.include_router(anti_spam_router)
