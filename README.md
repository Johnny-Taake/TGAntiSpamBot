# 🛡️ TG AntiSpam Bot

A production-ready minimal Telegram bot that protects groups and supergroups from spam using a **trust-based moderation system**.

The bot automatically removes suspicious messages from new users while allowing legitimate members to communicate freely - without captchas, delays, or manual moderation.

---

## 🎥 Demo

> *Short demos are worth more than long explanations*

**Spam message deletion:**
![Spam detection demo](docs/gifs/antispam.gif)

**Admin (group management):**
![Admin demo](docs/gifs/admin.gif)

**Bot rights via BotFather:**
![Bot rights demo](docs/gifs/bot_rights.gif)

**Admin rights in a group for bot to delete messages:**
![Admin rights for bot demo](docs/gifs/admin_rights.gif)


---

## ⭐ Key Features

* **Trust-based Anti-Spam**

  * New users are monitored more strictly
  * Trusted users are never interrupted
* **Automatic Spam Deletion**

  * Links, mentions, and suspicious entities are removed
* **Admin Panel**

  * Enable or disable protection per group
  * See all chats the bot is present in
* **Async Queue Processing**

  * Handles high message volume safely
* **Polling & Webhook modes**
* **Persistent Storage**

  * SQLite + migrations
* **Clean Architecture**

  * Filters, middleware, services, registry cache

---

## ❓ How It Works

The bot uses a **trust model** instead of hard rules:

1. **New users**

   * Messages with links or mentions may be deleted
2. **Trust building**

   * Time spent in chat
   * Number of clean messages sent
3. **Trusted users**

   * No moderation
   * No delays
   * No false positives

This approach keeps chats clean **without annoying real people**.

---

## 🪛 Configuration

Configuration is done via environment variables.

📄 **Full explanation:** [`docs/ENV.md`](docs/ENV.md)
📄 **Example file:** [`.env.example`](.env.example)

Minimal required variables:

```env
APP_BOT_TOKEN=your_bot_token_here
APP_MAIN_ADMIN_ID=your_telegram_user_id
```

Everything else has safe defaults.

---

## 📦 Installation

### 🐳 Docker (Recommended)

📄 **Detailed guide:** [`docs/DOCKER.md`](docs/DOCKER.md)

```bash
git clone <repository-url>
cd TGAntiSpamBot

cp .env.example .env
# edit .env

make run
```

The database and logs (depending on the env) are persisted automatically.

[Make](https://en.wikipedia.org/wiki/Make_(software)) is the preferred tool for local development. Otherwise, you can use the docker-compose.yml file directly.

---

### Production / Development Setup

📄 **make usage:** [`docs/MAKE.md`](docs/MAKE.md)
📄 **uv usage:** [`docs/UV.md`](docs/UV.md)

---

## 🤖 Bot Commands

### Private chats only

* `/start` - Welcome message
* `/about` - Bot description
* `/chats` - Admin panel (admin only)
Only if fun is enabled via .env:
* `/dice` - Roll a dice 🎲
* `/slot` - Slot machine 🎰


---

## 🛠️ Admin

Accessible via `/chats` (private chat, admin only).

Allows you to:

* View all groups (after adding there bot, giving admin rights and sending any message in the group after bot join by any user)
* Activate / deactivate anti-spam per group
* Navigate chats with pagination
* Safely manage large numbers of groups


---

## 🧩 Architecture Overview

* **Filters** - chat type, admin-only, private-only
* **Middleware**

  * DB session lifecycle
  * Chat registry cache
* **Services**

  * AntiSpamService (queue + workers)
  * ChatRegistry (in-memory TTL cache)
* **Database**

  * SQLAlchemy ORM
  * Alembic migrations
* **Bot Runtime**

  * aiogram 3.x


---

## 📁 Project Structure

```text
app/
├── antispam/        # Anti-spam logic & workers
├── bot/
│   ├── handlers/    # Commands & message handlers
│   ├── filters/     # Chat/admin filters
│   ├── middleware/  # DB, registry, antispam
│   └── utils/
├── services/        # Business logic
├── db/              # Models & helpers
├── container.py     # App container (DI)
docs/
├── ENV.md
├── DOCKER.md
├── UV.md
├── TEST.md
└── gifs/            # Demo GIFs
```

---

## Deployment Modes

### Polling (default)

* No public URL required
* Best for local or simple hosting

### Webhook

* Requires HTTPS and public URL
* Recommended for production

📄 **Webhook details:** [`docs/DOCKER.md`](docs/DOCKER.md)

```env
APP_BOT_MODE=webhook
APP_WEBHOOK_URL=https://your-domain.com
```

---

## Testing

📄 **Testing guide:** [`docs/TEST.md`](docs/TEST.md)

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Write clean, typed code
4. Add tests where reasonable
5. Open a Pull Request

---

## Support

If you:

* found a bug
* want a feature
* need help with setup

➡️ write to the issues section.
