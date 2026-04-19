---
name: hermes-genesis-local-setup
version: 1.0.0
description: Setting up hermes-genesis with local ollama instead of Nous API. Covers Docker networking, reasoning model patches, and prompt simplification for smaller models.
author: Etym
---

# hermes-genesis with Local Ollama

Run hermes-genesis on localhost using ollama instead of the Nous inference API.

## Prerequisites
- ollama running with a model pulled (e.g., `qwen2.5:7b-instruct`)
- Docker with compose

## Setup

### 1. Configure ollama for Docker access
Ollama defaults to localhost only. Docker containers can't reach it.
```bash
# Add to /etc/systemd/system/ollama.service [Service] section:
Environment="OLLAMA_HOST=0.0.0.0"

sudo systemctl daemon-reload && sudo systemctl restart ollama
```

### 2. Use host networking in docker-compose.yml
```yaml
services:
  genesis:
    build: .
    container_name: genesis-api
    network_mode: host  # replaces ports: - "8003:8003"
    volumes:
      - /opt/genesis/data:/app/data
    env_file:
      - .env
    restart: unless-stopped
```

### 3. Configure .env for local ollama
```env
NOUS_API_KEY=ollama
NOUS_BASE_URL=http://localhost:11434/v1
NOUS_MODEL=qwen2.5:7b-instruct
```

### 4. Patch LLM for reasoning models (if using Hermes-4-14B)
Some reasoning models put output in `reasoning` field instead of `content`.
Patch `backend/llm.py` after `resp.raise_for_status()`:
```python
data = resp.json()
msg = data["choices"][0]["message"]
content = msg.get("content", "")
reasoning = msg.get("reasoning", "")
if not content and reasoning:
    content = reasoning
return content
```

### 5. Simplify prompts for smaller models (7B)
The default prompts are written for 70B models. For 7B:
- Remove JSON examples from user prompts (prevents double-encoding)
- Shorter system prompts (1 line each)
- Fewer fields per entity
- Explicit "output ONLY JSON array" in SYSTEM message
- Add type coercion in assembler (model may return int where str expected)

### 6. Patch assembler for type coercion
In `backend/prompts/assembler.py`, coerce id fields to strings:
```python
for c in char_data:
    if 'id' in c and not isinstance(c['id'], str):
        c['id'] = str(c['id'])
```

## Pitfalls
- `docker compose restart` does NOT reload .env — use `up -d --force-recreate`
- Docker bridge networking prevents access to localhost — use `network_mode: host`
- 7B models may return JSON arrays as strings (double-escaped) — simplify prompts
- 7B models may return int ids where str expected — coerce in assembler
- Reasoning models (Hermes-4-14B) put output in wrong field — patch llm.py
