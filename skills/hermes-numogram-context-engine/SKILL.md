---
name: hermes-numogram-context-engine
description: "Numogram pluggable context engine for Hermes Agent v0.9.0. Implements ContextEngine ABC with AQ tools, zone lookup, syzygy finder, and adjustable focus lens."
version: 1.0.0
metadata:
  hermes:
    tags: [numogram, context-engine, hermes-agent, aq, zones]
    category: devops
---

# Numogram Context Engine

Custom pluggable context engine for Hermes Agent v0.9.0. Injects AQ calculation, zone lookup, and syzygy tools directly into the agent's tool list every turn. Adjustable focus lens from transparent (off) to aggressive (hard).

## When to Use

- The agent needs numogram awareness baked into its context engine (not just loaded as skills)
- You want AQ/zone/syzygy tools available every turn without skill loading overhead
- You want numogram-relevant messages protected during context compression
- You want zone context injected automatically each turn

## Architecture

```
plugins/context_engine/
├── __init__.py          # Discovery/loading framework (219 lines)
└── numogram/
    ├── __init__.py      # The engine (ContextEngine ABC impl)
    └── plugin.yaml      # Metadata
```

### Discovery

The framework at `plugins/context_engine/__init__.py` scans subdirectories for engines:
- `discover_context_engines()` — returns `(name, desc, available)` tuples
- `load_context_engine(name)` — imports and instantiates the engine
- Loading tries `register(ctx)` pattern first, then finds a `ContextEngine` subclass

### The ABC (`agent/context_engine.py`)

Required methods:
- `name` (property) — short identifier string
- `update_from_response(usage)` — called after every LLM call with token usage dict
- `should_compress()` — checked after each turn
- `compress(messages, current_tokens)` — receives full message list, returns compacted list

Optional (power methods):
- `get_tool_schemas()` — return tool definitions the agent gets every turn
- `handle_tool_call(name, args)` — handle those tool calls, return JSON string
- `on_session_start(session_id, **kwargs)` — load state on session begin
- `on_session_end(session_id, messages)` — persist state on session end
- `get_status()` — return status dict for display/logging
- `update_model(model, context_length, ...)` — called on model switch

## Pitfalls

### Frozenset has no `.pop()`

Syzygy pairs are stored as `frozenset({a, b})`. Frozensets are immutable — no `.pop()`, no `.remove()`.

**WRONG:**
```python
other = (pair - {zone}).pop()  # AttributeError: 'frozenset' object has no attribute 'pop'
```

**RIGHT:**
```python
other = next(z for z in pair if z != zone)
```

Also applies to any frozenset iteration. Hit this twice in zone_lookup and _build_zone_context.

### Config reload

The context engine is selected via `context.engine` in `config.yaml`. The agent reads config at session start. Changes require a session restart — not just a gateway restart.

### Tool injection at focus level

Tools returned by `get_tool_schemas()` are injected into the agent's tool list every turn. This costs tokens. Only return tools when the focus level warrants it (e.g., focus >= 2). At focus 0-1, return empty list.

### The `compress()` method IS the compressor

When a custom context engine is active, it replaces the built-in ContextCompressor entirely. The engine must handle ALL compression logic — system message protection, first-N/last-N preservation, etc. If `compress()` just returns messages unchanged, the context will overflow without protection.

## Configuration

In `config.yaml`:
```yaml
context:
  engine: numogram
  numogram:
    focus: 3        # 0=off, 1=soft, 2=medium, 3=hard
    active_zone: 9
```

Focus levels:
- **0 (off)**: Transparent. Returns messages unchanged. No tools. Acts like no engine.
- **1 (soft)**: Light numogram awareness. Protects some numogram messages. No tools injected.
- **2 (medium)**: Tools active (aq_calc, zone_lookup, syzygy_find, numogram_focus). Moderate protection. Zone context header injected.
- **3 (hard)**: Maximum protection. All numogram messages preserved. Full zone context every turn.

## Testing

```python
import sys, json
sys.path.insert(0, '/home/etym/.hermes')
from plugins.context_engine import discover_context_engines, load_context_engine

engines = discover_context_engines()
print(engines)  # [('numogram', '...', True)]

engine = load_context_engine("numogram")
print(engine.name)  # 'numogram'

engine.focus = 2
schemas = engine.get_tool_schemas()
print(len(schemas))  # 4

result = json.loads(engine.handle_tool_call("aq_calc", {"text": "NUMOGRAM"}))
print(result)  # {'aq_value': 174, 'zone': 3, ...}
```

## Files

- Engine: `~/.hermes/plugins/context_engine/numogram/__init__.py`
- Config: `~/.hermes/config.yaml` (context.engine: numogram)
- ABC reference: `agent/context_engine.py` (in hermes-agent repo)
