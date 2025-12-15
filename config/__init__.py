__all__ = ["config"]


from .settings import settings

config = settings.get_config()
