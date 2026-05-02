---
name: numogram-council-setup
version: 0.2.0
description: Set up a local model council with serial VRAM loading, per-slot fallbacks, temperature modes, and verified working configurations.
author: Etym
---

# Numogram Council — Local Model Council Setup

Convene a council of local models on a single GPU (serial VRAM — one model at a time). Cloud judge with local fallback. Temperature modes for creative vs analytical rounds.

## Architecture

```
Slot 1 (ollama) → answer
Slot 2 (ollama) → answer    → Judge (cloud or local) → synthesis
Slot 3 (ollama) → answer
```

Serial loading: ollama manages VRAM, loads one model at a time. ~30-60s per council deliberation.

## Setup

### 1. Install ollama models

```bash
# Pull models (serial, one at a time)
ollama pull qwen2.5:7b-instruct    # Fast reasoning (4.7GB)
ollama pull lelantos-7b             # Creative DPO (7.7GB)

# Or create from local GGUF
cat > /tmp/modelfile << EOF
FROM /path/to/model.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF
ollama create my-model -f /tmp/modelfile
```

### 2. Verify models

```bash
ollama list
# Should show your council models
```

### 3. Patch council plugin for serial loading

The original evey-council uses ThreadPoolExecutor (parallel). For serial VRAM loading, replace with a for loop:

```python
# OLD (parallel — fails with single-GPU ollama):
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(_query, model, prompt): model for model in MODELS}
    for future in concurrent.futures.as_completed(futures):
        answers.append(future.result())

# NEW (serial — ollama swaps models in/out of VRAM):
for i, model in enumerate(MODELS):
    result = _query(model, prompt)
    answers.append(result)
```

### 4. Add per-slot fallbacks

Each slot tries its primary model, falls back to secondary if it fails:

```python
COUNCIL_SLOTS = [
    {"name": "reasoning", "model": "qwen2.5-coder:14b", "fallback": "qwen2.5:7b-instruct"},
    {"name": "creative",  "model": "mythomax-l2-13b",   "fallback": "lelantos-7b"},
    {"name": "balanced",  "model": "gemma3:12b-it",     "fallback": "qwen3.5-9b-heretic"},
]

def query_with_fallback(slot, prompt):
    answer = call_ollama(slot["model"], prompt)
    if not answer and slot.get("fallback"):
        answer = call_ollama(slot["fallback"], prompt)
    return answer
```

### 5. Temperature modes

Expose temperature as a parameter for creative vs analytical rounds:

```python
TEMP_MODES = {
    "analytical": 0.3,  # Precise, factual
    "balanced":   0.7,  # Reasoned but open
    "creative":   0.9,  # Lateral, surprising
}

def council_decide(question, context=None, mode="balanced"):
    temp = TEMP_MODES.get(mode, 0.7)
    for slot in COUNCIL_SLOTS:
        answer = query_with_fallback(slot, prompt, temperature=temp)
    synthesis = judge(succeeded_answers)
    return synthesis
```

### 6. Judge with local fallback

Cloud judge (mimo-v2-pro via Nous) with local fallback (hermes-14b via ollama):

```python
JUDGE = {
    "cloud": "mimo-v2-pro",  # Requires OPENAI_BASE_URL
    "local": "hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest",  # ollama model name
}

def judge(answers, prompt):
    synthesis = call_cloud(JUDGE["cloud"], prompt)
    if not synthesis:
        synthesis = call_ollama(JUDGE["local"], prompt)
    return synthesis or max(answers, key=len)  # Last resort
```

## Ollama API (direct, no proxy needed)

```python
import urllib.request, json

def call_ollama(model, prompt, temperature=0.7, max_tokens=800, timeout=120):
    url = "http://localhost:11434/api/generate"
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens}
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read()).get("response", "")
```

## Pitfalls

- **Model names must match ollama exactly.** `hermes-14b` fails if ollama has `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest`. Always check `ollama list`.
- **Serial loading is slow.** 30-60s for 3 models + judge. Each model needs VRAM swap time.
- **Cloud judge needs OPENAI_BASE_URL.** Without it, the cloud call fails silently. Always have a local fallback.
- **Q8_0 models may have wrong chat template.** If a model produces garbage output (like a corporate governance document), the GGUF's chat template doesn't match ollama's expectations. Try a different quant or set the SYSTEM prompt explicitly.
- **Don't overwrite evey-council.** Create as a new plugin (numogram-council). The original may be needed if cloud models come back online.

## Verified Working (April 19, 2026)

### Working Models (ollama)
- `qwen2.5:7b-instruct` — 4.7GB, fast, reliable, good for all temperature modes
- `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:latest` — 9.0GB, best quality, returns empty on some prompts (template issue)

### Fallback-Only Models (created from GGUF)
- `lelantos-7b` — 7.7GB, from Jan AI GGUF. Produces garbage output (wrong chat template). Use as fallback only with explicit SYSTEM prompt.
- `qwen3.5-9b-heretic` — 9.5GB, from Jan AI GGUF. Same template issue. Use as fallback only.

### Not Installed (need pulling)
- `qwen2.5-coder:14b` — 9.8GB GGUF exists but too large for Q5_K_M. Need smaller quant.
- `mythomax-l2-13b` — Not in ollama registry. Check HuggingFace for GGUF.
- `gemma3:12b-it` — Not in ollama registry. Check HuggingFace for GGUF.

### Prompt Encoding (Critical)
When calling ollama via curl, the prompt must be JSON-encoded:
```bash
# WRONG — shell interpolation breaks JSON
curl -d "{\"prompt\": $PROMPT}" ...

# RIGHT — python3 -c escapes properly
curl -d "{\"prompt\":$(python3 -c "import json; print(json.dumps(open('/tmp/prompt.txt').read()))")}" ...
```

Or write prompt to a file first, then:
```bash
PROMPT_JSON=$(python3 -c "import json; print(json.dumps(open('/tmp/prompt.txt').read()))")
curl -d "{\"model\":\"qwen2.5:7b-instruct\",\"prompt\":$PROMPT_JSON,\"stream\":false}" ...
```

### Model Installation from Local GGUF
```bash
# Create modelfile
echo "FROM /path/to/model.gguf" > /tmp/modelfile
echo "PARAMETER temperature 0.7" >> /tmp/modelfile
echo "PARAMETER num_ctx 4096" >> /tmp/modelfile
echo "SYSTEM \"You are a helpful assistant.\"" >> /tmp/modelfile

# Create in ollama
ollama create my-model -f /tmp/modelfile

# Test
curl -s http://localhost:11434/api/generate -d \
  "{\"model\":\"my-model\",\"prompt\":\"Hello\",\"stream\":false,\"options\":{\"num_predict\":50}}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','EMPTY'))"
```

### Performance Notes
- `num_predict=400` → ~5-15s per model
- `num_predict=800` → ~15-30s per model
- `num_predict=1500` → ~30-60s per model
- Temperature doesn't significantly affect speed
- Serial loading overhead: ~2-5s per model swap

## Usage

```python
# Analytical round
council_decide(question='...', context='...', mode_override='analytical')

# Creative round
council_decide(question='...', context='...', mode_override='creative')

# Default (per-slot temperature)
council_decide(question='...', context='...')
```
