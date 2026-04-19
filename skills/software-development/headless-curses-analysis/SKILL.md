---
name: headless-curses-analysis
description: Analyze curses-based terminal games non-interactively. Extract game data, simulate runs, and produce analysis without running the game in a real terminal.
version: 1.0.0
author: Hermes
tags: [terminal, curses, roguelike, analysis, simulation]
---

# Headless Curses Analysis

Use when: you need to analyze or discuss a curses-based terminal game but can't run it interactively (no real terminal, delegation context, or headless environment).

## Problem
Curses games require a real PTY to initialize. Running them with `terminal()` or even `pty=true` fails with `cbreak() returned ERR`. You need the game's output/data without interactive play.

## Approach: Extract → Simulate → Analyze

### Step 1: Extract game data structures
Read the source file with `read_file()`. Identify:
- **Data definitions** (constants, dictionaries, lookups) — zone flavors, demon tables, item lists
- **Classes** (Room, Player, Enemy, Map) — what state they carry
- **Generation functions** — how maps/encounters are created
- **Key thresholds** — hyperstition levels, difficulty breakpoints, event triggers

Use `execute_code()` with targeted regex extraction if the file is too large to read fully.

### Step 2: Define game data in simulation
Recreate the essential data structures directly in a simulation script:
```python
# Don't import the game — define its data
SYZYGIES = { ... }
ZONE_FLAVOR = { ... }
CRYPTOLITH_MESSAGES = [ ... ]

def digital_root(n): ...
def generate_floor(seed): ...
```

This avoids import chain issues (curses dependencies, missing modules, incomplete __init__).

### Step 3: Simulate runs
Generate several runs with different seeds:
```python
for seed in [6025, 42391, 1776]:
    rooms = generate_floor(seed)
    start_zone = digital_root(seed)
    demon_pair = syzygy_pairs[seed % len(syzygy_pairs)]
    # ... track zone frequency, demon distribution, etc.
```

Key things to simulate:
- **Seed → zone mapping** (digital root of seed = entry zone)
- **Room generation** (how many rooms, which zones appear, total area)
- **Encounter distribution** (which demons appear, frequency analysis)
- **Threshold proximity** (how close does the player get to phase transitions?)
- **Cross-run patterns** (what's consistent? what varies?)

### Step 4: Analyze with voices or structured output
Feed the simulation results to analysis — either structured (tables, frequency counts) or creative (four-voice tetralogue, design critique, improvement proposals).

## What to extract from the source

| System | What to look for |
|--------|-----------------|
| Map generation | Room count ranges, density values, zone assignment logic |
| Encounters | Demon tables, spawn conditions, probability weights |
| Progression | Thresholds, milestones, unlock conditions |
| Persistence | Save files, cult/session data, what carries between runs |
| UI text | Flavor text, messages, corruption effects, lore fragments |
| Player stats | HP, damage, speed, inventory, special abilities |

## Pitfalls

- **Don't exec() the full game file** — it will fail on curses imports. Either strip the curses parts or define data manually.
- **Seed-dependent vs accumulated values** — check whether a value (like hyperstition starting level) is set at generation time or accumulated during play. Simulation only captures generation-time state.
- **Density ≠ probability** — a zone with density 0.8 doesn't mean 80% chance of appearing. It means more rooms when it does appear. Check the actual exclusion logic.
- **Import chain issues** — games often have circular imports or missing dependencies. Manual data definition is more reliable than partial imports.

## Running Curses Games via PTY (when simulation isn't enough)

If you need to actually play the game (not just simulate), use PTY mode:

```python
# Terminal launch — requires TERM env var
terminal(command="cd /path/to/game && TERM=xterm-256color python3 game.py", 
         pty=True, background=True)
```

**Critical gotcha:** Curses games crash with `setupterm: could not find terminal` if `TERM` is not set. Always prefix the command with `TERM=xterm-256color`. This applies to any sandboxed/non-standard environment (Docker, SSH, subagents).

**Interaction pattern:**
1. Launch with `pty=True, background=True` to get a `session_id`
2. Send input with `process(action="write", data="key", session_id=...)` 
3. Check output with `process(action="poll", session_id=...)`
4. Use `process(action="log")` for full output history

## Pitfalls (continued)

- **TERM not set in sandbox environments** — curses `initscr()` calls `setupterm()` which reads `$TERM`. Without it: `cbreak() returned ERR` or `setupterm: could not find terminal`. Fix: prefix command with `TERM=xterm-256color`.
- **Simulated data can be wrong** — the Abyssal Crawler simulation showed Zone 0 (Void) never generates, but real play data (30+ runs) showed Zone 0 appears in 100% of runs. Simulation captures generation-time structure but may miss runtime behavior. Always validate simulated findings against real play data before drawing conclusions.

## When NOT to use this

- If you CAN run the game interactively (real terminal, PTY mode works), play it instead
- If the game has a replay/demo mode, use that
- If the game outputs to stdout (not curses), just run it normally
