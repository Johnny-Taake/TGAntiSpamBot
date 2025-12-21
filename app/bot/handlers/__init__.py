__all__ = [
    "router",
]

from aiogram import Router

from config import config

router = Router()

from .start import router as start_router  # noqa: E402

router.include_router(start_router)

from .about import router as about_router  # noqa: E402

router.include_router(about_router)

if config.bot.fun_commands_enabled:
    from .fun import router as fun_router  # noqa: E402

    router.include_router(fun_router)

from .admin import router as admin_router  # noqa: E402

router.include_router(admin_router)

from .test import router as test_router  # noqa: E402

router.include_router(test_router)

from .antispam import router as anti_spam_router  # noqa: E402

router.include_router(anti_spam_router)
