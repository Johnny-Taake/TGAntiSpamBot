__all__ = [
    "router",
]


from .callbacks import router as callbacks_router  # noqa: E402
from .handlers import router as handlers_router  # noqa: E402

router = callbacks_router

router.include_router(handlers_router)
