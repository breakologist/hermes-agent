---
name: numogram-council
version: 1.1.0
description: Configurable model council with serial VRAM loading, temperature modes, fallback chains, and local/cloud judge.
author: Etym
---

# Numogram Council

A configurable model council that queries multiple local ollama models serially (one at a time in VRAM) and synthesizes answers through a cloud or local judge.

## Key Concepts

- **Serial VRAM loading:** Only one model in 12GB VRAM at a time. Ollama manages swapping.
- **Temperature modes:** analytical (0.3), balanced (0.7), creative (0.9) — same model, different thinking.
- **Fallback chains:** Primary model fails → fallback model activates. Council never fully fails.
- **Judge:** Cloud model (mimo-v2-pro via Nous) with local fallback (any ollama model).

## Files

- Plugin: `~/.hermes/plugins/numogram-council/__init__.py`
- Config: `~/.hermes/plugins/numogram-council/council-config.yaml`
- Setup: `~/.hermes/plugins/numogram-council/install-models.sh`
- GGUF models: `~/.hermes/council/models/`
- Ollama modelfiles: `/tmp/modelfile_*` (created during setup)

## Current Configuration

| Slot | Model | Temperature | Status |
|------|-------|------------|--------|
| 1 | qwen2.5-coder:14b (fallback: qwen2.5:7b-instruct) | 0.3 analytical | Pulling |
| 2 | mythomax-l2-13b | 0.9 creative | ✓ Installed (7.9GB) |
| 3 | gemma3:12b-it | 0.7 balanced | ✓ Installed (7.3GB) |
| Judge | mimo-v2-pro (cloud) / fallback: qwen2.5:7b-instruct | 0.3 analytical | Cloud + local |

## Usage

```python
import sys
sys.path.insert(0, '/home/etym/.hermes/plugins/numogram-council')
from __init__ import council_decide

result = council_decide(
    question='How should tree-based dungeon generation work?',
    context='BFS agent gets stuck in loops. 10 zone-themed floors.',
    mode_override='analytical'  # or 'creative' or 'balanced'
)

print(result['answer'])
```

## Temperature Modes

- **analytical (0.3):** Precise, implementable, pseudocode. Asks "how does this work?"
- **balanced (0.7):** Structured, reasoned, step-by-step. Acknowledges complexity.
- **creative (0.9):** Lateral, surprising, asks questions back. Asks "what if it doesn't?"

## Insights from Council Sessions

- Different temperatures from the same model produce genuinely different thought processes (not just rephrasing).
- Different models produce MORE difference than different temperatures. MythoMax asked questions back (unique). Gemma3 structured complexity differently. Qwen gave pseudocode.
- All three confirmed DFS accretion, single corridor per edge, loops after tree for dungeon generation.
- The council is best for: contested technical decisions, architecture choices, design problems where voices haven't converged.
- The tetralogue voices are best for: creative design, lore, worldbuilding, narrative.

## Extending to Tetralogue Voices

The council architecture can extend to the tetralogue: four different models as four voices, serial loading, accumulated context. Each voice's output becomes the next voice's input context. 2-4 minutes per tetralogue vs 30-60s per council.

Proposed model assignments (per user):
- Oracle: gemma4:12b-it-q5_K_M
- Builder: qwen3-coder:14b-q4_K_M
- Writer: gemma4:12b-it-q5_K_M (different prompt)
- Gamer: qwen3.5:9b-instruct-q6_K_M

## Installing New Models

```bash
# From ollama registry
ollama pull <model-name>

# From local GGUF
cat > /tmp/modelfile << EOF
FROM /path/to/model.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF
ollama create <model-name> -f /tmp/modelfile

# From HuggingFace
curl -L "https://huggingface.co/<org>/<model>/resolve/main/<file>.gguf" -o ~/.hermes/council/models/<file>.gguf
```

## Pitfalls

- Jan AI GGUF models (lelantos-7b, qwen3.5-9b-heretic) have wrong chat templates for ollama — produce garbage output. Need manual template in modelfile.
- Hermes-14B returns empty responses — model may be corrupted or wrong GGUF.
- Qwen2.5-Coder:14B is a 9GB download — takes ~15min on 10MB/s connection.
- Council timeout: if models take >60s to respond, increase timeout in `__init__.py`.
