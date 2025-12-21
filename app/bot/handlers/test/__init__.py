__all__ = [
    "router",
]

from aiogram import Router


router = Router()

from .test_ai import router as test_ai_router  # noqa: E402
router.include_router(test_ai_router)
