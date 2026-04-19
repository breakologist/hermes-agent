---
name: roguelike-auto-explore
category: gaming
description: DCSS-style auto-explore with interest-driven exploration for roguelike AI agents
triggers: ["auto-explore", "fog of war", "BFS pathfinding", "agent movement", "unexplored tiles", "interest model", "novelty scoring", "cross-run learning"]
---

# Roguelike Auto-Explore (DCSS-style + Interest Model)

## Three-Layer Implementation

### 1. Game Engine (explored tracking)
- `DungeonMap.explored` set: `(x,y)` tuples of tiles player has ever seen
- `update_explored(px, py, radius=6)`: circular LOS, marks passable tiles explored
- Call on: player movement, initial spawn
- LOS radius is the fog-of-war knob (future: zone-tied, hyp-degraded)

### 2. State Dump (explored/unexplored distinction)
- **FULL MAP**: unchanged, shows everything (backward compatible)
- **EXPLORED MAP**: new section, shows `?` for unexplored tiles
- Agent parses EXPLORED MAP preferentially, falls back to FULL MAP
- Gates visible even in unexplored areas (they glow)

### 3. Agent (Interest-Driven BFS)

The agent doesn't just find the nearest `?` — it scores every reachable `?` by interest and picks the most attractive one.

## tile_interest() — Novelty Scoring

```python
def tile_interest(tx, ty, rows, state):
    tile = rows[ty][tx]
    visits = visit_count.get((tx, ty), 0)  # how many times agent stood here

    if tile == '?':           # Mystery — unknown
        base = 5.0
        if _has_seen_gates_ever:  base += 3.0   # Cross-run: "gates exist, this might hide one"
        if (tx,ty) in known_zones: base += 8.0  # Within-run: glimpsed zone boundary
        if (tx,ty) in known_gates: base += 12.0 # Within-run: glimpsed gate (strongest)
        if (tx,ty) in demon_kills: base += 3.0  # Blood remembers
        if (tx,ty) in _blacklist:  return -999  # Tried and failed

    if tile in '.0123456789+':  # Known passable
        base = 1.0 - min(visits * 0.5, 2.0)  # Visit decay
        if tile == '+':     base += 2.0        # Gate
        if tile in '0123456789':
            if zone_num in _cult_zones: base += 0.5   # Conquered in past
            else:                       base += 3.0   # New zone — attractor
```

## Interest Hierarchy (highest to lowest)

| State | Score | Meaning |
|-------|-------|---------|
| KNOWN-UNKNOWN (glimpsed gate) | 17+ | Strongest attractor — agent SAW it, wants it |
| KNOWN-UNKNOWN (glimpsed zone) | 13+ | Strong — agent glimpsed a new zone |
| CROSS-RUN CURIOSITY (any ?) | 8+ | Agent knows gates/zones exist from cult.json |
| MYSTERY (?) | 5.0 | Unknown — attracts by default |
| NEW ZONE BOUNDARY | 4.0 | Zone number agent hasn't visited in past runs |
| DEMON KILL SITE | 3.0 | Blood remembers |
| GATE (explored) | 3.0 | Already here, mild interest |
| VISITED FLOOR | 1.0 - decay | Boring with repetition |
| WALL | -999 | Impassable |

## Cross-Run Knowledge (cult.json)

```python
# Load at agent start — agent remembers from PAST runs
with open('cult.json') as f:
    cult = json.load(f)
_has_seen_gates_ever = len(cult.get('gates_ever_opened', [])) > 0
_cult_zones = cult.get('zones_ever_visited', [])
```

The agent carries forward the **concept** of gates, not specific coordinates.
"I know gates exist. I will explore until I find one." — motivation, not memory.

## BFS with Priority

Complete BFS (don't stop at first-found). Score every reachable `?` by `tile_interest()`. Pick highest-priority target. Zone-boundary-adjacent `?` > gate-adjacent `?` > normal `?`.

## Blacklist (Anti-Oscillation)

```python
_auto_explore_blacklist = set()

# After picking target:
_blacklist.add(target)
if len(_blacklist) > 200:
    _blacklist.clear()  # Periodic reset

# In BFS: skip blacklisted tiles
if (nx, ny) in _blacklist:
    continue
```

Without this, agent oscillates when BFS targets a `?` that's actually a wall it can never enter.

## Decision Hierarchy

1. FLEE: HP < 25% + demon nearby → flee
2. FIGHT: demon adjacent + HP > 50% → attack
3. EXPLORE: interest-driven BFS → walk toward most interesting `?`
4. GATE: fallback when fully explored → walk toward known gate
5. RANDOM: last resort

**Gate direction is FALLBACK, not primary.** Gates on the full map may be behind walls. Pulling agent toward gates before it can reach them wastes turns.

## Pitfalls (learned the hard way)

1. **Headless newline bug**: `proc.stdin.write('p')` WITHOUT `\n` — headless reads line-by-line (`for line in sys.stdin`). Input never processed. Always: `proc.stdin.write('p\n')`

2. **Oscillation on walls**: BFS targets nearest `?`, but it's a wall. Agent walks there, can't enter, BFS retargets same `?`. Fix: blacklist.

3. **Gate-first priority fails**: Agent sees gate on full map behind wall, walks toward wall forever. Fix: gate as fallback, not primary.

4. **BFS early exit**: First-found `?` is suboptimal. Complete BFS finds zone-boundary-adjacent `?` which is higher value. Don't `break` at first find.

5. **Stale state**: Agent dumps state every 20 turns, BFS runs on 20-turn-old data. Fix: dump state after EVERY move.

6. **State dump race**: Agent sends `p`, game dumps to file, agent reads file. If timing is off, agent reads stale file. Sleep(0.05) between dump and read.

## DFS Commitment — Tree Traversal (BREAKTHROUGH — April 16)

The agent oscillates between corridor entrances because it re-evaluates every turn. The fix: **commit to a target and don't change until reached or blocked.**

The dungeon is a TREE (from Brogue room accretion algorithm). Doors are forks. Corridors are branches. Follow branches to endpoints. This is depth-first traversal, not breadth-first wandering.

```python
# At TOP of _decide (before flee/fight — override everything except critical HP):
if self.committed_target and pct > 0.2:
    tx, ty = self.committed_target
    dist = abs(tx-px) + abs(ty-py)
    if dist == 0:
        # Keep running in same direction (prevent oscillation)
        if self.last_action and self.last_action.upper() in ('L','H','J','K'):
            return self.last_action
        self.committed_target = None
    elif self.committed_steps > 60:
        self.committed_target = None  # branch exhausted
    else:
        self.committed_steps += 1
        return self._move(tx-px, ty-py, screen, run=True)
```

**When to commit:**
- Entering a corridor → commit to nearest unvisited endpoint
- Pursuing stairs → commit to farthest unvisited endpoint (stairs hide in dead ends)
- Walking toward a door → commit to the door

**When commitment clears:**
- Target reached (dist == 0, then keep running to prevent oscillation)
- Branch exhausted (60+ steps)
- Blocked (distance increases — hit wall)

**Results:** v1-v12 oscillated 2 positions. v13 with DFS commitment explored 216 floors (near-complete level 1).

## Corridor Entities — Structures, Not Tiles

Don't treat corridors as individual tiles. Detect connected corridor structures and treat them as entities with endpoints.

```python
def _detect_corridors(self, screen):
    all_corridors = self.known_corridors | (screen.corridors if screen else set())
    all_floors = self.known_floors | (screen.floors if screen else set())
    all_doors = self.known_doors | (screen.doors if screen else set())
    
    visited = set()
    self.corridors = []
    
    for tile in all_corridors:
        if tile in visited: continue
        corr_tiles = set(); queue = [tile]
        while queue:
            cx, cy = queue.pop()
            if (cx,cy) in visited or (cx,cy) not in all_corridors: continue
            visited.add((cx,cy)); corr_tiles.add((cx,cy))
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                if (cx+dx,cy+dy) in all_corridors and (cx+dx,cy+dy) not in visited:
                    queue.append((cx+dx,cy+dy))
        
        if len(corr_tiles) < 2: continue
        endpoints = set()
        for (cx,cy) in corr_tiles:
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                if (cx+dx,cy+dy) in all_floors or (cx+dx,cy+dy) in all_doors:
                    endpoints.add((cx+dx,cy+dy))
        
        self.corridors.append({'tiles': corr_tiles, 'endpoints': endpoints, 'length': len(corr_tiles)})
```

**Usage:** When in a corridor, walk toward unvisited endpoints (room entrances). Endpoints are the bridges to undiscovered rooms.

## Exponential Visit Decay (April 16)

Tiles die exponentially. Agent forced to find new territory.

```python
v = self.vcount.get((x,y), 1)
sc = -2.0 - v*v*0.5  # v=1:-2.5, v=2:-4, v=3:-6.5, v=4:-10, v=5:-14.5
```

Linear decay (1.0 - v×0.3) is too gentle. Exponential decay forces the agent to leave heavily-visited areas.

## Syzygy Riding for Oscillation

When agent oscillates between 2-3 positions, it's trapped in a syzygy pair. Don't break it — ride it outward.

```python
from collections import Counter
pos_counts = Counter(recent_positions[-12:])
if len(pos_counts) <= 3:
    # Syzygy detected — ride dominant axis
    xs = [p[0] for p in pos_counts.keys()]
    ys = [p[1] for p in pos_counts.keys()]
    if max(xs)-min(xs) > max(ys)-min(ys):
        return random.choice(['L','H'])  # horizontal
    else:
        return random.choice(['J','K'])  # vertical
```

## Oblique Strategies for Stagnation

When at same position 8+ of last 12 turns:

```python
most_common_pos, count = pos_counts.most_common(1)[0]
if count >= 8:
    strategies = ['s', '.', random.choice(['L','H','J','K'])]
    return random.choice(strategies)
```

Numogrammatic version of Eno's "Honor thy error as hidden intention."

## Cross-Run Stair Knowledge

Agent knows stairs exist from ANY previous run. Actively seeks them.

```python
self.memory['knows_stairs'] = True  # always remember

if self.memory.get('knows_stairs') and not self.known_stairs:
    for corr in self.corridors:
        for ep in corr.get('endpoints', []):
            if ep not in self.visited:
                self.committed_target = ep  # stairs might be there
                return self._move(ep[0]-px, ep[1]-py, screen, run=True)
```

## HP Management — Don't Fight When Hurt

```python
# Flee: below 40%, dangerous monsters below 55%
# Fight: only above 60%
# Rest: below 40% when safe, always below 30%

if pct < 0.4 and not screen.monsters:
    return '.'  # rest
if pct > 0.6:
    for mpx,mpy,ch in screen.monsters:
        if screen.adj(screen.pos, (mpx,mpy)):
            return self._move(mpx-px, mpy-py, screen, run=False)
```

## Running as Default (April 15)

Capital letters (H/J/K/L) run until hitting obstacle. Running passes through doors. Walking stops on them. Default to running for all non-combat movement.

```python
# Default: running (capital)
# Fights/flee: walking (lowercase)
# Rest: '.' only when HP < 30%
```

## Angband-Specific (April 16)

Angband works with `-mgcu` (text mode). Floor is `·` (middle dot), not `.`.
Parser: `FLOOR = set('.·§')` — handles both · and § (some terminals render differently).

ESC pitfall: sending ESC every turn may OPEN menus. Only send when dialogs detected.

Display: map left ~66 columns, sidebar right, status bar bottom.
- Zone-tied LOS radii: {0:4, 1:8, 2:6, 3:5, 4:7, 5:6, 6:9, 7:5, 8:7, 9:3}
- Hyperstition degrades vision: 50%+: -1, 80%+: -2, 100%+: -3, min 2
- `visible` set separate from `explored` — current vs historical knowledge
- `update_visible(px, py, zone, hyperstition)` — called on every move
- `reveal_burst(cx, cy, radius)` — gates 5 tiles, demon kills 3 tiles
- State dump: VISIBLE MAP section, demons filtered by visible set

### Curses Terminal Rendering (three visual states)
The fog of war must be rendered in the curses display, not just the state dump.
Without this, the terminal shows everything at full brightness and the user
can't see the fog at all.

Three states:
```python
in_visible = (mx, my) in game_map.visible
in_explored = (mx, my) in game_map.explored

if not in_explored:
    # Unexplored: dark void
    stdscr.addch(sy+2, sx, ord(' '), curses.color_pair(0))
elif in_visible:
    # Currently in LOS: full brightness
    stdscr.addch(sy+2, sx, ch, attr)
else:
    # Explored but not in LOS: dim
    stdscr.addch(sy+2, sx, ch, attr | curses.A_DIM)
```

Demons only render when `in_visible` — hidden demons don't show.
Gates show everywhere but are dim when not in LOS.

HUD should show LOS: `LOS:{vis_eff}({vis_tiles})` — radius + visible tile count.

### NumogramMap Compatibility (CRITICAL)
If game has multiple map classes (e.g., DungeonMap for normal play, NumogramMap for 100% hyp reveal), **ALL map classes must implement the fog-of-war interface**:
- `explored` set
- `visible` set
- `update_explored(px, py, radius)`
- `update_visible(px, py, zone, hyperstition)`
- `reveal_burst(cx, cy, radius)`

NumogramMap at 100% hyp can use full-reveal versions (everything visible). Without this, `AttributeError` crash on first move after map transition.

### Cult Name Tracking
Player name from 'n' key or `NUMOGRAM_PLAYER` env var. At save time, use `getattr(player, 'player_name', env_default)` — NOT `os.environ.get()` directly. Otherwise in-game name changes are lost.

### Demo Key Name Fix
Curses arrow keys (KEY_UP=259, KEY_DOWN=258, KEY_LEFT=260, KEY_RIGHT=261) get recorded as hex (0x104, 0x106) if you just do `chr(key) if 32<=key<127 else f"0x{key:x}"`. Use a lookup dict:
```python
_CURSES_KEY_NAMES = {258:"DOWN", 259:"UP", 260:"LEFT", 261:"RIGHT", ...}
def _demo_key_name(key):
    if key in _CURSES_KEY_NAMES: return _CURSES_KEY_NAMES[key]
    if 32 <= key < 127: return chr(key)
    return f"0x{key:x}"
```

### Headless Demo Recording
Headless mode should auto-record demos (start at game init, stop at quit/death/EOF). Player methods (move, attack) already call `demo.record_event()` — shared between modes. Only need to wire up `demo.start(player_name)` and `demo.stop()` at exit points.