# LLM Setup Guide

This guide explains how to connect different **LLM providers** to the app using `.env` configuration.

The bot supports **OpenAI-compatible Chat Completions APIs**, which allows you to use:

* Cloud providers (OpenAI, OpenRouter, Together AI, Mistral, etc.)
* Local inference (Ollama, LM Studio)
* Custom or self-hosted endpoints

---

## Configuration Overview

All LLM configuration is done via environment variables.

Minimal required setup:

```env
APP_AI_ENABLED=true
APP_AI_BASE_URL=your_provider_url
APP_AI_API_KEY=your_api_key
APP_AI_MODEL=model_name
```

---

## 🔑 Core Environment Variables

### Required

* `APP_AI_ENABLED`
  Enables or disables AI-based spam detection globally.
  If set to `false`, **all AI logic is skipped entirely** and the bot falls back to rule-based moderation only.

* `APP_AI_BASE_URL`
  Base URL of an OpenAI-compatible **chat completions** endpoint.

* `APP_AI_API_KEY`
  API key for the provider.
  For local providers (Ollama, LM Studio), a dummy value is acceptable.

* `APP_AI_MODEL`
  Model identifier as expected by the provider.

---

### Optional (Recommended)

* `APP_AI_TEMPERATURE`
  Sampling temperature.
  Default: `0.2` (low variance, deterministic output)

* `APP_AI_SPAM_THRESHOLD`
  Probability threshold above which a message is considered spam.
  Default: `0.3`

* `APP_HTTP_CONCURRENCY`
  Maximum number of concurrent requests to the LLM backend.

* `APP_HTTP_TIMEOUT_S`
  Request timeout in seconds.
  Default: `30.0`

---

## Local Ollama Setup

For a full Docker + GPU setup, see:
📄 **[`docs/OLLAMA.md`](OLLAMA.md)**

> GPU acceleration is optional but highly recommended for 7B+ models.

---

## Cloud Providers

### OpenRouter (Recommended)

[OpenRouter](https://openrouter.ai/) provides access to many open-source and commercial models behind a single API.

```env
APP_AI_ENABLED=true
APP_AI_BASE_URL=https://openrouter.ai/api/v1/chat/completions
APP_AI_API_KEY=sk-or-...
APP_AI_MODEL=qwen/qwen-2.5-7b-instruct

APP_HTTP_CONCURRENCY=5
APP_HTTP_TIMEOUT_S=30.0
```

> Note: Model latency and cost may vary depending on OpenRouter routing.

**Recommended models:**

* `qwen/qwen-2.5-7b-instruct` - fast, reliable, well-suited for moderation
* `tngtech/deepseek-r1t2-chimera` - stronger reasoning, slower responses

---

### OpenAI

```env
APP_AI_ENABLED=true
APP_AI_BASE_URL=https://api.openai.com/v1/chat/completions
APP_AI_API_KEY=sk-...
APP_AI_MODEL=gpt-4o

APP_HTTP_CONCURRENCY=5
APP_HTTP_TIMEOUT_S=30.0
```

**Suggested models:**

* `gpt-4o` - best balance of quality and latency
* `gpt-4-turbo` - cheaper, slightly slower
* `gpt-3.5-turbo` - fastest, lowest cost, weaker reasoning

---

## Performance Tuning Guidelines

### Concurrency

* **Local inference**: `1`
* **Cloud APIs**: `5–10`
* **Self-hosted GPU clusters**: depends on capacity

### Timeout

* Local models: `30–60s`
* Cloud APIs: `30s`
* Heavy reasoning models: `60–120s`

### Temperature & Threshold

* Temperature: `0.1–0.3` for moderation
* Spam threshold:

  * `0.1–0.2` → strict
  * `0.3` → balanced (default)
  * `0.4+` → permissive

---

## 🚨 Troubleshooting

**Common problems:**

* Rate limits → lower concurrency
* Timeouts → increase timeout or use faster models
* Authentication errors → verify API key format and permissions
* Model not found → double-check model name
* Slow local inference → enable GPU or use smaller models

---

## Customizing Prompt Behavior

This project uses a transparent, text-based moderation policy defined in `prompts/moderation_policy.txt`.

You can customize the bot’s behavior by modifying this file to adapt it to your community’s rules.

### Modifying the Moderation Policy

1. Open `prompts/moderation_policy.txt`
2. Adjust rules according to your guidelines
3. Restart the application to reload the prompt

---

### Scoring Thresholds

Each message receives a score from `0.0` to `1.0`:

* **0.0–0.29** - clean content, warnings, complaints
* **0.3–0.4** - low-grade spam (format-based, mild promotion)
* **0.5–0.6** - offers without a clear funnel
* **0.7–0.9** - clear solicitation or job funnels
* **1.0** - criminal activity or drug trade

---

### Behavior Configuration Variables

| Variable                  | Description                                 | Default | Recommended Range  |
| ------------------------- | ------------------------------------------- | ------- | ------------------ |
| `APP_AI_SPAM_THRESHOLD`   | Score threshold for marking content as spam | `0.3`   | `0.2–0.4`          |
| `APP_AI_TEMPERATURE`      | Model randomness / creativity               | `0.2`   | `0.0–0.5`          |
| `APP_MIN_MINUTES_IN_CHAT` | Minimum time in chat to be trusted          | `60`    | `1–1440`           |
| `APP_MIN_VALID_MESSAGES`  | Clean messages required for trust           | `20`    | `1–100`            |

---

### Adjusting Sensitivity

Stricter moderation:

```env
APP_AI_SPAM_THRESHOLD=0.2
```

More permissive moderation:

```env
APP_AI_SPAM_THRESHOLD=0.4
```

---

### Temperature Effects

* **0.0–0.2** - maximum consistency, predictable output
* **0.3–0.5** - more variance, sometimes better on edge cases

---

## Quick Note

| Provider   | Concurrency | API Key |
| ---------- | ----------- | ------- |
| Ollama     | `1`         | No*     |
| OpenRouter | `5–10`      | Yes     |
| OpenAI     | `5–10`      | Yes     |

\* A dummy API key value is required for local providers due to the unified client interface.
