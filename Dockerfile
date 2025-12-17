FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ADD pyproject.toml uv.lock ./
RUN uv sync
ENV PATH="/app/.venv/bin:$PATH"

COPY . /app

CMD ["uv", "run", "main.py"]
