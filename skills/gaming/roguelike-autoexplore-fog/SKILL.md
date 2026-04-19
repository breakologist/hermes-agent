---
name: roguelike-autoexplore-fog
description: "DCSS-style auto-explore, numogram fog-of-war, and conduct system for roguelike agents. BFS exploration, zone-tied vision, constraint-based play."
version: 1.0.0
author: Etym
tags: [roguelike, ai-agent, auto-explore, fog-of-war, conducts, numogram, dcss]
---

# Auto-Explore, Fog of War & Conducts for Roguelike Agents

Use when: building AI-playable roguelikes where the agent needs structured exploration, partial information, and constraint-based challenge modes.

## Auto-Explore (DCSS-Style BFS)

DCSS's auto-explore is the gold standard. BFS from player to nearest unexplored passable tile:

```python
from collections import deque

def auto_explore_step(player_x, player_y, explored, is_passable, width, height):
    """BFS to nearest unexplored passable tile. Returns first step (dx, dy) or None."""
    visited = set()
    queue = deque()
    queue.append((player_x, player_y, []))
    visited.add((player_x, player_y))
    
    while queue:
        x, y, path = queue.popleft()
        if (x, y) not in explored and (x, y) != (player_x, player_y):
            return path[0] if path else (0, 0)
        for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in visited and is_passable(nx, ny):
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [(dx, dy)]))
    return None  # floor complete
```

### Interrupts (stop auto-explore)
- Demon in LOS, gate discovered, zone boundary crossed, HP < 25%, triangular milestone fires, Cryptolith click threshold

### Key Insight
Crawler enters Zone 1 within 8 turns. Our agent stays in Zone 0 for 80+ turns. The difference: the crawler implicitly follows corridors to zone boundaries. Auto-explore makes this explicit.

## Fog of War (Numogram-Tied Vision)

Two sets: `explored` (ever seen, persistent) and `visible` (currently in LOS, transient).

### Zone LOS Ranges
| Zone | Name | LOS | Rationale |
|------|------|-----|-----------|
| 0 | Void | 4 | Oppressive |
| 1 | Stability | 8 | Clear, stable |
| 2 | Separation | 6 | Fog |
| 3 | Warp | 5 | Swirling |
| 4 | Catastrophe | 7 | Ice-clear |
| 5 | Pressure | 6 | Green murk |
| 6 | Abstraction | 9 | Clearest — geometric |
| 7 | Blood | 5 | Red-tinged |
| 8 | Multiplicity | 7 | Lavender depths |
| 9 | Iron Core | 3 | Nearly blind |

### Hyperstition Degrades Vision
- 0-49%: no penalty
- 50-79%: -1
- 80-99%: -2
- 100%: -3

### Gate Revelation
Stepping on '+' reveals 5-tile radius. Demons show only if in visible set.

## Conducts (Numogram-Titled)

**PACIFIST — "The Surge"**: Zero kills. Surge current (8→1).
**SPEEDRUN — "The 253rd Step"**: Complete in <=253 turns. T(22)=253.
**CARTOGRAPHER — "The Complete Graph"**: Visit all 10 zones. C(10,2)=45.
**CRYPTOLITH BEARER — "The Descent"**: Carry Cryptolith + die at 100%.
**ZONE-LOCKED — "The Syzygy"**: Only zones in one syzygy pair (e.g., 4+5, 3+6, 0+9).

## Numogram Design Principles
- Auto-explore follows numogram currents (corridors = currents, zone boundaries = syzygies)
- Fog of war creates feedback: more exploration → more hyp → less vision → need more care
- Conducts are syzygy constraints on the C(10,2)=45 traversal graph

## Interest Model (Cross-Run Curiosity)

BFS should prioritize, not just find nearest. Tiles have novelty scores:

```python
def tile_interest(tile, tx, ty, visits, known_gates, known_zones, cult_zones):
    if tile == '?':
        base = 5.0
        if has_seen_gates_ever: base += 3.0   # cross-run curiosity
        if (tx,ty) in known_zones: base += 8.0 # glimpsed boundary
        if (tx,ty) in known_gates: base += 12.0 # strongest attractor
        return base
    if tile in '.0123456789+':
        base = 1.0 - min(visits * 0.5, 2.0)   # visit decay
        if tile in '0123456789':
            zone = int(tile)
            base += 3.0 if zone not in cult_zones else 0.5
        return base
```

Cross-run knowledge from cult.json: agent remembers THAT gates exist, not WHERE. "I know gates are real. This ? might hide one."

## Debugging Guide — Bugs Found in Practice

### Silent newline (agent never moves)
Headless reads line-by-line. `'p'` without `\n` never processed. Agent reads stale state forever. Fix: always send `'p\n'`.

### BFS oscillation on walls
`?` tile might be a wall. Agent walks toward it, can't enter, BFS retargets same tile. Fix: blacklist unreachable targets, clear at 200 entries.

### Gate-first priority pulls toward walls
Gates from FULL MAP might be behind walls. Agent walks toward unreachable gate for 300 turns. Fix: gate direction as FALLBACK, not primary. Auto-explore interest scoring already prioritizes gates.

### NumogramMap missing fog methods
Game transitions to NumogramMap at 100% hyp. Only DungeonMap had update_explored/update_visible. Fix: add methods to NumogramMap with full-reveal behavior. Use `getattr(game_map, 'ZONE_LOS_RADIUS', {})` fallback.

### Curses display didn't render fog
State dump showed fog working, terminal didn't. Curses rendering loop drew all tiles at full brightness. Fix: three visual states — unexplored (space), explored-dim (A_DIM), visible (full). Demons only render in visible set.

### Cult name not tracking
User changed name with 'n' key but cult.json showed "crawler". Save read env var not player.player_name. Fix: `getattr(player, 'player_name', default)` at save time.

## Pitfalls
- Test BOTH curses and headless — shared code, different bugs
- State dump and curses display are separate renderers — fog needs both
- `getattr(game_map, 'attr', fallback)` when game has multiple map classes
- Headless stdin is line-buffered — every command needs `\n`
- BFS on unexplored tiles can target walls — blacklist or verify passability
- `ZONE_LOS_RADIUS` is a class attribute on DungeonMap — NumogramMap needs getattr fallback
