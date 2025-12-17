__all__ = [
    "router",
]

from aiogram import Router


router = Router()

from .start import router as start_router  # noqa: E402
router.include_router(start_router)

from .about import router as about_router  # noqa: E402
router.include_router(about_router)

from .fun import router as fun_router  # noqa: E402
router.include_router(fun_router)

from .admin import router as admin_router  # noqa: E402
router.include_router(admin_router)

from .antispam import router as anti_spam_router  # noqa: E402
router.include_router(anti_spam_router)
