---
name: hermes-context-engine
description: "Build custom context engine plugins for Hermes Agent v0.9.0+. Controls what the agent sees each turn — compression, tool injection, domain-specific context."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [context, plugin, compression, hermes-v0.9]
    category: devops
---

# Hermes Context Engine Plugin

Build custom context engines that control what the agent sees each turn. Available since Hermes Agent v0.9.0.

## When This Skill Activates

Use this skill when:
- Building a domain-specific context engine (numogram, project-specific, etc.)
- Injecting custom tools via the context engine slot
- Controlling message compression/prioritization
- Implementing "lens" behavior (adjustable focus levels)

## Architecture

### File Placement
```
~/.hermes/plugins/context_engine/<name>/
├── __init__.py      # ContextEngine subclass + register(ctx) function
└── plugin.yaml      # Metadata (name, description)
```

### Discovery
The framework at `plugins/context_engine/__init__.py` scans subdirectories. Each must have `__init__.py` with either:
- A `register(ctx)` function that calls `ctx.register_context_engine(engine)`
- A top-level class extending `ContextEngine` (auto-discovered and instantiated)

### Activation
Set in `~/.hermes/config.yaml`:
```yaml
context:
  engine: <name>
```
Only ONE engine active at a time. Default is `"compressor"` (built-in).

## The ABC (agent/context_engine.py)

### Required Methods

```python
@property
def name(self) -> str:
    """Short identifier (e.g. 'numogram', 'lcm')."""

def update_from_response(self, usage: Dict[str, Any]) -> None:
    """Track token usage. Called after every LLM call."""

def should_compress(self, prompt_tokens: int = None) -> bool:
    """Return True if compaction should fire."""

def compress(self, messages: List[Dict], current_tokens: int = None) -> List[Dict]:
    """Receive full message list, return compacted list."""
```

### Token State (maintained by engine, read by run_agent.py)
```python
last_prompt_tokens: int = 0
last_completion_tokens: int = 0
last_total_tokens: int = 0
threshold_tokens: int = 0
context_length: int = 0
compression_count: int = 0
```

### Compaction Parameters
```python
threshold_percent: float = 0.75  # When to fire compression
protect_first_n: int = 3         # Always keep first N non-system messages
protect_last_n: int = 6          # Always keep last N non-system messages
```

### Optional: Tool Injection (the powerful part)
```python
def get_tool_schemas(self) -> List[Dict]:
    """Return OpenAI-format tool schemas the agent can call."""
    return [
        {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "What it does",
                "parameters": { ... }
            }
        }
    ]

def handle_tool_call(self, name: str, args: Dict, **kwargs) -> str:
    """Handle tool calls. Must return JSON string."""
```

### Optional: Session Lifecycle
```python
def on_session_start(self, session_id: str, **kwargs) -> None:
    """Load state, kwargs may include hermes_home, platform, model."""

def on_session_end(self, session_id: str, messages: List[Dict]) -> None:
    """Persist state. NOT called per-turn — only at session boundary."""

def on_session_reset(self) -> None:
    """Reset per-session state (on /new or /reset)."""
```

### Optional: Model Switch
```python
def update_model(self, model: str, context_length: int, base_url="", api_key="", provider="") -> None:
    """Called on model switch or fallback. Update context_length + threshold_tokens."""
```

## Implementation Template

```python
"""My custom context engine."""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MyContextEngine:
    @property
    def name(self) -> str:
        return "my-engine"

    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0
    last_total_tokens: int = 0
    threshold_tokens: int = 0
    context_length: int = 0
    compression_count: int = 0
    threshold_percent: float = 0.75
    protect_first_n: int = 3
    protect_last_n: int = 6

    def __init__(self):
        self._my_state = {}

    def update_from_response(self, usage: Dict[str, Any]) -> None:
        self.last_prompt_tokens = usage.get("prompt_tokens", 0)
        self.last_completion_tokens = usage.get("completion_tokens", 0)
        self.last_total_tokens = usage.get("total_tokens",
            self.last_prompt_tokens + self.last_completion_tokens)

    def should_compress(self, prompt_tokens: int = None) -> bool:
        tokens = prompt_tokens or self.last_prompt_tokens
        if self.context_length <= 0:
            return False
        return tokens >= self.threshold_tokens

    def compress(self, messages: List[Dict], current_tokens: int = None) -> List[Dict]:
        # Implement domain-aware compression
        # Always protect: system msgs, first N, last N
        # Your logic for middle messages
        return messages

    def get_tool_schemas(self) -> List[Dict]:
        return []  # Add your tools

    def handle_tool_call(self, name: str, args: Dict, **kwargs) -> str:
        return json.dumps({"error": f"Unknown: {name}"})

    def on_session_start(self, session_id: str, **kwargs) -> None:
        pass

    def on_session_end(self, session_id: str, messages: List[Dict]) -> None:
        pass

    def on_session_reset(self) -> None:
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0
        self.compression_count = 0

    def update_model(self, model: str, context_length: int, **kwargs) -> None:
        self.context_length = context_length
        self.threshold_tokens = int(context_length * self.threshold_percent)


def register(ctx):
    ctx.register_context_engine(MyContextEngine())
```

## Testing & Verification

Always test the engine loads and works before expecting it to activate in the agent:

```python
import sys, json
sys.path.insert(0, '/home/etym/.hermes')

# Clear caches if re-testing after edits
for key in list(sys.modules.keys()):
    if 'plugins.context_engine' in key:
        del sys.modules[key]

from plugins.context_engine import discover_context_engines, load_context_engine

# 1. Discovery — should list your engine
engines = discover_context_engines()
for name, desc, available in engines:
    print(f"  [{'ok' if available else 'FAIL'}] {name}: {desc}")

# 2. Load — should return instance
engine = load_context_engine("my-engine")
assert engine is not None, "Engine failed to load"
print(f"  name: {engine.name}")

# 3. Tools — test at different focus levels
engine.focus = 0
assert len(engine.get_tool_schemas()) == 0, "Tools leak at focus=0"
engine.focus = 2
print(f"  tools: {len(engine.get_tool_schemas())}")

# 4. Tool calls — should return valid JSON
result = engine.handle_tool_call("tool_name", {"arg": "value"})
parsed = json.loads(result)
assert "error" not in parsed or parsed["error"] is None

# 5. Compression — verify message structure preserved
messages = [
    {"role": "system", "content": "system prompt"},
    {"role": "user", "content": "domain specific content"},
    {"role": "assistant", "content": "response"},
    # ... more messages
]
compressed = engine.compress(messages)
assert compressed[0]["role"] == "system", "System messages must be preserved"
assert len(compressed) <= len(messages), "Compression should not grow messages"
```

## Config Reading Pattern

The engine reads its config block in `on_session_start`. Config structure:

```yaml
context:
  engine: my-engine           # selects the engine
  my-engine:                  # engine-specific block (read by engine itself)
    focus: 3
    custom_param: value
```

Reading it:
```python
from pathlib import Path
import yaml

def on_session_start(self, session_id, **kwargs):
    config_path = Path.home() / ".hermes" / "config.yaml"
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        ctx = config.get("context", {})
        my_config = ctx.get(self.name, {})
        self.focus = my_config.get("focus", 1)
    except Exception:
        pass  # use defaults
```

## Pitfalls

- **frozenset has no `.pop()`** — When iterating syzygy pairs (frozensets), use `next(z for z in pair if z != target)` instead of `(pair - {target}).pop()`. frozenset subtraction returns a new frozenset, which also lacks `.pop()`. This was hit and fixed during numogram engine development.
- **compress() receives ALL messages** — The engine gets the full list including system messages. Separate them out first: `system_msgs = [m for m in messages if m.get("role") == "system"]`. Protect system messages always.
- **compress() strategy** — Proven pattern: extract system msgs → head (first N) → tail (last N) → middle (scan for relevance) → inject context as system msg → reassemble. Don't try to compress in-place.
- **Tools need focus gating** — If your engine has adjustable focus levels, only expose tools via `get_tool_schemas()` when focus >= threshold. At focus=0, return `[]` so the agent sees no extra tools. Tools appear EVERY turn and consume context window.
- **Context injection via system messages** — To inject domain context, insert a `{"role": "system", "content": "[Domain] ..."}` message into the protected list. Do this inside `compress()` so it only appears when compression fires.
- **Config.yaml must have `context.engine` key** — Without it, the built-in ContextCompressor runs. Discovery finds your engine but doesn't auto-select it.
- **Session restart required** — Changing `context.engine` in config.yaml requires agent restart. Use a tool (like `numogram_focus`) for live changes within a session.
- **Only ONE engine active** — You can't stack engines. Build a composite internally if you need multiple behaviors.
- **plugin.yaml for discovery** — Include a `plugin.yaml` with `name` and `description` in your engine directory. The discovery system reads it for metadata. Without it, the engine still loads but shows no description.

## Lens Pattern (adjustable focus)

A proven pattern for domain engines — expose a `level` parameter that controls aggressiveness:

| Focus | Behavior |
|-------|----------|
| 0 (off) | Transparent — return messages unchanged, expose no tools |
| 1 (soft) | Light awareness — keyword scanning, minimal protection |
| 2 (medium) | Tools active, domain messages protected, context injected |
| 3 (hard) | Maximum protection, full context injection every turn |

Let the user adjust at runtime via a tool (`numogram_focus` in our case) or set default in `context.numogram.focus` in config.yaml.

## Config Structure (actual working config)

```yaml
context:
  engine: numogram          # selects the engine
  numogram:                 # engine-specific config read by on_session_start()
    focus: 3                # 0=off, 1=soft, 2=medium, 3=hard
    active_zone: 9          # starting zone
```

The engine reads its config block from `config.yaml` in `on_session_start()` via PyYAML. Engine-specific settings go under `context.<engine_name>:` — the loader doesn't auto-inject them, you read them yourself.

## Example: Numogram Context Engine (built)

Production implementation at `~/.hermes/plugins/context_engine/numogram/__init__.py` with:
- 4 injected tools: `aq_calc`, `zone_lookup`, `syzygy_find`, `numogram_focus`
- Numogram keyword regex for message relevance scanning
- Focus-adjustable lens (0-3) with `numogram_focus` runtime tool
- Zone context header injection at focus 2+
- Session lifecycle with active zone tracking
- `plugin.yaml` for discovery metadata

Activated in config.yaml:
```yaml
context:
  engine: numogram
  numogram:
    focus: 3
    active_zone: 9
```

## Learnings from Numogram Engine Build (Apr 2026)

- Discovery works immediately after `mkdir` + write `__init__.py` — no restart needed to discover (but config change needs restart to activate)
- `discover_context_engines()` calls `_load_engine_from_dir()` which tries `register()` then falls back to class discovery. Both paths work.
- The `frozenset.pop()` bug hit in TWO places (zone_lookup and _build_zone_context) — fix both when iterating frozensets
- Context injection: inserting a system message into the protected list during `compress()` is the cleanest approach. Don't try to append to the message list outside compression.
- Tools at focus=0 should genuinely return `[]` — the agent's tool list is additive, extra tools consume context every turn
- The `numogram_focus` tool enabling runtime focus adjustment is essential — users want to widen the lens without restarting
