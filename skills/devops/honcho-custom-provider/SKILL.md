---
name: honcho-custom-provider
description: Configure Honcho's deriver, dialectic, and embeddings to use non-standard LLM providers (Nous, local models, OpenRouter, etc.) instead of the defaults (OpenAI/Anthropic/Google).
---

# Honcho Custom Provider Configuration

Use when setting up or troubleshooting Honcho's deriver/dialectic with a non-standard LLM provider.

## Key Discovery

Honcho's deriver does NOT accept `openai_compatible` as a provider. The valid providers are:
**CRITICAL**: `docker compose restart` does NOT reload `.env` changes. You MUST use:
```bash
docker compose up -d --force-recreate deriver
```

Valid deriver providers: `anthropic`, `openai`, `google`, `groq`, `custom`, `vllm`

To use an OpenAI-compatible endpoint (Nous, OpenRouter, local llama.cpp, etc.), set provider to **`custom`**.

## Required .env Variables (`~/honcho/.env`)

### For Deriver + Dialectic (custom provider)
```bash
DERIVER_PROVIDER=custom
DERIVER_MODEL=xiaomi/mimo-v2-pro          # or your model name

LLM_OPENAI_COMPATIBLE_API_KEY=llama.cpp   # your API key
LLM_OPENAI_COMPATIBLE_BASE_URL=https://inference-api.nousresearch.com/v1  # your endpoint
```

### For Embeddings
```bash
LLM_EMBEDDING_PROVIDER=gemini   # options: openai, gemini, openrouter
```

**PITFALL**: `HONCHO_EMBEDDING_MODEL=local` does NOT work. The correct env var is `LLM_EMBEDDING_PROVIDER`.

### Dialectic Level Overrides
All 5 levels need explicit overrides. Format uses `__` nested delimiter:
```bash
DIALECTIC_LEVELS__minimal__PROVIDER=custom
DIALECTIC_LEVELS__minimal__MODEL=xiaomi/mimo-v2-pro
DIALECTIC_LEVELS__minimal__THINKING_BUDGET_TOKENS=0
DIALECTIC_LEVELS__minimal__MAX_TOOL_ITERATIONS=1
DIALECTIC_LEVELS__minimal__MAX_OUTPUT_TOKENS=512

DIALECTIC_LEVELS__low__PROVIDER=custom
DIALECTIC_LEVELS__low__MODEL=xiaomi/mimo-v2-pro
DIALECTIC_LEVELS__low__THINKING_BUDGET_TOKENS=0
DIALECTIC_LEVELS__low__MAX_TOOL_ITERATIONS=5

DIALECTIC_LEVELS__medium__PROVIDER=custom
DIALECTIC_LEVELS__medium__MODEL=xiaomi/mimo-v2-pro
DIALECTIC_LEVELS__medium__THINKING_BUDGET_TOKENS=0
DIALECTIC_LEVELS__medium__MAX_TOOL_ITERATIONS=2

DIALECTIC_LEVELS__high__PROVIDER=custom
DIALECTIC_LEVELS__high__MODEL=xiaomi/mimo-v2-pro
DIALECTIC_LEVELS__high__THINKING_BUDGET_TOKENS=0
DIALECTIC_LEVELS__high__MAX_TOOL_ITERATIONS=4

DIALECTIC_LEVELS__max__PROVIDER=custom
DIALECTIC_LEVELS__max__MODEL=xiaomi/mimo-v2-pro
DIALECTIC_LEVELS__max__THINKING_BUDGET_TOKENS=0
DIALECTIC_LEVELS__max__MAX_TOOL_ITERATIONS=10
```

### Summary Provider (optional)
```bash
SUMMARY_PROVIDER=google   # or custom — gemini is fine for summaries
```

## Restart After Changes

**CRITICAL**: `docker compose restart` does NOT reload `.env` changes into the container. Docker caches env vars at container creation time. You MUST recreate the container:

```bash
cd ~/honcho
docker compose up -d --force-recreate deriver honcho
```

Verify the new env vars are live:
```bash
docker exec honcho-deriver-1 env | grep DERIVER
```

## Switching to Google/Gemini

If the custom endpoint has auth issues (401), switch deriver to Google instead:

```bash
# ~/honcho/.env
DERIVER_PROVIDER=google
DERIVER_MODEL=gemini-2.5-flash          # deriver: cheap, fast
LLM_GEMINI_API_KEY=your-key            # must be set

# Dialectic levels
DIALECTIC_LEVELS__minimal__PROVIDER=google
DIALECTIC_LEVELS__minimal__MODEL=gemini-2.5-flash-lite
DIALECTIC_LEVELS__low__PROVIDER=google
DIALECTIC_LEVELS__low__MODEL=gemini-2.5-flash-lite
DIALECTIC_LEVELS__medium__PROVIDER=google
DIALECTIC_LEVELS__medium__MODEL=gemini-2.5-flash
DIALECTIC_LEVELS__high__PROVIDER=google
DIALECTIC_LEVELS__high__MODEL=gemini-2.5-flash
DIALECTIC_LEVELS__max__PROVIDER=google
DIALECTIC_LEVELS__max__MODEL=gemini-2.5-pro
```

Then force-recreate (not restart):
```bash
cd ~/honcho && docker compose up -d --force-recreate deriver
```

## Backup/Fallback Provider

**CRITICAL**: Both `BACKUP_PROVIDER` and `BACKUP_MODEL` must be set together or both omitted. Setting only one will cause Pydantic `ValidationError` that crashes BOTH the deriver AND the main honcho container. Fix with:
```bash
cd ~/honcho && docker compose up -d --force-recreate honcho deriver
```

Useful for local fallback when cloud API runs out of credits:

```bash
# Primary: Google/Gemini (cloud)
DERIVER_PROVIDER=google
DERIVER_MODEL=gemini-2.5-flash

# Backup: Ollama (local, RTX 3060)
LLM_OPENAI_COMPATIBLE_BASE_URL=http://host.docker.internal:11434/v1
LLM_OPENAI_COMPATIBLE_API_KEY=ollama
DERIVER_BACKUP_PROVIDER=custom
DERIVER_BACKUP_MODEL=hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest

# Backup for dialectic levels too
DIALECTIC_LEVELS__minimal__BACKUP_PROVIDER=custom
DIALECTIC_LEVELS__minimal__BACKUP_MODEL=hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest
DIALECTIC_LEVELS__low__BACKUP_PROVIDER=custom
DIALECTIC_LEVELS__low__BACKUP_MODEL=hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest
DIALECTIC_LEVELS__medium__BACKUP_PROVIDER=custom
DIALECTIC_LEVELS__medium__BACKUP_MODEL=hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest
```

**Note:** `OPENAI_COMPATIBLE_BASE_URL` is shared config. Safe to point at ollama when primary is `google` (Gemini uses its own client via `LLM_GEMINI_API_KEY`, ignores this var). Docker containers use `host.docker.internal` to reach host services.

## Config Validation Crashes Honcho Main Too

Invalid deriver settings cause Pydantic `ValidationError` on the **honcho main container** — not just the deriver. Watch for `honcho` restarting in `docker compose ps`. This is because honcho main imports the same config module. Fix the .env and force-recreate both:

```bash
cd ~/honcho && docker compose up -d --force-recreate honcho deriver
```

## Verify
```bash
# Check deriver is running without errors
docker logs honcho-deriver-1 --tail 20

# Test endpoint reachability from inside container
docker exec honcho-deriver-1 python -c "import httpx; print(httpx.get('YOUR_URL/v1/models').status_code)"

# Check container health
docker ps --format '{{.Names}}\t{{.Status}}'
```

## Known Valid Providers per Component
| Component | Valid Providers |
|-----------|----------------|
| Deriver | anthropic, openai, google, groq, custom, vllm |
| Dialectic | Same as deriver |
| Embeddings | openai, gemini, openrouter |
| Summary | Same as deriver |

## How `custom` Provider Works
In `src/utils/clients.py`, the `custom` client is created as:
```python
CLIENTS["custom"] = AsyncOpenAI(
    api_key=settings.LLM.OPENAI_COMPATIBLE_API_KEY,
    base_url=settings.LLM.OPENAI_COMPATIBLE_BASE_URL,
)
```
So any OpenAI-compatible endpoint works with `custom`.

## Troubleshooting
- **401 Unauthorized**: Check `LLM_OPENAI_COMPATIBLE_API_KEY` is not a placeholder
- **Provider not found error**: You used `openai_compatible` instead of `custom`
- **Embeddings falling to OpenAI**: `LLM_EMBEDDING_PROVIDER` not set (defaults to `openai`)
- **Deriver health: unhealthy**: Usually means LLM API calls are failing — check logs for 401/timeout
- **Both containers restarting**: Pydantic validation error in .env — check BACKUP_PROVIDER/BACKUP_MODEL are both set or both omitted
