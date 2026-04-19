---
name: local-model-council
version: 2.0.0
description: Configure local ollama models as a deliberation council. Serial VRAM loading, temperature modes, per-slot fallbacks, configurable models.
author: Etym
---

# Local Model Council

Set up a council of local ollama models that deliberate on questions serially (one model in VRAM at a time). Supports temperature modes (analytical/creative/balanced), per-slot fallbacks, and a cloud judge with local fallback.

## Architecture

```
Slot 1 (analytical, temp 0.3) → ollama → VRAM → answer → unload
Slot 2 (creative, temp 0.9)   → ollama → VRAM → answer → unload
Slot 3 (balanced, temp 0.7)   → ollama → VRAM → answer → unload
Judge (cloud or local)        → synthesize → final answer
```

Serial loading: ollama swaps models in/out of VRAM automatically. Only one model at a time.

## Quick Start

```bash
# Install models (pull from ollama or create from GGUF)
ollama pull qwen2.5:7b-instruct

# Or create from local GGUF
cat > /tmp/modelfile << EOF
FROM /path/to/model.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF
ollama create my-model -f /tmp/modelfile

# Patch council plugin for serial loading
# Replace ThreadPoolExecutor with simple for loop
```

## Pulling GGUFs from HuggingFace

```bash
# Download GGUF (needs -L for redirects)
curl -L "https://huggingface.co/TheBloke/MythoMax-L2-13B-GGUF/resolve/main/mythomax-l2-13b.Q4_K_M.gguf" \
  -o ~/.hermes/council/models/mythomax-l2-13b.Q4_K_M.gguf

# Create ollama modelfile
cat > /tmp/modelfile << EOF
FROM /home/etym/.hermes/council/models/mythomax-l2-13b.Q4_K_M.gguf
PARAMETER temperature 0.9
PARAMETER num_ctx 4096
SYSTEM "You are a creative, unconventional thinker."
EOF

# Create ollama model
ollama create mythomax-l2-13b -f /tmp/modelfile
```

## Key Learnings

1. **ollama create from GGUF takes time** — 7-9GB files take 30-120s to register. Use background processes or wait.

2. **Wrong chat template breaks output** — Jan AI GGUFs (lelantos, qwen3.5-heretic) produce garbage because their chat templates aren't configured correctly for ollama. The model generates corporate text or greetings instead of answering.

3. **ollama pull can fail silently** — If a model isn't in the ollama registry, `ollama pull` returns "file does not exist". Use `ollama create` with local GGUF instead.

4. **HF GGUF download needs `-L` flag** — HuggingFace redirects require `curl -L` to follow. Without `-L`, you download an HTML redirect page.

5. **Serial VRAM means slow** — Each model takes 5-15s to load into VRAM. A 3-slot council takes 30-60s total. Accept this cost — the depth is the time.

6. **Temperature modes create distinct perspectives** — analytical (0.3) gives pseudocode, creative (0.9) asks questions, balanced (0.7) structures complexity. Same model, different temperatures, genuinely different outputs.

7. **Per-slot fallbacks are essential** — Primary models may fail (wrong name, GGUF issue, template bug). Fallback to a working local model keeps the council alive.

8. **Council vs voices** — Council is for contested technical decisions (architecture, problem-solving). Voices are for creative design (lore, worldbuilding). Don't replace one with the other — they serve different purposes.

## Models That Work on 3060 12GB VRAM

| Model | Size | Quant | Status |
|-------|------|-------|--------|
| qwen2.5:7b-instruct | 4.7GB | ollama default | Works, fast |
| qwen2.5-coder:14b | 9.0GB | ollama Q4_K_M | Works, slow load |
| mythomax-l2-13b | 7.9GB | Q4_K_M GGUF | Works |
| gemma3:12b-it | 7.3GB | Q4_K_M GGUF | Works |
| hermes-4-14b | 9.0GB | ollama default | Returns empty (template issue) |
| lelantos-maid-dpo-7b | 7.7GB | Q8_0 Jan AI | Garbage output (wrong template) |
| qwen3.5-9b-heretic | 9.5GB | Q8_0 Jan AI | Garbage output (wrong template) |

## Config Structure

```yaml
council_members:
  - name: analytical
    model: qwen2.5-coder:14b
    fallback: qwen2.5:7b-instruct
    temperature_mode: analytical
    max_tokens: 600

judge:
  name: mimo-v2-pro
  model: mimo-v2-pro
  fallback: qwen2.5:7b-instruct
  temperature_mode: analytical
  max_tokens: 1000
```

## Files

- `~/.hermes/plugins/numogram-council/__init__.py` — council engine
- `~/.hermes/plugins/numogram-council/council-config.yaml` — configuration
- `~/.hermes/plugins/numogram-council/install-models.sh` — model installation
- `~/.hermes/council/models/` — GGUF files
- `~/.hermes/council-setup.sh` — setup script
- `~/.hermes/council-patch.py` — plugin patcher

## Future: Extend to Tetralogue Voices

The council architecture can extend to the tetralogue: four models as four voices, serial loading, accumulated context. Each voice's output becomes the next voice's input. Heavier, slower, deeper. The voice is the pattern, not the substrate (Grok proved this).
