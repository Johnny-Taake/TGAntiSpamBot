# Testing Commands

## Setup

```sh
# Install test dependencies
uv sync --group test
```

## Running Tests

```sh
# Run all tests
uv run --group test pytest

# Run tests with verbose output
uv run --group test pytest -v

# Run tests with coverage
uv run --group test pytest --cov

# Run specific test file
uv run --group test pytest tests/test_file.py
```
