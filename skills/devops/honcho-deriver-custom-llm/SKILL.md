---
name: honcho-deriver-custom-llm
description: Configure Honcho's deriver and dialectic to use a custom OpenAI-compatible LLM endpoint (Nous Portal, llama.cpp, vLLM) instead of OpenAI/Anthropic/Google. Use when the user wants to point Honcho at their own model.
---

# Honcho Deriver — Custom LLM Configuration

## Problem

Honcho's deriver defaults to OpenAI/Anthropic/Google. If you want to use a different endpoint (Nous Portal, local llama.cpp, vLLM), you need specific env var configuration.

## Key Gotcha

The provider name for OpenAI-compatible endpoints is **`custom`**, NOT `openai_compatible`. Using `openai_compatible` causes a Pydantic validation error:

```
Input should be 'anthropic', 'openai', 'google', 'groq', 'custom' or 'vllm'
```

## Configuration Steps

### 1. Edit `~/honcho/.env`

```bash
# Embeddings — use Gemini (or openai if you have a key)
LLM_EMBEDDING_PROVIDER=gemini

# Custom LLM endpoint (e.g., Nous Portal)
LLM_OPENAI_COMPATIBLE_BASE_URL=https://inference-api.nousresearch.com/v1
LLM_OPENAI_COMPATIBLE_API_KEY=your-api-key-here

# Deriver — MUST be "custom" not "openai_compatible"
DERIVER_PROVIDER=custom
DERIVER_MODEL=xiaomi/mimo-v2-pro

# Dialectic levels — all pointed at custom endpoint
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

### 2. Restart containers

```bash
docker restart honcho-deriver-1 honcho
```

### 3. Verify

```bash
# Check deriver logs for errors
docker logs honcho-deriver-1 --tail 20

# Check health
docker inspect honcho-deriver-1 --format '{{.State.Health.Status}}'

# Test from inside container
docker exec honcho-deriver-1 python -c "import httpx; r = httpx.get('YOUR_ENDPOINT/v1/models'); print(r.status_code)"
```

## Supported Providers

| Provider | Env Var Prefix | Notes |
|----------|---------------|-------|
| `anthropic` | `LLM_ANTHROPIC_API_KEY` | Claude models |
| `openai` | `LLM_OPENAI_API_KEY` | GPT models |
| `google` | `LLM_GEMINI_API_KEY` | Gemini models |
| `groq` | `LLM_GROQ_API_KEY` | Groq inference |
| **`custom`** | `LLM_OPENAI_COMPATIBLE_*` | Any OpenAI-compatible endpoint |
| `vllm` | `LLM_VLLM_*` | Local vLLM server |

## Embedding Providers

Only three options: `openai`, `gemini`, `openrouter`. No "local" option.

If using a custom LLM for the deriver, still need a separate embedding provider (Gemini recommended if you have the key).

## Critical: Restarting After Config Changes

**`docker compose restart` does NOT reload `.env` variables.** You must recreate the container:

```bash
# WRONG — keeps old env vars
docker restart honcho-deriver-1

# CORRECT — picks up new .env values
cd ~/honcho && docker compose up -d --force-recreate deriver

# If validation fails on honcho main too (shared config), recreate both
cd ~/honcho && docker compose up -d --force-recreate honcho deriver
```

## Using Google/Gemini as Provider

Gemini uses its **own client** (not OPENAI_COMPATIBLE). Set provider to `google`:

```bash
DERIVER_PROVIDER=google
DERIVER_MODEL=gemini-2.5-flash
LLM_GEMINI_API_KEY=your-gemini-key

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

## Setting Up Backup/Fallback Provider

Both `BACKUP_PROVIDER` and `BACKUP_MODEL` must be set together (or both None):

```bash
# Backup to local ollama (Hermes-4-14B on RTX 3060)
LLM_OPENAI_COMPATIBLE_BASE_URL=http://host.docker.internal:11434/v1
LLM_OPENAI_COMPATIBLE_API_KEY=ollama

DERIVER_BACKUP_PROVIDER=custom
DERIVER_BACKUP_MODEL=hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest

DIALECTIC_LEVELS__minimal__BACKUP_PROVIDER=custom
DIALECTIC_LEVELS__minimal__BACKUP_MODEL=hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest
```

**Note:** `OPENAI_COMPATIBLE_BASE_URL` is shared config. If primary provider is `google`, it doesn't use this var, so it's safe to point at ollama. But if primary is `custom`, both primary and backup share the same endpoint.

## Config Validation Can Crash Honcho Main

Invalid deriver settings (e.g., wrong provider name) cause Pydantic `ValidationError` on the **honcho main** container too — not just the deriver. Watch `docker compose ps` for honcho restarting. Fix the .env and recreate both:

```bash
cd ~/honcho && docker compose up -d --force-recreate honcho deriver
```

## Source

Honcho config: `~/honcho/src/config.py`
Embedding client: `~/honcho/src/embedding_client.py`
