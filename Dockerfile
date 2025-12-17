FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ADD pyproject.toml uv.lock ./

# NOTE: polling mode
RUN uv sync

# NOTE: webhook mode
# RUN uv sync --frozen --no-dev --group webhook

ENV PATH="/app/.venv/bin:$PATH"

COPY . /app

# NOTE: polling mode
CMD ["uv", "run", "main.py"]

# NOTE: webhook mode
# EXPOSE 8000
# CMD ["uv", "run", "--group", "webhook", "python", "-m", "bot"]
