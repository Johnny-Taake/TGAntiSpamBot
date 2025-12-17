#  Makefile Guide

This project uses **Make** as a convenient wrapper around Docker Compose.

Make is **not mandatory**, but it makes daily work faster and less error-prone.

---

## Why Make?

Instead of typing:

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

You can simply type:

```bash
make run
make logs
```

---

## Available Commands

### `make run`

Builds the image (if needed) and starts the bot.

```bash
make run
```

Equivalent to:

```bash
docker compose build
docker compose up -d
```

---

### `make build`

Build Docker images:

```bash
make build
```

---

### `make build-no-cache`

Build images without cache (useful if dependencies changed):

```bash
make build-no-cache
```

---

### `make up`

Start containers without rebuilding:

```bash
make up
```

---

### `make stop`

Stop running containers:

```bash
make stop
```

---

### `make down`

Stop and remove containers (keeps database and logs):

```bash
make down
```

---

### `make restart`

Restart containers:

```bash
make restart
```

---

### `make rebuild`

Full rebuild + restart:

```bash
make rebuild
```

This runs:

1. `docker compose down`
2. `docker compose build --no-cache`
3. `docker compose up -d`

---

### `make logs`

Follow logs in real time:

```bash
make logs
```

---

## Requirements

* GNU Make
* Docker
* Docker Compose v2

### Installing Make

**Linux:**

Debian / Ubuntu:
```bash
sudo apt install make
```

Arch Linux:
```bash
sudo pacman -S make
```

**macOS (brew):**

```bash
brew install make
```

**Windows:**

* Use WSL (recommended)
* Or install Make via Chocolatey / Scoop
