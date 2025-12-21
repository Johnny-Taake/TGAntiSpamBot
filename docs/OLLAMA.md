# Local Ollama Setup (Docker + NVIDIA GPU)

This guide explains how to run **Ollama locally in Docker** with optional **NVIDIA GPU acceleration**, and how to connect it to the app via `.env`.

## Requirements

* Docker + Docker Compose installed
* If you want **GPU support**:

  * NVIDIA GPU
  * NVIDIA drivers installed on the host
  * NVIDIA Container Toolkit installed (so Docker can access the GPU)

> If you don’t have GPU, you can still run Ollama on CPU - just skip the GPU parts - still not recommended.

---

## 1) Quick GPU sanity check

Run:

```sh
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

If everything is set up correctly, you should see your GPU listed.

If you get an error like “could not select device driver”, GPU runtime is not configured (you likely need NVIDIA Container Toolkit / drivers). Check [NVIDIA docs](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for details.

> If you are having any problems - google it or ask GPT. You can also open an issue in the repo.

---

## 2) Docker Compose setup

Create (or extend) your `docker-compose.yml` with an `ollama` service:

```yml
services:
  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama_data:
```

### Notes

* `ports: 11434:11434` exposes Ollama to the host at `http://localhost:11434`
* `ollama_data` persists downloaded models across restarts
* The `deploy.resources...` GPU section is the part that enables NVIDIA GPUs

---

## 3) Start Ollama (if you are using CMake and the same yml file as for the app - make commands will work out of the box)

```sh
docker compose up -d ollama
```

Check logs:

```sh
docker compose logs -f ollama
```

Check health endpoint:

```sh
curl -s http://localhost:11434/api/tags
```

If it returns JSON, Ollama is alive.

---

## 4) Download a model (inside the container)

Ure the sctipt:

```sh
chmod +x scripts/ollama_pull_model.sh
./scripts/ollama_pull_model.sh qwen2.5:7b-instruct
```

OR pick a model and pull it with docker compose:

```sh
docker compose exec ollama ollama pull qwen2.5:7b-instruct
```

List installed models:

```sh
docker compose exec ollama ollama list
```

---

## 5) Configure your app to use local Ollama

In your `.env`:

```env
APP_AI_ENABLED=true

# Local Ollama API
APP_AI_BASE_URL=http://localhost:11434/api/chat
APP_AI_MODEL=qwen2.5:7b-instruct
APP_AI_API_KEY=ollama

# FOR LOCAL OLLAMA SHOULD BE 1 ( ! )
APP_HTTP_CONCURRENCY=1
APP_HTTP_TIMEOUT_S=30.0

APP_AI_TEMPERATURE=0.2
APP_AI_SPAM_THRESHOLD=0.3
```

### Important: if your app runs inside Docker too

If your **app container** is in the same `docker-compose.yml` network, then `localhost` inside the app container points to itself, not Ollama.

Use the service name instead:

```env
APP_AI_BASE_URL=http://ollama:11434/api/chat
```

---

## 6) Quick API test (optional)

You can test Ollama directly:

```sh
curl http://localhost:11434/api/chat -s -H "Content-Type: application/json" -d '{
  "model": "qwen2.5:7b-instruct",
  "messages": [
    {"role":"system","content":"Return ONLY a number between 0.0 and 1.0."},
    {"role":"user","content":"DM me for a quick deal"}
  ],
  "stream": false
}'
```

---

## Troubleshooting

### GPU not detected in container

* Re-run the `nvidia-smi` Docker test (Step 1)
* Confirm NVIDIA drivers installed on host
* Confirm NVIDIA Container Toolkit installed
* Confirm Docker daemon is configured for NVIDIA runtime

### Model is slow / bot lags

* Lower concurrency: `APP_HTTP_CONCURRENCY=1`
* Use a smaller model
* Ensure GPU is actually being used (check container logs and host GPU utilization)
