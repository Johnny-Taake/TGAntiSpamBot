import asyncio
from collections import OrderedDict
from typing import Final


_SENTINEL: Final = object()


class TTLSet:
    """
    Small in-memory TTL set to deduplicate tasks by (chat_id, message_id).
    Prevents duplicated processing if the same message gets enqueued twice.
    """

    def __init__(self, ttl_s: int = 300, max_size: int = 2000):
        self.ttl_s = ttl_s
        self.max_size = max_size
        self._data: OrderedDict[object, float] = OrderedDict()

    def add_if_new(self, key: object) -> bool:
        now = asyncio.get_running_loop().time()
        self._evict(now)
        if key in self._data:
            return False
        self._data[key] = now
        return True

    def _evict(self, now: float) -> None:
        ttl = self.ttl_s

        while self._data:
            _, ts = next(iter(self._data.items()))
            if now - ts < ttl:
                break
            self._data.popitem(last=False)

        while len(self._data) > self.max_size:
            self._data.popitem(last=False)


def get_sentinel():
    """Get the sentinel object used for graceful shutdown."""
    return _SENTINEL
