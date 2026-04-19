---
name: local-model-council
version: 1.0.0
description: Set up a multi-model council using local ollama (serial VRAM) + cloud judge. Per-slot fallbacks, serial loading, zero API cost.
author: Etym
---

# Local Model Council

Use when: you want multi-model deliberation for decisions but only have one GPU (12GB VRAM). Ollama manages serial model loading — one model in VRAM at a time. The council queries models sequentially.

## Architecture

```
Council Members (serial, ollama):
  Slot 1: qwen2.5:7b-instruct   (fast, reasoning)
  Slot 2: crow-9b               (different training perspective)
  Slot 3: qwen3.5-9b-heretic    (uncensored, creative)

Judge (cloud):
  mimo-v2-pro via Nous OAuth    (synthesizes best answer)

Total time: ~25-45s per council deliberation
Cost: zero (local models + free cloud judge)
```

## Key Constraint

**One model in 12GB VRAM at a time.** Ollama handles swapping automatically — loads a model, queries it, unloads, loads next. Cannot run models in parallel on a single GPU.

## Setup

### Step 1: Pull/Link Models in Ollama

```bash
# Already installed
ollama list

# Pull new models
ollama pull qwen2.5:7b-instruct

# Create from local GGUF
cat > Modelfile.crow-9b << 'EOF'
FROM /path/to/crow-9b.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF
ollama create crow-9b -f Modelfile.crow-9b
```

### Step 2: Configure LiteLLM Proxy (Optional)

If using a proxy for uniform API access:

```bash
# config.yaml
model_list:
  - model_name: council-slot1
    litellm_params:
      model: ollama/qwen2.5:7b-instruct
      api_base: http://host.docker.internal:11434
  - model_name: council-slot2
    litellm_params:
      model: ollama/crow-9b
      api_base: http://host.docker.internal:11434
  - model_name: council-judge-local
    litellm_params:
      model: ollama/hermes-14b
      api_base: http://host.docker.internal:11434

# Run
docker run -d --name litellm -p 4000:4000 \
  -v ~/.hermes/litellm:/app \
  ghcr.io/berriai/litellm:main-latest \
  --config /app/config.yaml
```

### Step 3: Patch Council Plugin for Serial Loading

Replace parallel ThreadPoolExecutor with serial loading:

```python
def _run_council(question, context):
    """Serial: one model at a time in VRAM."""
    results = []
    for i, model in enumerate(COUNCIL_MODELS):
        logger.info(f"Council member {i+1}/{len(COUNCIL_MODELS)}: {model}")
        member = _query_council_member(model, question, context)
        results.append(member)
    # Judge synthesizes
    successful = [r for r in results if r["status"] == "success"]
    judge_answer = _call_council_model(JUDGE_MODEL, _build_judge_prompt(...))
    return {"status": "success", "answer": judge_answer, "individual_answers": ...}
```

### Step 4: Per-Slot Fallbacks

```python
# In _query_council_member:
def _query_council_member_with_fallback(model, fallback, question, context):
    result = _query_council_member(model, question, context)
    if result["status"] == "success":
        return result
    logger.warning(f"{model} failed, trying {fallback}")
    return _query_council_member(fallback, question, context)

# Slot 1: try council-slot1, fallback to ollama direct
# Slot 2: try council-slot2, fallback to council-slot1
# Slot 3: try council-slot3, fallback to council-judge-local
# Judge: council-judge (cloud), fallback to council-judge-local (ollama)
```

## Model Selection for 12GB VRAM

| Model | Size | Best for | Notes |
|-------|------|----------|-------|
| qwen2.5:7b-instruct | 4.7GB | Reasoning, analysis | Fast load (~5s) |
| crow-9b | ~5GB | Claude distill perspective | Different training |
| qwen3.5-9b-heretic | ~8.9GB | Creative, uncensored | Largest that fits |
| hermes-14b | 9GB | Judge, synthesis | Barely fits 12GB |

## Actual Working Setup (April 19, 2026)

Models installed in ollama:
```
qwen2.5:7b-instruct         4.7GB  (Slot 1: fast reasoning)
lelantos-7b                  7.7GB  (Slot 2: DPO creative)
qwen3.5-9b-heretic           9.5GB  (Slot 3: uncensored)
hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF  9.0GB  (judge fallback)
```

GGUF source: `~/.local/share/jan.ai.app/localstorage/` (Jan AI models)

Plugin patched: ThreadPoolExecutor → serial for loop in `~/.hermes/plugins/evey-council/__init__.py`

Setup files: `~/.hermes/council-setup.sh` (setup script), `~/.hermes/council-patch.py` (plugin patcher)

## Pitfalls

1. **Serial loading adds latency** — ~5-15s per model swap. Total council: 25-45s vs ~10s for cloud parallel. Acceptable for decisions, not for real-time.

2. **Judge model should be cloud** — the judge synthesizes 3 answers, needs strong reasoning. Cloud models (mimo-v2-pro) are better judges than local 7-9B models.

3. **Fallback chain prevents total failure** — if one model fails, the next slot's model tries instead. Council degrades gracefully.

4. **Temperature variation** — set different temperatures per slot (0.5, 0.7, 0.9) to get genuinely different perspectives.

5. **LiteLLM proxy is optional** — can call ollama API directly at localhost:11434/v1/chat/completions without Docker.

## When to Use Council vs Voices

| Decision type | Use |
|---|---|
| Creative design (lore, worldbuilding) | Voices (Oracle/Builder/Writer/Gamer) |
| Architecture (tree gen, agent merge) | Council (3 fresh perspectives) |
| Stuck problem (BFS, agent navigation) | Council (novel approaches) |
        | Naming (AQ values, zone alignment) | Either |
| Third ending evaluation | Council (evaluates candidates) |

## New Findings (April 19, 2026)

### Temperature Modes as Perspective

Using the SAME model at different temperatures creates distinct perspectives:
- analytical (0.3): precise, factual, direct
- creative (0.9): lateral, surprising, unconventional
- balanced (0.7): reasoned but open

Config:
```python
"temperature_modes": {"analytical": 0.3, "balanced": 0.7, "creative": 0.9}
```

Slot config includes `temperature_mode` field. Temperature is computed from mode + override.

### Jan AI Model Template Issues

Models from `~/.local/share/jan.ai.app/localstorage/` (lelantos-maid-dpo-7b, Qwen3.5-9B-ultra-heretic) have wrong ollama chat templates. They produce garbage output (ADP corporate text, UK demographics, empty responses).

Fix: download correct GGUF from TheBloke or unsloth on HuggingFace:
```bash
curl -L "https://huggingface.co/TheBloke/MythoMax-L2-13B-GGUF/resolve/main/mythomax-l2-13b.Q4_K_M.gguf" -o ~/.hermes/council/models/mythomax-l2-13b.Q4_K_M.gguf
curl -L "https://huggingface.co/unsloth/gemma-3-12b-it-GGUF/resolve/main/gemma-3-12b-it-Q4_K_M.gguf" -o ~/.hermes/council/models/gemma-3-12b-it-Q4_K_M.gguf

ollama create mythomax-l2-13b -f /tmp/modelfile_mythomax
ollama create gemma3:12b-it -f /tmp/modelfile_gemma3
```

### numogram-council Plugin (Separate from evey-council)

Created as NEW plugin at `~/.hermes/plugins/numogram-council/` — does NOT overwrite evey-council.

Features:
- Direct ollama API calls (no LiteLLM proxy needed)
- Configurable models per slot (not hardcoded)
- Temperature modes with `mode_override` parameter
- Per-slot fallback chains
- Judge: cloud mimo-v2-pro + local fallback
- Council rounds with different temperatures

```python
council_decide(
    question='...',
    context='...',
    mode_override='creative'  # override all slots to creative temp
)
```

### Ollama Direct API (No LiteLLM)

```python
def call_ollama(model, prompt, temperature=0.7, max_tokens=800, timeout=120):
    import urllib.request, json
    url = "http://localhost:11434/api/generate"
    data = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens}
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read()).get("response", "")
```

### VRAM Sizing (12GB RTX 3060)

| Quant | 7B | 9B | 12-14B |
|-------|-----|-----|--------|
| Q4_K_M | 4.7GB | 5.5GB | 7-8GB |
| Q3_K_M | 3.5GB | 4GB | 5-6GB |

All three council slots (Q4_K_M quant) fit in 12GB — one at a time via ollama serial loading.

### Actual Working Council (April 19)

| Slot | Model | Size | Temp | Status |
|------|-------|------|------|--------|
| 1 | qwen2.5-coder:14b | 9GB | 0.3 | Pulling |
| 2 | mythomax-l2-13b | 7.9GB | 0.9 | ✓ Installed |
| 3 | gemma3:12b-it | 7.3GB | 0.7 | ✓ Installed |
| Judge | mimo-v2-pro (cloud) | — | 0.3 | Nous OAuth |
| Fallback | qwen2.5:7b-instruct | 4.7GB | — | ✓ Installed |
