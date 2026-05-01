---
name: numogram-council-config
version: 1.0.0
description: Configure and run a local model council for multi-perspective deliberation. Serial VRAM loading through ollama, temperature modes, fallback chains, cloud judge with local fallback.
author: Etym
---

# Numogram Council Configuration

Use when: you need multi-perspective deliberation on a design question, want to validate an approach from multiple angles, or need fresh thinking on a stuck problem. The council gives you 3 different "opinions" synthesized by a judge.

# Numogram Council Configuration — v2.0 (2026-04-25)

Use when: you need multi-perspective deliberation on a design question, want to validate an approach from multiple angles, or need fresh thinking on a stuck problem. The council gives you 3 different "opinions" synthesized by a judge.

## Architecture (Two Implementations)

```
┌─────────────────────┐        ┌──────────────────────┐
│  Plugin v2.0         │        │ Orchestrator v0.2    │
│  (direct HTTP)      │        │  (delegate_task)     │
├─────────────────────┤        ├──────────────────────┤
│ COUNCIL_SLOTS       │        │ ~/.hermes/council/   │
│   inline in Python  │        │   config.yaml        │
│   provider: "ollama"│        │   provider: "ollama" │
│   provider: "openai"│        │   or "openai" etc.   │
│   base_url per slot │        │   base_url per slot  │
│                     │        │                      │
│ Workspace:          │        │ Workspace:           │
│ ~/.hermes/council/  │        │ ~/.hermes/council/   │
 │ workspace/<session>│        │ workspace/<session>  │
│                     │        │                      │
│ Best for:           │        │ Best for:            │
│ Portable, zero      │        │ Integrated with      │
│ agent coupling      │        │ agent memory &       │
│ Quick experiments   │        │ fallback chains      │
└─────────────────────┘        └──────────────────────┘
```

Only 1 model in VRAM at a time (Ollama swaps automatically). ~60–120s per full council.

## Temperature Modes

| Mode | Temperature | Use Case | Output Style |
|------|------------|----------|--------------|
| analytical | 0.3 | Technical decisions, algorithms | Precise pseudocode, concrete steps |
| balanced | 0.7 | Design questions, trade-offs | Structured reasoning, pros/cons |
| creative | 0.9 | Open-ended, lateral thinking | Questions back, unexpected connections |

## Plugin v2.0 Configuration (Direct HTTP)

**File:** `~/.hermes/plugins/numogram-council/__init__.py`

Edit the inline constants:

```python
COUNCIL_SLOTS = [
    {
        "name": "analytical",
        "model": "qwen2.5-coder:14b",     # Ollama model name
        "provider": "ollama",             # "ollama" or "openai"
        "base_url": "http://localhost:11434",
        "temperature_mode": "analytical",
        "max_tokens": 600,
        "fallback": "qwen2.5:7b-instruct",  # same provider
    },
    {
        "name": "creative",
        "model": "mythomax-l2-13b",
        "provider": "ollama",
        "temperature_mode": "creative",
        "max_tokens": 600,
        "fallback": "qwen2.5:7b-instruct",
    },
    {
        "name": "balanced",
        "model": "gemma3:12b-it",
        "provider": "ollama",
        "temperature_mode": "balanced",
        "max_tokens": 600,
        "fallback": "qwen2.5:7b-instruct",
    },
]

JUDGE_SLOT = {
    "name": "synthesizer",
    "model": "mimo-v2-pro",              # can be cloud or local
    "provider": "nous",                  # provider override for judge
    "temperature_mode": "analytical",
    "max_tokens": 1000,
    "fallback": "qwen2.5:7b-instruct",
    "fallback_provider": "ollama",       # judge fallback can cross providers
    "fallback_base_url": "http://localhost:11434",
}
```

**For llama.cpp:** Change all slots to:
```python
{
    "name": "analytical",
    "model": "your-model-name",          # as llama.cpp reports it
    "provider": "openai",                # or "local"
    "base_url": "http://localhost:8080",
    "temperature_mode": "analytical",
    "max_tokens": 600,
}
```

Restart Hermes gateway after editing: `hermes gateway restart`

## Orchestrator Configuration (delegate_task)

**File:** `~/.hermes/council/config.yaml`

```yaml
version: 1
temperature_modes:
  analytical: 0.3
  balanced: 0.7
  creative: 0.9

council_members:
  - name: analytical
    model: qwen2.5-coder:14b
    provider: ollama
    base_url: http://localhost:11434
    temperature_mode: analytical
    max_tokens: 600
    fallback: qwen2.5:7b-instruct
    description: Precise reasoning, code analysis, implementable steps

  - name: creative
    model: mythomax-l2-13b
    provider: ollama
    temperature_mode: creative
    max_tokens: 600
    fallback: qwen2.5:7b-instruct
    description: Lateral connections, mythic thinking, unexpected angles

  - name: balanced
    model: gemma3:12b-it
    provider: ollama
    temperature_mode: balanced
    max_tokens: 600
    fallback: qwen2.5:7b-instruct
    description: Structured reasoning, trade-off analysis, clarity

judge:
  name: synthesizer
  model: stepfun/step-3.5-flash
  provider: stepfun
  temperature_mode: analytical
  max_tokens: 1000
  fallback: qwen2.5:7b-instruct
  fallback_provider: ollama
  fallback_base_url: http://localhost:11434
  description: Synthesises three perspectives into final answer

settings:
  execution_strategy: serial
  member_timeout: 300
  judge_timeout: 600
  retain_days: 7
```

**For llama.cpp:**
```yaml
council_members:
  - name: analytical
    model: your-model-gguf-name
    provider: openai
    base_url: http://localhost:8080
    temperature_mode: analytical
    max_tokens: 600
```

The orchestrator skill reads this YAML and spawns subagents with matching `provider`/`base_url` via `delegate_task`.

## Usage

```python
# Plugin (direct HTTP)
from numogram_council import council_decide
result = council_decide(
    question="How should BFS corridor attachment work in a 10-zone roguelike?",
    context="Agent gets stuck in loops on dead-end branches.",
    mode_override="analytical"
)
print(result["answer"])

# Orchestrator (if skill registered)
from numogram_council_orchestrator import council_decide
result = council_decide(
    question="What is the geometric relationship between the numogram's seven-segment display and the 45 tetragrams?",
    context="Focus on LED symmetry and rotational gates.",
    mode_override="balanced"
)
print(result["answer"])
```

## Model Management

**Ollama models** (check `ollama list`):
| Model | Size | Role |
|-------|------|------|
| qwen2.5-coder:14b | 9GB | analytical |
| mythomax-l2-13b | 7.9GB | creative |
| gemma3:12b-it | 7.3GB | balanced |
| qwen2.5:7b-instruct | 4.7GB | fallback |

**llama.cpp:** Start with `./server -m models/your-model.gguf --api --port 8080`
Verify: `curl http://localhost:8080/v1/models`

## Known Issues

1. **Ollama model not found** — exact name required; check `ollama list`
2. **OpenAI-compatible 404** — llama.cpp must start with `--api` flag
3. **Timeouts** — default 300s per member; increase in config if needed
4. **Provider mismatch in fallback** — plugin fallbacks assume same provider; orchestrator judge can cross providers via `fallback_provider`/`fallback_base_url`
5. **Serial VRAM swapping** — each slot loads sequentially; total time ≈ sum of inferences + model-load latency. Smaller models faster.

## Council vs Voices

| Use Case | Voices (Oracle/Builder/Writer/Gamer) | Council (3 models + judge) |
|----------|-------------------------------------|----------------------------|
| Creative design | ✓ Better — domain-specific, deep | Generic perspective |
| Architecture | Context-switches between roles | 3 fresh approaches |
| Validation | Voices validate internally | External stress-test |
| Stuck problems | Voices iterate | Fresh perspective |
| Naming | Oracle computes, Writer vibes | 3 proposals, judge selects |

**Workflow:** Voices → tetralogue → insights → best insight → council → validates → feeds back into next tetralogue. The loop spirals.

## Migration: Plugin v1 → v2

v1 used `council-config.yaml`. v2 embeds config inline in `__init__.py`. Old config file is ignored. Copy your model list into `COUNCIL_SLOTS` and `JUDGE_SLOT`.

## Migration: Plugin → Orchestrator

Both tools expose `council_decide` with identical schema. To switch:
1. Ensure `~/.hermes/council/config.yaml` exists with desired slots
2. Disable or unregister the plugin tool
3. Ensure orchestrator skill is loaded
4. Call `council_decide` — agent routes to orchestrator

Future: `council.orchestrator: true` flag in `config.yaml` will control tool resolution.
