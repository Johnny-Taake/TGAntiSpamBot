__all__ = [
    "router",
]

from aiogram import Router

from .callbacks import router as callbacks_router  # noqa: E402
from .handlers import router as handlers_router  # noqa: E402

router = Router()

router.include_router(handlers_router)
router.include_router(callbacks_router)
