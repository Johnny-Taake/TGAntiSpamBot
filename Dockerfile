FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN uv sync --all-groups

ENV PATH="/app/.venv/bin:$PATH"

COPY . /app

CMD ["uv", "run", "main.py"]
