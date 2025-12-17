__all__ = [
    "router",
]

from aiogram import Router


router = Router()

from .dice import router as dice_router  # noqa: E402
router.include_router(dice_router)

from .slot import router as slot_router  # noqa: E402
router.include_router(slot_router)
