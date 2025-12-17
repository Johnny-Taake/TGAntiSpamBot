from app.db import Chat

PAGE_SIZE = 3


def paginate(chats: list[Chat], page: int) -> tuple[list[Chat], int]:
    total_pages = max(1, (len(chats) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    return chats[start:end], total_pages
