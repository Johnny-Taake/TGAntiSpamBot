# Environment Variables

This project is configured via environment variables.

All variables are read automatically at startup using **Pydantic Settings**.
You must provide them via a `.env` file or your deployment environment.

👉 **Almost all variables are already pre-filled in `.env.example`.**
In most cases, you only need to copy it and adjust a few values, e.g. `APP_BOT_TOKEN` and `APP_MAIN_ADMIN_ID` to your own values.

---

## Quick Start

```bash
cp .env.example .env
```

Then edit `.env` and **at minimum** set:

* `APP_BOT_TOKEN`
* `APP_MAIN_ADMIN_ID`

---

## Logging

### `APP_LOG_LEVEL`

Controls application log verbosity.

**Allowed values:**

* `DEBUG`
* `INFO`
* `WARNING`
* `ERROR`
* `CRITICAL`

**Recommended:**

* `DEBUG` for development
* `INFO` for production

```env
APP_LOG_LEVEL=DEBUG
```

---

### `APP_WRITE_TO_FILE`

Whether logs should also be written to a file.

```env
APP_WRITE_TO_FILE=true
```

When enabled, logs are written to `logs/app.log`.

---

## Database (SQLite)

### `APP_DB_PATH`

Path to the SQLite database file.

```env
APP_DB_PATH=database/database.db
```

The directory will be created automatically if it doesn’t exist.

---

### `APP_DB_ECHO`

Enables SQLAlchemy SQL query logging.

```env
APP_DB_ECHO=false
```

Set to `true` only when debugging SQL queries.

---

### `APP_DB_TIMEOUT`

SQLite connection timeout in seconds.

```env
APP_DB_TIMEOUT=30
```

Increase this if you experience `database is locked` errors.

---

## Application Runtime

### `APP_RUN_PORT`

Port used when running in **webhook mode**.

```env
APP_RUN_PORT=8000
```

Ignored in polling mode.

---

## Bot Mode

### `APP_BOT_MODE`

How the bot receives updates.

**Allowed values:**

* `polling`
* `webhook`

```env
APP_BOT_MODE=polling
```

---

### `APP_WEBHOOK_URL`

Public HTTPS URL for webhook mode.

⚠️ **Required only if `APP_BOT_MODE=webhook`.**

```env
APP_WEBHOOK_URL=https://your-domain.example
```

Examples:

* ngrok URL
* production domain with HTTPS

---

## Telegram Bot

### `APP_BOT_TOKEN`

Telegram Bot API token.

🚨 **Required. Never commit this to Git. Otherwise invalidate it ASAP and create the new one**

```env
APP_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### `APP_MAIN_ADMIN_ID`

Telegram user ID of the **main administrator**.

This user:

* can access `/chats` command
* can manage chat activation
* is excluded from anti-spam checks

```env
APP_MAIN_ADMIN_ID=8875...
```

---

## Anti-Spam Configuration

### `APP_MIN_MINUTES_IN_CHAT`

Minimum time (in minutes) a user must be in the chat before being trusted.

```env
APP_MIN_MINUTES_IN_CHAT=60
```

Converted internally to seconds.

---

### `APP_MIN_VALID_MESSAGES`

Number of clean (non-spam) messages required before a user is trusted.

```env
APP_MIN_VALID_MESSAGES=20
```

---

### `APP_ANTISPAM_QUEUE_SIZE`

Maximum number of pending messages in the anti-spam queue.

```env
APP_ANTISPAM_QUEUE_SIZE=10000
```

If the queue is full, the bot will wait until workers free space.

---

### `APP_ANTISPAM_WORKERS`

Number of background workers processing anti-spam messages.

```env
APP_ANTISPAM_WORKERS=8
```

**Guidelines:**

* 2–4 for small bots
* 4–8 for active group

---

## Fun Commands

### `APP_FUN_COMMANDS_ENABLED`

Enable or disable fun commands like `/dice` and `/slot`.

```env
APP_FUN_COMMANDS_ENABLED=false
```

When `false` (default):

* `/dice` command is disabled
* `/slot` command is disabled
* Commands won't appear in help text

When `true`:

* `/dice` command works (in private chats)
* `/slot` command works (in private chats)
* Commands appear in help text

---

## AI / LLM (Optional)

The bot can optionally use an LLM backend to perform **contextual spam detection** (in addition to classic heuristics and trust logic).

📄 **Setup guide:** [`docs/LLM.md`](docs/LLM.md)

### `APP_AI_ENABLED`

Global switch for AI-based moderation.

```env
APP_AI_ENABLED=false
```

When `false`:

* the bot runs in **rule-based mode only**
* no LLM requests are made
* any incomplete AI config is ignored safely

When `true`:

* the bot will try to initialize the AI client
* if required variables are missing, AI is skipped with a warning

---

## AI Provider & Model

### `APP_AI_BASE_URL`

Base URL of the provider endpoint.

```env
APP_AI_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

Notes:

* The bot expects an **OpenAI-compatible Chat Completions** endpoint.
* For local providers the URL may differ (e.g. Ollama /api/chat).

---

### `APP_AI_API_KEY`

API key for your provider.

```env
APP_AI_API_KEY=sk-...
```

Notes:

* Required for cloud providers (OpenAI, OpenRouter, etc.)
* For local providers (Ollama / LM Studio), a dummy value is acceptable

---

### `APP_AI_MODEL`

Model identifier as required by your provider.

```env
APP_AI_MODEL=qwen/qwen-2.5-7b-instruct
```

---

## AI Moderation Behavior

### `APP_AI_SPAM_THRESHOLD`

Score threshold above which a message is treated as spam.

```env
APP_AI_SPAM_THRESHOLD=0.3
```

Guidelines:

* `0.2` — stricter moderation (more deletions)
* `0.3` — balanced (default)
* `0.4+` — more permissive (fewer deletions)

---

### `APP_AI_TEMPERATURE`

Model temperature for scoring.

```env
APP_AI_TEMPERATURE=0.2
```

Lower values make output more consistent and stable for moderation.

---

## AI HTTP Client (Networking)

### `APP_HTTP_CONCURRENCY`

Maximum number of concurrent requests to the LLM backend.

```env
APP_HTTP_CONCURRENCY=5
```

Guidelines:

* Local inference: `1`
* Cloud APIs: `5–10`

---

### `APP_HTTP_TIMEOUT_S`

Request timeout in seconds.

```env
APP_HTTP_TIMEOUT_S=30.0
```

Increase this if your model is slow or you use heavy “reasoning” models.

---

### `APP_HTTP_MAX_CONNECTIONS`

Total connection pool size.

```env
APP_HTTP_MAX_CONNECTIONS=40
```

---

### `APP_HTTP_MAX_KEEP_ALIVE_CONNECTIONS`

Max keep-alive connections.

```env
APP_HTTP_MAX_KEEP_ALIVE_CONNECTIONS=20
```

---

### `APP_HTTP_KEEP_ALIVE_EXPIRY_S`

Keep-alive expiry in seconds.

```env
APP_HTTP_KEEP_ALIVE_EXPIRY_S=30.0
```

---

## `.env.example`

A nearly complete and safe template is provided in:

```text
.env.example
```

It contains:

* correct variable names
* recommended defaults
* placeholders instead of secrets

👉 **Always copy `.env.example` instead of creating `.env` from scratch.**

---

## Security Notes

* Never commit `.env`
* Never expose `APP_BOT_TOKEN`
* For production, prefer environment variables over files
