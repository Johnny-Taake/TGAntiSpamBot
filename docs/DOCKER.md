# 🐳 Docker Guide

This document explains how to run **TG AntiSpam Bot** using Docker and Docker Compose.

It is written to be fully usable **without Make**.
If you prefer shortcuts, see the **Optional: Make** section at the end.

---

## Prerequisites

Install:

- **Docker**
- **Docker Compose v2**

Check installation:

```bash
docker --version
docker compose version
```

---

## Quick Start (Docker Compose)

1. Clone the repository:

```bash
git clone <repository-url>
cd TGAntiSpamBot
```

2. Create environment file:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```env
APP_BOT_TOKEN=your_bot_token_here
APP_MAIN_ADMIN_ID=your_telegram_user_id
```

3. Build the image:

```bash
docker compose build
```

4. Start the container:

```bash
docker compose up -d
```

5. Watch logs:

```bash
docker compose logs -f
```

The bot will:

* build and start as a container
* run database migrations automatically at startup
* start in **polling mode** by default (if `APP_BOT_MODE=polling`)

---

## Docker Compose Structure

The project uses a single service:

```yaml
services:
  app:
    build: .
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
    restart: unless-stopped
```

### Volumes

* `./database` → SQLite database persistence
* `./logs` → application logs (if enabled)

This means:

* restarting the container does **not** reset the database
* logs survive container restarts

---

## Polling vs Webhook Mode

### Polling (default)

No public URL required.

```env
APP_BOT_MODE=polling
```

Good for:

* local development
* simple VPS setups
* quick testing

---

### Webhook Mode

Webhook mode requires:

* public **HTTPS** URL
* exposed port (default: `8000`)

Environment variables:

```env
APP_BOT_MODE=webhook
APP_WEBHOOK_URL=https://your-domain.com
APP_RUN_PORT=8000
```

#### docker-compose.yml (important)

You **must expose the port**:

```yaml
services:
  app:
    ports:
      - "8000:8000"
```

> ⚠️ Telegram requires HTTPS for webhooks
> ngrok, Cloudflare Tunnel, or a real domain are suitable.

---

## Common Docker Compose Commands

### Build

```bash
docker compose build
```

### Build without cache

```bash
docker compose build --no-cache
```

### Start (detached)

```bash
docker compose up -d
```

### Start (foreground)

```bash
docker compose up
```

### Stop containers (keeps them)

```bash
docker compose stop
```

### Stop and remove containers

```bash
docker compose down --remove-orphans
```

### Logs

```bash
docker compose logs -f
```

### Restart

```bash
docker compose restart
```

---

## Logs

See container logs:

```bash
docker compose logs -f
```

If `APP_WRITE_TO_FILE=true`, logs are also written to:

```text
./logs/app.log
```

---


## Optional: Make

This repository includes a `Makefile` that wraps the same Docker Compose commands.

Example:

```bash
make run
make logs
```

If you like shortcuts - use it.
If you prefer explicit Docker commands - ignore it completely.

📄 Make reference: [`docs/MAKE.md`](MAKE.md)
