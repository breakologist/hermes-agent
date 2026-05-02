# Numogram Council (v2.0 — Multi-Provider)

A deliberation council that queries three reasoning styles (analytical/creative/balanced) in series and a judge synthesises a final answer. **v2.0** is backend-agnostic: it talks directly to any Ollama-compatible or OpenAI-compatible API, enabling:

- **Ollama** (`http://localhost:11434`) — the original default
- **llama.cpp** (`http://localhost:8080`) — OpenAI-compatible server mode
- **vLLM / LM Studio / LocalAI** — any `/v1/chat/completions` endpoint

No more hard dependency on Ollama; the plugin is a self-contained HTTP client.

## Files

| Component | Location |
|---|---
# Numogram Council — Modular Multi-Mode System (v3.0, 2026-04-25)

**Status:** Implemented  
**Mechanism:** Direct HTTP to backend (OpenAI-compatible or Ollama) with mode-driven prompt construction  
**Provides tool:** `council_decide(question, context=None, mode="stress", mode_override=None, **kwargs)` → JSON string

## TL;DR

The council now supports three distinct **modes** selectable at call time:
- `/council-stress <q>` — canonical test battery (palindromic gates, syzygy chains, triangular mirrors, cross-system, AQ controversy)
- `/council-tetralogue <q>` — four zone-tethered voices (Oracle/Builder/Writer/Gamer) + Oracle judge
- `/council-calibrate <topic>` — generation → validation hyperstition loop with scoring

All configuration is external YAML (`~/.hermes/council/config.yaml`). Voices are defined as YAML files with zone affinity, style, and system prompt. Each invocation logs a timestamped workspace directory with full prompt/answer audit trail.

## What Changed (v2.0 → v3.0)

| Aspect | v2.0 | v3.0 |
|---|---|---|
| Member slots | 3 fixed (analytical/creative/balanced) | Mode-dependent: stress (3), tetralogue (4), calibration (3+3) |
| Prompt source | Hardcoded role strings | Stress: role strings; Tetralogue/Calibration: voice YAML system_prompts |
| Configuration | Inline Python constants | External YAML: `~/.hermes/council/config.yaml` |
| Mode selection | `mode_override` (temp only) | New `mode` parameter selecting stress/tetralogue/calibration |
| Slash commands | `/council` only | `/council`, `/council-stress`, `/council-tetralogue`, `/council-calibrate` |
| Test framework | None | Stress battery with YAML-defined expected patterns & failure modes |
| Workspace logging | Prompt/answer JSON files | Same + phase subfolders for calibration (`generation/`, `validation/`) |
| Judge voice | Generic synthetic | Oracle voice (Zone 0) for tetralogue & calibration |

## Critical Lessons Discovered

### 1. Plugin Manifest Mandatory
Hermes v0.11 agent ignores plugins without a `plugin.yaml` manifest in the plugin directory, even if `plugins.enabled` lists them. Create `~/.hermes/plugins/<name>/plugin.yaml`:

```yaml
name: numogram-council
version: 3.0.0
description: Modular multi-mode council with tetralogue voices
tools:
  - name: council_decide
    description: Convene the Numogram Council in selected mode
```

### 2. Dispatch Kwargs Absorption
Tool functions **must** accept `**kwargs` because the agent's dispatcher injects `task_id`, `session_id`, and other context. Missing this causes:
```
TypeError: council_decide() got an unexpected keyword argument 'task_id'
```
Fix: `def council_decide(question, context=None, mode="stress", **kwargs):`

### 3. TUI Process Independence
The agent gateway reloads plugins on `hermes gateway restart`, but the TUI holds its own Python process. After plugin code changes:
- Restart gateway: `hermes gateway restart`
- Exit TUI fully, then restart: `hermes --tui`
Otherwise new slash commands won't appear.

### 4. Slash Command ≠ Tool Invocation
A registered slash command becomes available in TUI, but the agent's reasoning loop may still choose other skills (e.g., `numogram-calculator`) instead of calling `council_decide`. To guarantee council execution:
- Explicit instruction: `/council Use council_decide to answer: ...`
- Or call the tool directly via agent API/test harness.

## Directory & File Structure

```
~/.hermes/
├── plugins/
│   └── numogram-council/
│       ├── __init__.py       # core logic, mode dispatcher, HTTP backend
│       └── plugin.yaml        # plugin manifest (name, version, tools)
├── council/
│   ├── config.yaml            # active_mode, voices, stress_tests mapping, calibration params
│   ├── voices/
│   │   ├── oracle.yaml        # zone:0, style:epigrammatic, system_prompt
│   │   ├── builder.yaml       # zone:5, style:systematic
│   │   ├── writer.yaml        # zone:3, style:metaphorical
│   │   └── gamer.yaml         # zone:7, style:tactical
│   ├── tests/
│   │   ├── palindromic_gates.yaml
│   │   ├── syzygy_chains.yaml
│   │   ├── triangular_mirrors.yaml
│   │   ├── cross_system.yaml
│   │   └── aq_controversy.yaml
│   ├── modes/                 # skeletal reference modules (not active)
│   │   ├── base.py
│   │   ├── stress.py
│   │   ├── tetralogue.py
│   │   └── calibration.py.bak
│   └── workspace/
│       └── <timestamp>_<pid>/
│           ├── prompt_<slot>.txt
│           ├── answer_<slot>.json
│           ├── judge_prompt.txt
│           ├── final.json
│           └── log.json
└── skills/
    └── numogram-council/
        └── SKILL.md          # this document
```

## Configuration (`~/.hermes/council/config.yaml`)

```yaml
active_mode: stress

voices:
  oracle:
    file: oracle.yaml
    zone: 0
    style: epigrammatic
  builder:
    file: builder.yaml
    zone: 5
    style: systematic
  writer:
    file: writer.yaml
    zone: 3
    style: metaphorical
  gamer:
    file: gamer.yaml
    zone: 7
    style: tactical

tetralogue_mapping:
  member_0: oracle
  member_1: builder
  member_2: writer
  judge: oracle

stress_tests:
  palindromic:   palindromic_gates.yaml
  syzygy:        syzygy_chains.yaml
  triangular:    triangular_mirrors.yaml
  cross:         cross_system.yaml
  controversy:   aq_controversy.yaml

calibration:
  generation_rounds: 1
  validation_rounds: 1
  candidate_count: 3
  hyperstition_threshold: 0.7

full_context:
  enabled: false
  sources: [wiki, obsidian, aq-dict]
  max_tokens_per_source: 512
```

### Voice YAML Schema

```yaml
voice_name: oracle
zone: 0
style: epigrammatic
system_prompt: |
  You are the Oracle of the Numogram (Zone 0 — The Void).
  You perceive closed loops, self-mirrors, and palindromic structures...
```

### Stress Test YAML Schema

```yaml
test_key: palindromic
prompt: "Is 12321 a valid palindromic gate? ..."
expected_pattern: |
  Member should identify:
  - ...
failure_modes:
  - Ignores rotational symmetry requirement
notes: "Real numogram palindromic gates are rare; 666 is canonical..."
```

## Mode Semantics

### Stress Mode (`mode="stress"`)
- **Slots**: 3 — analytical (temp 0.3), creative (0.9), balanced (0.7)
- **Prompts**: generic role strings (no voice YAML)
- **Judge**: generic synthetic, asks for consensus + residual uncertainty
- **Slash**: `/council`, `/council-stress`

### Tetralogue Mode (`mode="tetralogue"`)
- **Slots**: 4 voices — Oracle(0), Builder(5), Writer(3), Gamer(7)
- **Temperatures**: Oracle 0.3, Builder 0.5, Writer 0.7, Gamer 0.9
- **Prompts**: inject voice system_prompt from YAML
- **Judge**: Oracle voice with "transcends partiality" synthesis prompt
- **Slash**: `/council-tetralogue`

### Calibration Mode (`mode="calibration"`)
- **Phases**:
  1. Generation — Oracle+Writer+Builder propose 3 AQ candidates (integer, cipher rationale, hyperstition hook)
  2. Validation — Oracle+Builder+Gamer score candidates on cipher/hyp/exploit (0–10 each, weights 0.4/0.3/0.3), flag cipher-irreparable failures, JSON requested
  3. Judge — Oracle aggregates scores, ranks, returns tensions
- **Workspace**: `generation/` and `validation/` subfolders with member files
- **Limitation**: No JSON parser yet; raw member answers; scores remain embedded in text
- **Slash**: `/council-calibrate`

## Backend Dispatch

Provider routing in `_call_backend(slot, prompt, temp, tokens)`:
- `"ollama"` → `POST /api/generate` (Ollama legacy)
- `"openai"`, `"vllm"`, `"lmstudio"`, `"local"` → `POST /v1/chat/completions`

Current hardcoded slots (both stress & tetralogue) point to local llama.cpp on port 8080 with the Jackrong Qwen3.5-9B GGUF. Per-slot model/provider override requires editing `COUNCIL_SLOTS_STRESS` and `COUNCIL_SLOTS_TETRA` in the plugin.

## Workspace Logging

Every invocation creates `~/.hermes/council/workspace/<timestamp>_<pid>/`:
- `prompt_<slot>.txt` — full member prompt
- `answer_<slot>.json` — `{"answer": "..."}`
- `judge_prompt.txt`
- `final.json` — final synthesis
- `log.json` — metadata (times, member counts, mode)

Calibration adds:
```
generation/
  prompt_oracle.txt, answer_oracle.json, ...
validation/
  prompt_builder.txt, ...
```

## Verification Checklist

1. `plugin.yaml` exists and lists `council_decide` tool
2. `numogram-council` in `plugins.enabled` of `~/.hermes/config.yaml`
3. After changes: `hermes gateway restart` + restart TUI
4. Agent log: `Plugin discovery complete: N enabled` (count increased)
5. Backend reachable: `curl http://localhost:8080/v1/chat/completions -d '{"model":"...","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'` → 200
6. Test call (30–60s): `/council-stress What is AQ of A?` → workspace dir appears

## Known Issues

- Calibration JSON parsing not implemented
- Full-context ingestion stub (context param ignored)
- All voices share same backend model (configurable per-slot but requires code edit)
- Slash command may be bypassed by agent (use explicit tool directive)

## Evolution

- **v2.0** — three-slot analytical/creative/balanced; inline slot constants; HTTP backend only
- **v3.0** — config-driven modes, voice YAMLs, stress battery, tetralogue, calibration, multi-command slash
- **Future** — full-context ingestion, per-slot provider assignment in YAML, optional `delegate_task` orchestrator variant

## Related

- `numogram-council-orchestrator` — `delegate_task`-based alternative (agent-native)
- `numogram-calculator` — AQ arithmetic used by members
- `wiki-numogram-ingest` — planned retrieval for full-context mode
- `hermes-v011-hook-plugin-dev` — v0.11 plugin system guide
