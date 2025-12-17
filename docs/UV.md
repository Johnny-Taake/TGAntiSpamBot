# UV Commands

## Installation

```sh
# Only basic dependencies (polling mode)
uv sync

# Install test dependencies
uv sync --group test

# Install dev dependencies (linting, type checking, etc.)
uv sync --group dev

# Install all dependencies
uv sync --all-groups
```

## Running the Bot

```sh
# Run the bot in polling mode (default)
uv run python main.py

# Run the bot in webhook mode
uv run --group webhook python main.py
```

## Development Tools

### Linting

```sh
uv run --group dev flake8 .
uv run --group dev ruff check .
uv run --group dev black --check .
```

### Type Checking

```sh
uv run --group dev mypy .
```
