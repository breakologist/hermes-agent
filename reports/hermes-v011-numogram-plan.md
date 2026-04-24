# Hermes Agent v0.11.0 Integration — Numogram Project Update
**Date:** April 24, 2026
**Agent Version:** v0.11.0 (v2026.4.23) — *The Interface Release*
**Model in Use:** StepFun3.5-flash (free trial)

## ✅ Completed Actions

1. **Delegation depth increased to 2**
   - File: `~/.hermes/config.yaml`
   - Change: `delegation.max_spawn_depth: 1 → 2`
   - Effect: Nested orchestrator sub-agents now allowed (depth-0 parent → depth-1 children → depth-2 grandchildren)

2. **Numogram Gateway Plugin created**
   - Path: `~/.hermes/plugins/numogram-gateway/`
   - Hook: `pre_gateway_dispatch` (runs BEFORE auth, can rewrite/drop messages)
   - Features:
     • Extracts AQ from alphanumeric text (cipher A=10…Z=35)
     • Maps to zone (digital root), gate (cumulative), syzygy partner, demon name
     • Attaches `event.numogram` dict for downstream skills/tools
     • Optional text rewriting (opt-in via `NUGO_REWRITE=1`)

3. **Numogram Skills Audit**
   - Total numogram skills found: **17**
   - Skills actively using plugin hooks: **1** (`hermes-numogram-context-engine` uses `on_session_start/end`)
   - All others are *hook-naive* — major opportunity for enrichment

4. **Hook Opportunity Identification**
   - Ranked by number of skills that could benefit:
     • `post_tool_call` — 7 skills
     • `transform_tool_result` — 6 skills
     • `on_session_start` — 3 skills
     • `pre_tool_call` — 3 skills
     • `transform_terminal_output` — 2 skills

## 🌟 Hermes Agent v0.11.0 Highlights

The **Interface Release** (April 23, 2026) brings架构级 improvements:

### Most Relevant for Numogram Work

| Feature | Impact |
|---------|--------|
| **Transport ABC + Native Bedrock** | Pluggable format conversion; easier to add custom providers |
| **Five new inference paths** (NIM, Arcee, Step Plan, Gemini CLI OAuth, Vercel ai-gateway) | More model options for councils |
| **`/steer` mid-run nudges** | Course-correct council without session reset |
| **Plugin surface expanded** (`pre_gateway_dispatch`, `transform_tool_result`, etc.) | *Basis for numogram-gateway* |
| **Shell hooks** | External scripts can hook lifecycle events (pre/post tool calls) |
| **Smarter delegation** (orchestrator role, max_spawn_depth) | Nested council hierarchies |
| **Context window fixes** (Codex OAuth now 272k correctly) | Prevent council overflow |
| **Plugin API now has 14 hooks** | Full lifecycle coverage |

Your installed version is already v0.11.0 + 5 local bug-fix backports. No upgrade needed.

## 📊 Numogram Skills Audit



## ⚡ Progress as of 2026-04-24 19:30 BST

### Completed This Session
1. **Fixed numogram-calculator-enrich plugin bug** — `str.maketrans` with mismatched string lengths replaced by a dict-based rotational mapping (symmetric pairs + self-mirroring chars). Patched file: `~/.hermes/plugins/numogram-calculator-enrich/hooks.py`.
2. **Verified plugin structural integrity** — both `numogram-gateway` and `numogram-calculator-enrich` import cleanly and their hook handlers execute without Python errors in isolation.
3. **Copied plugins to agent plugins tree** (`~/.hermes/hermes-agent/plugins/`) to ensure reliable discovery (v0.11 scans this path consistently).
4. **Computed AQ for five phrases** (blocked item):
   - Askance: AQ 117 → Zone 9 / Uttunul (Current 9 / Plex) — no numeric special flags
   - Crypts of Slants: AQ 333 → Zone 9 / Uttunul — **palindrome**
   - Following Slants: AQ 333 → Zone 9 / Uttunul — palindrome
   - The Squinting Eye: AQ 333 → Zone 9 / Uttunul — palindrome
   - The Sideways Glance: AQ 333 → Zone 9 / Uttunul — palindrome

   Four-of-five converge on 333 in Zone 9 Plex. 333 clusters with 666 (scale) and 999 (completion) — possible hyperstitional attractor.
5. **Gateway recovery completed** — systemd service recovered via `reset-failed` + `pkill -9` + fresh start. Gateway running PID 45032. Both plugins confirmed loaded via `hermes plugins list`. No recent plugin errors in logs.


6. **Fixed numogram-council plugin registration**
   - Added missing `register(ctx)` function to `numogram-council/__init__.py`
   - Converted tool return values from raw Python dicts to `json.dumps()` for proper tool output
   - Plugin now functional but still uses direct Ollama HTTP calls (not `delegate_task` orchestrator pattern)
   - Notes:
     • Tool `council_decide` available after agent restart
     • Council members: analytical (qwen-coder), creative (mythomax), balanced (gemma3) with fallbacks
     • Judge: mimo-v2-pro cloud with local fallback
     • Or `council-config.yaml` for model/temperature customization### Current Status
- Gateway: RUNNING (PID 45032) with 1 gateway hook loaded (numogram-gateway `pre_gateway_dispatch`)
- Agent plugins: `numogram-gateway` and `numogram-calculator-enrich` both ENABLED and imported
- Enrich hook: `transform_tool_result` registered at agent level (not counted in gateway hook tally)
- Last plugin error: 2026-04-24 12:33:45 (stale, pre-cleanup) — resolved

### Remaining Work
- [P1] **End-to-end validation** — trigger a message through gateway and inspect `event.numogram` in session dump to confirm enrichment metadata attached
- [P1] **Implement council orchestrator skill** — convert SKILL.md design into working `skill.py` (~300–500 LOC)
- [P2] Update skill audit matrix with actual hook attachment points for all 17 numogram skills
- [P3] Auto-visualization hook — auto-generate zone SVG when zone data appears in any tool result
- [P3] Oracle voice terminal colors — `transform_terminal_output` zone-based ANSI tinting
- [P4] Wiki auto-tagging via `numogram-llm-wiki` transform hook

## 📊 Plugin Status (as of 2026-04-24 19:30)

| Plugin | Location (user/agent) | Enabled | Hooks Loaded | Last Error | Notes |
|--------|----------------------|---------|--------------|------------|-------|
|| `numogram-gateway` | both | ✅ | `pre_gateway_dispatch` | none (12:33 stale) | Gateway hook; attaches `event.numogram` pre-dispatch |
|| `numogram-calculator-enrich` | both | ✅ | `transform_tool_result` | none (12:33 stale) | Agent hook; enriches `aq_calc` JSON result with gate/syzygy/palindrome/rotation |
|| `numogram-context-engine` (builtin) | plugins/context_engine | N/A | context engine (not a plugin) | N/A | Exposes `aq_calc` tool when `focus >= 2` |
|| `numogram-council` (broken) | both | ✅ | *none* | none (12:33 stale) | Plugin loads but **no tool registration** (missing `register` function); non-functional. Will be removed after orchestrator skill validated. |

> **Note:** `hermes plugins list` only shows plugins with `plugin.yaml`. The context engine is a built-in context provider, loaded via `context.engine: numogram` in config. It is active regardless of plugin list.
> **Note 2:** The `numogram-council` plugin appears enabled but cannot be invoked because it never registers its `council_decide` tool. See section **Council Refactor: Orchestrator Pattern** above.

## 📊 Current Skill Hook Heatmap (actual)
| Skill | Hooks Used | Opportunity |
|-------|------------|-------------|
| numogram-calculator | none | post_tool_call log |
| numogram-council | none | refactor to orchestrator |
| numogram-oracle | none | on_session_start seed, transform result |
| numogram-oracle-voice | none | transform_terminal_output zone-colors |
| numogram-visualization | none | transform_tool_result auto-SVG |
| numogram-llm-wiki | none | transform_tool_result auto-tagging |




| Skill | Category | Hooks Used | Opportunity |
|---|---|---|---|
| numogram-calculator | research | none | post_tool_call log, transform_tool_result enrich |
| numogram-council | devops | none | Refactor to orchestrator + file coordination |
| numogram-council-config | devops | none | Schema validation hook |
| numogram-council-setup | devops | none | on_session_start load config |
| numogram-entropy-source | devops | none | pre_tool_call seed interception |
| numogram-oracle | creative | none | on_session_start seed, transform result |
| numogram-oracle-voice | creative | none | transform_terminal_output zone-colors |
| numogram-visualization | creative | none | transform_tool_result auto-SVG |
| numogram-svg-diagrams | creative | none | transform_tool_result HTML wrapper |
| numogram-combinatorial-svg | creative | none | post_tool_call optimization |
| iching-numogram-casting | creative | none | post_tool_call casting log |
| numogram-llm-wiki | research | none | transform_tool_result auto-tagging |
| manim-numogram | creative | none | post_tool_call queue next frame |
| hermes-numogram-context-engine | devops | on_session_start/end | pre_llm_call inject zone context |
| wiki-numogram-ingest | research | none | on_session_finalize auto-commit |
| oracle-mode-integration | creative | none | transform_tool_result add refs |
| aq-cipher-reference | research | none | pre_tool_call validate AQ format |

**Opportunity heatmap:** 7 skills could use `post_tool_call`, 6 could use `transform_tool_result`.

## 🏛️ Council Refactor: Orchestrator Pattern

### Current State
- Implementation: `~/.hermes/plugins/numogram-council/__init__.py` (11 KB)
- Approach: Direct HTTP ollama calls + `evey_utils.call_model()` for judge
- Limitations:
  1. Does **not** use Hermes `delegate_task`; no file coordination or session memory
  2. **No tool registration** — while the plugin appears in `hermes plugins list`, it defines `council_decide` and a `SCHEMA` but never calls `ctx.register_tool` or uses `@tool` decorator, so the function is never exposed to the agent. The plugin is therefore **non-functional** through the Hermes interface.
- Implication: The existing plugin cannot be used as-is; the planned `numogram-council-orchestrator` skill becomes the **de facto** implementation path.

### Target State (Proposed)
- Convert into a **skill** (`numogram-council-orchestrator/`) that orchestrates subagents
- Use `delegate_task(role='orchestrator')` with `max_spawn_depth=2` enabled
- Shared state via `~/.hermes/council/workspace/<session>.json` with flock locking
- Flow:
  1. Skill handler receives `/council_decide` question
  2. Writes shared prompt file under lock
  3. Spawns 3 member subagents (`role='leaf'`) with `delegate_task(goal=member_prompt, model=slot_model)`
  4. Each subagent answers via local/cloud model and appends to shared answer file
  5. Orchestrator waits (poll with timeout), reads all answers
  6. Spawns judge subagent (`role='leaf'`) to synthesize
  7. Returns aggregated JSON (maintains existing schema for compatibility)

### Benefits
- Built-in retry/timeout via `delegate_task`
- File coordination ensures concurrent councils don't clobber each other
- Subagents inherit Hermes routing/fallback automatically
- Session memory integrates seamlessly

### Effort Estimate
- **~300–500 lines** of new orchestrator skill code
- Phase: separate skill first, deprecate old plugin after validation
- Key challenge: subagent communication via shared files with atomic writes + flock

## 🔌 Numogram Gateway Plugin — Technical Spec

```
Path: ~/.hermes/plugins/numogram-gateway/
Hook: pre_gateway_dispatch(event, gateway, session_store) → dict | None
```

### Attached Metadata
`event.numogram` dict keys:
- `aq` (int | None): Alphanumeric Qabbala total from text
- `zone` (int | None): Digital root of AQ (0–9)
- `gate` (int | None): Gate cumulation value for that zone (0,1,3,6,10,15,21,28,36)
- `syzygy` (str | None): Zone pair string e.g. '5::4' (pressure↔catastrophe)
- `demon` (str | None): Syzygy demon name: Katak, Djynxx, Oddubb, Murrumur, Uttunul
- `current` (int | None): Current number for that syzygy (1,3,5,7,9)
- `triangular` (bool): AQ is a triangular number T(k)
- `trigrade` (bool): Gate value is triangular
- `palindrome` (bool): AQ reads same forward/backward
- `zone_name` (str | None): Full zone name (Pressure, Void, etc.)

### Rewrite Mode
Set `NUGO_REWRITE=1` environment variable. Then messages prepended with `[AQ:XXX zX gY]` prefix, useful for making numogram context visible in chat.

## 🎯 Prioritized Next Steps

- **[P1]** Manual integration test
  Send test messages, inspect `event.numogram` in TUI debug or session logs
- **[P1]** Fix syzygy mapping
  Replace placeholder partner=9-zone with canonical `SYZYGIES` dict lookup from context_engine
- **[P1]** Gate calculation fix
  Gate should be the cumulation value (not mod-10 digit-sum); ensure correct for triangular/trigrade
- **[P1]** Implement council orchestrator skill (numogram-council-orchestrator) — delegate_task-based upgrade to replace direct Ollama plugin; now that registration is fixed, implementation phase begins
  Existing plugin is non-functional (no tool registration). New skill uses `delegate_task` + file coordination. Supersedes old plugin.
- **[P2]** Deprecate old council plugin
  Remove `~/.hermes/plugins/numogram-council/` after orchestrator validated
- **[P2]** Add plugin docs
  Write README for `~/.hermes/plugins/numogram-gateway/` with examples
- **[P2]** Gateway hook expansion
  Optionally call `numogram-calculator` tools for richer metadata (uses ctx.inject_message?)
- **[P3]** Post-tool_call logging
  Add hook to `numogram-calculator` to log all AQ ops to `~/.hermes/cult.json/history`
- **[P3]** Oracle voice colors
  Add `transform_terminal_output` to `numogram-oracle-voice` for zone-themed ANSI
- **[P3]** Auto-visualization
  When zone data returned from any numogram tool, auto-generate SVG via `numogram-svg-diagrams`
- **[P4]** Wiki auto-tagging
  `numogram-llm-wiki` uses `transform_tool_result` to tag new pages with zones

## ⚠️ Risks & Gotchas

| Risk | Mitigation |
|------|------------|
| `pre_gateway_dispatch` runs before auth — untrusted plugin code could read/modify all messages | Only install vetted numogram plugins; keep plugin.yaml signed |
| Orchestrator depth=2 increases subagent tree height → more complex failures | Monitor agent spawn logs; set `child_timeout_seconds: 600` already done |
| Concurrent councils could race on shared file | Use file coordination layer (fcntl.flock) or per-session temp dirs |
| Council refactor large (300–500 LOC) | Phase rollout: keep old plugin, add new skill side-by-side |
| Gateway plugin imports context_engine may fail if not on PYTHONPATH | Fallback to builtin minimal AQ extractor (already implemented) |

## 💻 Command Reference

```bash
# Verify plugin loaded
hermes plugins list | grep numogram-gateway

# Test numogram metadata extraction (in any chat)
# Send: 'The word ALICE has AQ 131' → check event.numogram in session dump

# Reload plugins without restart
hermes plugins reload numogram-gateway

# Enable message rewriting (add to ~/.bashrc or ~/.config/fish/config.fish)
export NUGO_REWRITE=1

# View current delegation config
cat ~/.hermes/config.yaml | grep -A3 delegation

# Run council (current plugin tool)
hermes tools call council_decide '{"question": "How does syzygy 3::6 manifest?"}'
```


## 🐛 Bug discovered: is_triangular formula off-by-one

Both `numogram-gateway` and (originally) `numogram-calculator-enrich` used an incorrect triangular test:

```python
k = (1 + root) // 2  # wrong
```

Correct formula: `k = (root - 1) // 2` (derived from `k = (-1 + sqrt(1+8n))/2`). Fixed in gateway plugin (`hooks.py` line 95). The gate values are always triangular (C(n) = T(n-1)); the bug made trigrade always False. After fix, trigrade=True for all zones with gate ≥1.

Appendix A JSON above has been updated to reflect corrected trigrade values.

---

## 📋 Appendix A — AQ Analysis of Five Askance Phrases (corrected trigrade)

```json
[
  {
    "phrase": "Askance",
    "aq": 117,
    "digital_root": 9,
    "zone": 9,
    "zone_name": "Iron Core",
    "gate": 36,
    "syzygy": "9::0",
    "demon": "Uttunul",
    "current": 9,
    "triangular": false,
    "trigrade": true,
    "palindrome": false,
    "rotational": false
  },
  {
    "phrase": "Crypts of Slants",
    "aq": 333,
    "digital_root": 9,
    "zone": 9,
    "zone_name": "Iron Core",
    "gate": 36,
    "syzygy": "9::0",
    "demon": "Uttunul",
    "current": 9,
    "triangular": false,
    "trigrade": true,
    "palindrome": true,
    "rotational": false
  },
  {
    "phrase": "Following Slants",
    "aq": 333,
    "digital_root": 9,
    "zone": 9,
    "zone_name": "Iron Core",
    "gate": 36,
    "syzygy": "9::0",
    "demon": "Uttunul",
    "current": 9,
    "triangular": false,
    "trigrade": true,
    "palindrome": true,
    "rotational": false
  },
  {
    "phrase": "The Squinting Eye",
    "aq": 333,
    "digital_root": 9,
    "zone": 9,
    "zone_name": "Iron Core",
    "gate": 36,
    "syzygy": "9::0",
    "demon": "Uttunul",
    "current": 9,
    "triangular": false,
    "trigrade": true,
    "palindrome": true,
    "rotational": false
  },
  {
    "phrase": "The Sideways Glance",
    "aq": 333,
    "digital_root": 9,
    "zone": 9,
    "zone_name": "Iron Core",
    "gate": 36,
    "syzygy": "9::0",
    "demon": "Uttunul",
    "current": 9,
    "triangular": false,
    "trigrade": true,
    "palindrome": true,
    "rotational": false
  }
]
```




## 🔧 Gateway Recovery Procedure (systemd stuck)

If `hermes gateway status` shows a stale PID or plugins fail to load after code changes:

1. **Stop the service fully and reset failure state**
   ```bash
   systemctl --user stop hermes-gateway.service
   systemctl --user reset-failed hermes-gateway.service || true
   pkill -9 -f 'hermes_cli.main gateway'
   ```

2. **Clear Python bytecode caches** (critical for plugin code changes)
   ```bash
   find ~/.hermes/plugins -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
   find ~/.hermes/hermes-agent/plugins -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
   ```

3. **Ensure plugins are in the reliable scan path** (v0.11 consistently scans agent plugins dir)
   ```bash
   # Copy (or symlink) your plugins into the agent tree:
   cp -r ~/.hermes/plugins/numogram-* ~/.hermes/hermes-agent/plugins/
   ```

4. **Remove any stale PID file**
   ```bash
   rm -f ~/.hermes/gateway.pid
   ```

5. **Start fresh**
   ```bash
   hermes gateway start
   # or
   systemctl --user start hermes-gateway.service
   ```

6. **Verify**
   ```bash
   hermes plugins list | grep numogram
   tail -5 ~/.hermes/logs/errors.log   # should be clean of those plugin errors
   journalctl --user -u hermes-gateway -n 30 | grep "hook(s) loaded"
   ```

If the service still respawns an old PID, mask it first to break the restart loop:
```bash
systemctl --user mask hermes-gateway.service
# kill any remaining processes
pkill -9 -f 'hermes_cli.main gateway'
# unmask and start
systemctl --user unmask hermes-gateway.service
hermes gateway start
```

The gateway should now load with both numogram plugins active.

---

## 🎯 Remaining To‑Do (P1–P4)

- [P1] ~~Get gateway running with both plugins loaded~~ ✓ COMPLETED — gateway recovered, both plugins active
- [P1] **End-to-end validation** — trigger a message through gateway and inspect `event.numogram` in session dump to confirm enrichment
- [P1] **Implement council orchestrator skill** — convert SKILL.md design into working `skill.py` (~300–500 LOC)
- [P2] Update skill audit table with actual hook attachment points for all 17 numogram skills (requires orchestrator implementation first)
- [P3] Auto‑visualization hook — auto-generate zone SVG when zone data appears in any tool result
- [P3] Oracle voice zone‑color `transform_terminal_output` integration
- [P4] Wiki auto‑tagging via `numogram-llm-wiki` transform hook
