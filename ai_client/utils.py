def is_running_inside_docker() -> bool:
    """Check if the application is running inside a Docker container."""
    try:
        with open("/.dockerenv", "rb"):
            return True
    except Exception:
        return False


def looks_like_ollama(base_url: str) -> bool:
    """Check if the base URL appears to point to an Ollama service."""
    s = (base_url or "").lower()
    return (
        ("11434" in s)
        or ("ollama" in s)
        or ("/api/chat" in s)
        or ("/api/generate" in s)
    )
