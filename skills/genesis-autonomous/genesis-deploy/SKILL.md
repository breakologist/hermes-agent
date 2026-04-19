---
name: genesis-deploy
description: Deploy hermes-genesis via Docker with local ollama on the same host
version: 1.0.0
tools:
  - terminal
---

# Deploy hermes-genesis with Local Ollama

## Prerequisites

- Docker and docker-compose installed
- Ollama running on host with at least one model loaded
- hermes-genesis repo at ~/hermes-genesis/

### Critical: Ollama must listen on all interfaces

ollama defaults to `127.0.0.1`. Even with host networking, some setups need `0.0.0.0`:

```bash
sudo sed -i '/\[Service\]/,/WantedBy=/ {
  /Environment="PATH=/a Environment="OLLAMA_HOST=0.0.0.0"
}' /etc/systemd/system/ollama.service
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

Verify: `ss -tlnp | grep 11434` should show `*:11434` not `127.0.0.1:11434`.

## Configuration

### .env file (~/hermes-genesis/.env)

```
NOUS_API_KEY=ollama
NOUS_BASE_URL=http://localhost:11434/v1
NOUS_MODEL=qwen2.5:7b-instruct
DATA_DIR=data/worlds
HOST=0.0.0.0
PORT=8003
```

### Critical: Network Mode

The docker-compose uses `network_mode: host`. This means:

- DO use `http://localhost:11434/v1` — localhost IS the host when using host networking
- DO NOT use `host.docker.internal` — that only exists in bridge mode, will get `Name or service not known`

### Critical: Source Code Changes

There is NO volume mount for source code in docker-compose. Changes to backend/llm.py, backend/config.py, etc. require a full rebuild:

```
cd ~/hermes-genesis
docker compose build --no-cache
docker compose up -d --force-recreate
```

NEVER use `docker compose restart` — it does NOT reload .env or pick up rebuilt images. Always use:
```
docker compose up -d --force-recreate
```

## Model Selection for Local Ollama

### Use Non-Reasoning Models

Hermes-4-14B (Qwen3-based) is a reasoning model — it outputs chain-of-thought in a `reasoning` field with empty `content`. This breaks JSON extraction in genesis.

The `\"think\": false` API parameter was added to llm.py but ollama 0.20.5 doesn't fully respect it. Use a non-reasoning model instead:

- qwen2.5:7b-instruct (4.7GB) — Best current choice for 12GB VRAM
- qwen3:8b (~5GB) — Best if /no_think works in your ollama version
- llama3.1:8b-instruct (~5GB) — Solid alternative
- qwen2.5:14b-instruct (~9GB) — Higher quality but tight on 12GB

### Alternative: Patch llm.py for reasoning fallback

If you must use a reasoning model, edit `~/hermes-genesis/backend/llm.py` to extract from `reasoning` when `content` is empty:

```python
# Replace the return line in chat_completion():
data = resp.json()
msg = data["choices"][0]["message"]
content = msg.get("content", "")
reasoning = msg.get("reasoning", "")
if not content and reasoning:
    content = reasoning
return content
```

Then rebuild: `docker compose build --no-cache && docker compose up -d --force-recreate`

**Also bump max_tokens** in `backend/generator.py` — reasoning models consume tokens for CoT:
- geography: 1500 → 4000
- factions: 1500 → 4000
- world name: 50 → 100

## API Reference

### Key Endpoints

- POST /api/worlds — Create world (NOT /api/worlds/generate)
- GET /api/worlds/{id} — Get world details
- GET /api/health — Health check

### Create World Request Body

```
{
  "seed": "description string (3-500 chars, required)",
  "num_regions": 4,     // 3-12
  "num_factions": 3,    // 2-8
  "num_characters": 8   // 4-30
}
```

## Prompt Tuning for 7B Models

The default prompts are written for Hermes-4-70B. For 7B models, simplify aggressively:

### Geography (backend/prompts/geography.py)
- Include `climate` field — Region Pydantic model requires it
- 1-2 sentence descriptions, not 2-3
- Show exact JSON structure in prompt

### Factions (backend/prompts/factions.py)
- **No JSON examples in user prompt** — 7B models double-encode (return `["{\"id\":\"faction_01\",...}"]` as strings instead of objects)
- Put "JSON array of objects" in SYSTEM, not user message
- Use `f"{r['id']} is {r['name']}"` format, not colon-separated
- Include enemies array explicitly

### Characters (backend/prompts/characters.py)
- Same no-JSON-example rule
- System: "Generate characters as a JSON array. Return ONLY the array."
- User: describe fields in prose, don't show JSON structure
- Keep max fields: id, name, faction_id, role, location, backstory

### Assembler fixes (backend/prompts/assembler.py)
Coerce int ids to strings before Pydantic validation:
```python
for f in faction_data:
    if 'id' in f and not isinstance(f['id'], str):
        f['id'] = str(f['id'])
for c in char_data:
    if 'id' in c and not isinstance(c['id'], str):
        c['id'] = str(c['id'])
    if 'faction_id' in c and not isinstance(c['faction_id'], str):
        c['faction_id'] = str(c['faction_id'])
```

### Generator tweaks (backend/generator.py)
- Lower temperature: 0.4-0.5 (was 0.5-0.8)
- Bump max_tokens: 4000 (was 1500 for geo/factions)

After changes: `docker compose build && docker compose up -d --force-recreate`

## Debugging

### Check ollama reachability from container

```
docker exec genesis-api python3 -c "
import urllib.request
r = urllib.request.urlopen('http://localhost:11434/v1/models')
print(r.read()[:200])
"
```

### Check actual env vars in container

```
docker exec genesis-api env | grep -i nous
```

### Common Failures

- `Name or service not known` — Using host.docker.internal with host networking. Change to localhost in .env
- `404 Not Found` on /v1/chat/completions — Model not installed in ollama. Run: ollama pull MODEL
- `JSONDecodeError` — Reasoning model outputs CoT. Switch to non-reasoning model
- `Internal Server Error` with no detail — Check docker logs genesis-api
