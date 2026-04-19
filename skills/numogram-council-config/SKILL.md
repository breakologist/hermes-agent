---
name: numogram-council-config
version: 1.0.0
description: Configure and run a local model council for multi-perspective deliberation. Serial VRAM loading through ollama, temperature modes, fallback chains, cloud judge with local fallback.
author: Etym
---

# Numogram Council Configuration

Use when: you need multi-perspective deliberation on a design question, want to validate an approach from multiple angles, or need fresh thinking on a stuck problem. The council gives you 3 different "opinions" synthesized by a judge.

## Architecture

```
Council Member 1 (analytical, temp 0.3)
        ↓ serial VRAM swap
Council Member 2 (creative, temp 0.9)
        ↓ serial VRAM swap
Council Member 3 (balanced, temp 0.7)
        ↓
Judge (cloud or local fallback) → Synthesis
```

Only 1 model in VRAM at a time. Ollama handles swapping. ~60s per full council.

## Plugin Location

`~/.hermes/plugins/numogram-council/__init__.py`

## Temperature Modes

| Mode | Temperature | Use Case | Output Style |
|------|------------|----------|--------------|
| analytical | 0.3 | Technical decisions, algorithms | Precise pseudocode, concrete steps |
| balanced | 0.7 | Design questions, trade-offs | Structured reasoning, pros/cons |
| creative | 0.9 | Open-ended, lateral thinking | Questions back, unexpected connections |

## Current Configuration

```python
COUNCIL_MEMBERS = [
    {"name": "analytical", "model": "qwen2.5-coder:14b", "fallback": "qwen2.5:7b-instruct"},
    {"name": "creative", "model": "mythomax-l2-13b", "fallback": "qwen2.5:7b-instruct"},
    {"name": "balanced", "model": "gemma3:12b-it", "fallback": "qwen2.5:7b-instruct"},
]
JUDGE = {"model": "mimo-v2-pro", "fallback": "qwen2.5:7b-instruct"}
```

## Usage

```python
from numogram_council import council_decide

# Standard (per-slot temperature)
result = council_decide(
    question='How should X work?',
    context='Background information...'
)

# Override temperature for all slots
result = council_decide(
    question='How should X work?',
    mode_override='creative'  # all slots at temp 0.9
)
```

## Model Management

Models in ollama (check with `ollama list`):

| Model | Size | Role | Status |
|-------|------|------|--------|
| qwen2.5-coder:14b | 9GB | Slot 1 analytical | Pulling |
| mythomax-l2-13b | 7.9GB | Slot 2 creative | Installed |
| gemma3:12b-it | 7.3GB | Slot 3 balanced | Installed |
| qwen2.5:7b-instruct | 4.7GB | Fallback for all | Installed |

## Known Issues

1. **Jan AI GGUF models** (lelantos, qwen3.5-heretic): Wrong chat template for ollama. Produce garbage output. Need template fix in modelfile.

2. **Hermes-14B returns empty**: The GGUF model in ollama returns empty responses. Template issue.

3. **Primary model not installed**: If primary model fails, fallback activates automatically. Check `ollama list` to see what's available.

4. **Serial VRAM swapping**: Each model takes ~10-30s to load into VRAM. Total council time: 60-120s. Faster with smaller models.

## Setup

```bash
# Pull models (if not installed)
ollama pull qwen2.5-coder:14b
ollama pull mythomax-l2-13b
ollama pull gemma3:12b-it

# Or install from HF GGUF (if not in ollama registry)
cat > /tmp/modelfile << EOF
FROM /path/to/model.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF
ollama create model-name -f /tmp/modelfile
```

## Council vs Voices

| Use Case | Voices (Oracle/Builder/Writer/Gamer) | Council (3 models + judge) |
|----------|-------------------------------------|---------------------------|
| Creative design | ✓ Better — domain-specific, deep | Generic perspective |
| Architecture | Context-switches between roles | 3 fresh approaches |
| Validation | Voices validate internally | External stress-test |
| Stuck problems | Voices iterate | Fresh perspective |
| Naming | Oracle computes, Writer vibes | 3 proposals, judge selects |

Workflow: Voices → tetralogue → produces insights → best insight → council → validates → feeds back into next tetralogue. The loop spirals.

## Configuration File

`~/.hermes/plugins/numogram-council/council-config.yaml` — editable YAML config for models, fallbacks, temperature modes.
