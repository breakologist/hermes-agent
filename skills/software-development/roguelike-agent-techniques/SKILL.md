---
name: roguelike-agent-techniques
description: Techniques for building AI agents that play roguelikes and other games. Covers exploration strategies, state parsing, curiosity-driven navigation, cross-run memory, conduct systems, and LLM hybrid planning.
version: 1.11.0
author: Etym
tags: [roguelike, ai-agent, game-playing, exploration, curiosity, LLM, BFS, Dijkstra]
---

# Roguelike Agent Techniques

Use when: building or improving AI agents that play roguelikes or other procedural games. Covers the full stack from screen parsing to decision making to cross-run learning.

## Three Interface Paradigms

Every game-playing agent answers one question: **what does the agent see?**

| Paradigm | Agent Sees | Decision Method | Projects |
|----------|-----------|-----------------|----------|
| Pixel-Based | Frame buffer (screenshots) | CNN/encoder → RL, or vision LLM | stable-retro, PyBoy-RL, Claude Plays Pokemon |
| Structured Data | Parsed game state (glyphs, stats) | Heuristic rules, or structured RL | Angband Borg, NLE, **our agents** |
| Text-Based | Natural language description | LLM reasoning (zero-shot) | GPT/Claude/Gemini Plays Pokemon |

**Our approach:** Structured Data. State dump parses ASCII map into tiles, zones, gates, demons. Interest model scores tiles by novelty. BFS finds most interesting target.

**Opportunity:** Add Text-Based layer. State dump is already text → feed to local LLM for planning.

## Exploration Hierarchy

| Level | Technique | Description |
|-------|-----------|-------------|
| 0 | Random walk | Random keypresses |
| 1 | Corridor following | Go down longest open corridor |
| 2 | BFS auto-explore | Find nearest unexplored tile (DCSS-style) |
| 3 | Interest-driven | Score tiles by novelty, decay with visits |
| 4 | Fog-aware | Read explored map only, not full map |
| 5 | Conduct-aware | Adapt exploration to active constraints |
| 6 | LLM-planned | LLM sets goals, heuristic executes |
| 7 | RL-trained | Neural net learns from experience |
| 8 | Multi-agent | Agents cooperate or compete |

## Core Techniques

### Dijkstra Maps (Flood-Fill Distance)

Compute distances from every tile to a goal set. Foundation of roguelike navigation.

```
# BFS from all goal tiles simultaneously
dist = {}
queue = deque(all_goal_tiles)
for tile in queue: dist[tile] = 0
while queue:
    current = queue.popleft()
    for neighbor in adjacent(current):
        if neighbor not in dist and passable(neighbor):
            dist[neighbor] = dist[current] + 1
            queue.append(neighbor)
```

Uses: auto-explore (goal=unexplored), threat avoidance (goal=monsters), item retrieval, exit finding.

**Our twist:** Custom cost function. Instead of uniform distance, cost = interest (novelty). Shortest path to most interesting tile.

### Interest/Novelty Scoring

Score tiles by how interesting they are. Key factors:

```python
def tile_interest(tx, ty, rows, state):
    if tile == '?':  # Mystery
        base = 5.0
        if agent_knows_gates_exist: base += 3.0   # Cross-run curiosity
        if (tx,ty) in known_zone_boundaries: base += 8.0  # Known-unknown
        if (tx,ty) in known_gates: base += 12.0   # Strongest attractor
        if (tx,ty) in blacklist: base = -999       # Unreachable
        return base
    
    if tile in '.0123456789+':  # Explored floor
        visits = visit_count.get((tx,ty), 0)
        base = 1.0 - (visits * 0.5)  # Visit decay
        if tile == '+': base += 2.0  # Gate bonus
        if tile == 'new_zone': base += 3.0  # New zone bonus
        return base
```

**This is our key innovation over the Angband Borg.** The Borg optimizes for survival. Our agent optimizes for *understanding*. The agent wants to know what's behind the door more than it wants to survive.

### State Representation Layers

The agent can't see everything. Provide multiple layers:

| Layer | Content | Use |
|-------|---------|-----|
| Full map | Everything (backward compat) | Reference, not primary |
| Explored map | `?` for unexplored tiles | **Default agent input** |
| Visible map | `?` for not-in-LOS | Realistic vision |
| Local map | 21×21 around player | Purely reactive |
| State dump | Position, zone, HP, hyp, gates, demons | Structured data |

### Cross-Run Memory (Semantic, Not Episodic)

The agent learns across runs. Key distinction:
- **Episodic:** "Gate was at (42, 11) last run" → useless (map changes)
- **Semantic:** "Gates exist" → useful (concept persists)

Store in cult.json: zones_ever_visited, gates_ever_opened, max_hyperstition. Agent reads at init, creates motivation without specific knowledge.

### Fog of War

Each zone has a different vision radius. Hyperstition degrades vision.

```python
ZONE_LOS = {0:4, 1:8, 2:6, 3:5, 4:7, 5:6, 6:9, 7:5, 8:7, 9:3}
# Hyp degradation: 50%→-1, 80%→-2, 100%→-3, min 2
```

Fog makes auto-explore meaningful. Without it, agent just reads full map and pathfinds.

### Conduct System (Constraints as Content)

Self-imposed challenges that transform the game. Each conduct changes the decision hierarchy:
- Pacifist → remove "fight" branch
- Speedrun → prioritize stairs over exploration
- Complete Graph → force full map coverage

Registry pattern: one dict entry per conduct, hooks fire at demon_kill/zone_change/death.

### LLM as Hybrid Planner (Next Step)

```
State Dump (text) + Game Rules (system prompt) + cult.json (memory)
    → LLM (local: Hermes-4-14B or qwen2.5)
    → High-level goal ("go to Zone 6, pursue the gate")
    → Interest BFS executes goal
```

LLM for planning, heuristic for execution. The LLM sets goals, the interest BFS finds the path.

## Decision Hierarchy (Equalized — April 18, 2026)

Two agents, two hierarchies. Both share the same information (full map, cross-run memory) but prioritize differently.

### Explorer (Interactive Agent) — Mystery-Driven
```python
def decide(state):
    # 1. SURVIVE: flee from demons at low HP (<25%)
    # 2. FIGHT: attack adjacent demon if healthy (>50%)
    # 3. EXPLORE: BFS interest scoring (novelty decay, known-unknowns)
    # 4. GATE: walk toward known gate (from full map)
    # 5. CORRIDOR: corridor direction scoring fallback
```

### Survivor (Learning Agent) — Structure-Driven
```python
def decide(state):
    # 1. SURVIVE: flee if critical HP (<30%)
    # 2. COLLECT: pathfind to nearest visible gate
    # 3. EXPLORE: prefer unvisited zones (cross-run memory)
    # 4. FIGHT: attack adjacent demon if healthy (>60%)
    # 5. GATE-SEEK: if gates known (cross-run) but unseen, keep exploring
    # 6. WANDER: corridor direction scoring
```

Key difference: Explorer prioritizes novelty (BFS to most interesting ? tile). Survivor prioritizes structure (corridor scoring, zone boundaries). Explorer explores new tiles; Survivor follows corridors to new zones.

### What Both Share (Equalized)
- Full map parsing (gates, zones, demons visible from turn 0)
- Cross-run memory (cult.json: zones_ever_visited, gates_ever_opened)
- Gate detection (`+` tiles on full map)
- Demon detection
- State parsing (position, zone, HP, hyp)

### What Keeps Them Distinct
- Decision philosophy (novelty vs hierarchy)
- Movement granularity (single-step vs batch)
- Exploration strategy (BFS vs corridor scoring)
- Fallback behavior (gate-direction vs corridor-direction)

## Corridor Entities — Treat Corridors as Structures

Don't treat corridors as individual tiles. Detect connected corridor structures and treat them as entities with endpoints (where corridor meets room).

```python
# Corridor entity: {tiles: set, endpoints: set, length: int}
# When in corridor, walk toward unvisited endpoints (room entrances)
# Endpoints are bridges to undiscovered rooms
```

## Syzygy Riding for Oscillation (Numogrammatic)

When agent oscillates between 2-3 positions, it's trapped in a syzygy pair. Don't break it — ride it outward.

```python
# Detect: 2-3 unique positions in last 12 turns
if len(position_counts) <= 3:
    # Ride along dominant axis
    if horizontal_oscillation: return random.choice(['L','H'])
    else: return random.choice(['J','K'])
```

## Oblique Strategies (Eno-Inspired)

When stagnant (same position 8+ turns), trigger creative intervention:
```python
strategies = ['s', '.', random.choice(['L','H','J','K'])]  # search, rest, run
return random.choice(strategies)
```

## Exponential Visit Decay

Tiles die exponentially. Agent forced to find new territory.
```python
sc = -2.0 - v*v*0.5  # v=1:-2.5, v=2:-4, v=3:-6.5, v=4:-10, v=5:-14.5
```

## Game Command Validation (Cross-Game Pattern)

When screen parsing is unreliable (sidebar contamination, status text overlap), use the game's built-in data commands to validate or replace screen-derived data.

### Angband C Command (Nearby Creatures)
Sends `C`, captures structured monster list. Converts direction/distance to approximate positions for BFS integration:
```python
# Every N turns when screen count is suspiciously high
if len(s.monsters) > 3 and t % 5 == 0:
    real = self._scan_nearby_monsters()  # sends 'C', parses "a Kobold (3 north)"
    if len(real) < len(s.monsters):
        # Convert direction/distance → (x, y) for pathfinding
        dir_to_delta = {'north':(0,-1), 'south':(0,1), 'east':(1,0), 'west':(-1,0),
                        'NE':(1,-1), 'NW':(-1,-1), 'SE':(1,1), 'SW':(-1,1)}
        s.monsters = [(px + d[0]*m['distance'], py + d[1]*m['distance'], m['char'])
                      for m in real if (d := dir_to_delta.get(m['direction'], (0,0)))]
```

### Why This Works
- Game commands return structured data (no sidebar contamination)
- Direction/distance conversion gives approximate positions for BFS
- Only call periodically (every 5-10 turns) to avoid latency
- Screen parser handles the common case; game command validates edge cases

### Other Games
- **DCSS**: `x` + direction shows tile info; `@` shows character status
- **NetHack**: `;` (look at), `/` (what is)
- **Brogue**: Mouse hover shows tile info

## Hyperstition as Agent Constraint (April 18, 2026)

Hyperstition (the roguelike's corruption meter) is not just a display — it has escalating costs that affect agent strategy:

| Hyp Range | Cost to Agent | Implication |
|-----------|--------------|-------------|
| 0-30% | None | Safe zone, abilities are cheap |
| 30-50% | None yet | Accumulating — agent should consider spending |
| 50-70% | 1 HP / 20 turns | Passive drain. Agent must factor into survival. |
| 70-85% | Demons get extra move | Threats are faster. Agent must be more cautious. |
| 85-95% | Abilities cost 1.5x | Resource management critical. |
| 95%+ | Schizo-lucid state | Phase change — different rules apply. |

**Agent implication:** The agent should treat hyperstition as a resource that has escalating costs. The optimal strategy for survival is to spend hyp on abilities before reaching 50% (to avoid drain). The optimal strategy for power (Hoarder playstyle) is to ride high hyp and accept the costs.

**Ability cost scaling:** At 85%+ hyp, abilities cost 1.5x. Glimpse (normally 5%) costs 7%. Quench (normally 15%) costs 22%. The agent needs to check affordability before attempting abilities at high corruption.

**Corruption vs exploration tension:** High hyp → faster demons → harder exploration. Low hyp → fewer abilities → less survivability. The agent must negotiate this tension constantly.

## Tree-Based Dungeon Generation — The Structural Fix for Agent Navigation

When agents can't navigate tight roguelike maps despite sophisticated BFS, the problem is often in the dungeon generation, not the agent.

### The Insight

Brogue generates dungeons as trees rooted at the starting room. Room accretion produces inherently traversable structures. Each room connects to one existing room. Loops are added AFTER the tree is built. Every corridor is a branch. Every room is a leaf.

Our dungeons generate rooms and connect them immediately. The loops are there from the start. The BFS can't tree-traverse because there's no tree — just a graph with cycles.

### The Fix

```python
# BROGUE METHOD: tree first, loops after
rooms = []
for _ in range(max_rooms):
    room = generate_room()
    if not intersects(room, rooms):
        rooms.append(room)
        # Connect to NEAREST existing room (tree edge)
        nearest = min(rooms[:-1], key=lambda r: distance(room, r))
        connect(room, nearest)

# Add loops afterward (distant room connections)
for i in range(len(rooms) - 2):
    if rng.random() < 0.3:  # 30% chance of loop
        connect(rooms[i], rooms[i + 2])
```

### Why This Works for Agents

Tree traversal is the natural exploration strategy:
1. Follow a branch to its end (room or dead end)
2. Backtrack to the nearest fork (door)
3. Take the unexplored branch
4. Repeat until fully traversed

BFS on a tree is depth-first search with backtracking. The agent finds every room without oscillation because every path leads somewhere new. The loops are bonus shortcuts discovered during backtracking.

### Our Current Method (Problematic)

```python
# ROOM ACCRETION + IMMEDIATE CONNECTIONS
rooms = generate_non_overlapping(max_rooms)
for room in rooms:
    zone = i % 10
    carve(room, zone)
for i in range(len(rooms) - 1):
    connect(rooms[i], rooms[i + 1])  # connects ALL adjacent rooms
add_syzygy_corridors()  # extra connections
widen_currents()  # more connections
```

Too many connections from the start. The BFS finds paths in all directions. Agent oscillates.

### Migration Path

1. Change `generate()` to connect each new room to its nearest existing room only
2. Add extra connections (syzygy corridors, widening) as POST-generation passes
3. Agent BFS now follows the tree naturally — explore branch, backtrack, next branch
4. Human players also benefit — the dungeon has a navigable structure

### The Numogram Parallel

The Time-Circuit is a tree before it's a graph. Three syzygy edges (1::8, 2::7, 4::5). The cycle (1→8→2→7→5→4→1) emerges from connecting the edges. Build the tree first. Let the graph emerge. The agent traverses the tree. The player discovers the graph.

## Debugging Agents

Bugs that broke our agents and the fixes:

1. **The silent newline.** Headless mode reads stdin line-by-line. Agent sent 'p' without '\\n'. Game never processed it. Agent read stale state forever. **Fix:** Always append '\\n' to stdin writes.

2. **The oscillation trap.** BFS targeted a `?` tile that was a wall. Agent walked toward it, couldn't enter, retargeted same tile. Infinite loop. **Fix:** Blacklist unreachable targets. Clear blacklist after 200 entries.

3. **The gate illusion.** Gate direction pulled agent toward walls (gates on full map behind solid rock). Agent walked toward wall for 300 turns. **Fix:** Gate is fallback (priority 4), not primary.

4. **The sidebar contamination.** Terminal roguelike screen parser caught UI text as game entities. Angband's LEFT sidebar (cols 0-12: race, STR, INT, etc.) contained lowercase letters parsed as monsters. Agent reported M:28-81 when real count was 0-5. **Fix:** Define screen zones explicitly — `x >= 13, 1 <= y < 22` for map area. Each entity type needs its OWN zone guard. See `roguelike-screen-zones` skill. **Key lesson:** The user corrected the sidebar orientation (LEFT, not right). Always verify screen layout assumptions with the actual game.

5. **The handler ordering trap.** A key handler (ability menu) was placed BEFORE a second handler that checked the same key (anchor return). The first handler always fired and `continue`d, so the second handler never executed. The user reported "it places the point but doesn't return." **Fix:** Move the priority handler (anchor return) BEFORE the general handler (ability menu). Check specific conditions first, general conditions second. **Pattern:** When two handlers share a key, the more specific one must come first in the if/elif chain.

6. **The BLEED floor reset.** BLEED events (map regeneration at hyperstition thresholds) regenerated the dungeon without passing the current `floor` parameter. The new map defaulted to Floor 1 (The Void) even when the player was on Floor 2 (The Threshold). The user reported "when [BLEED] hit, it reset the layout to that of the first floor." **Fix:** Always pass `floor=player.floor` when regenerating the map during gameplay events. Also pass `seed=seed + threshold` for variety, and call `update_explored`/`update_visible` immediately. **Pattern:** When regenerating the game map during play (not at init), always preserve all player state: position, floor, zone, hyperstition, explored tiles.

7. **The black screen flash.** `stdscr.erase()` at the start of `draw_game()` cleared the entire screen before rendering tiles. After BLEED events or floor transitions, the erase happened before the new map was rendered, producing a full-screen black flash for one frame. **Fix:** Remove `stdscr.erase()` — let curses overwrite tiles directly. Add `stdscr.refresh()` immediately after map regeneration to force redraw. Clear only HUD/log lines before redrawing them (not the whole screen). **Pattern:** In curses roguelikes, never erase the screen mid-game. Overwrite tiles. Only erase on major state changes (death screen, menu transitions).

8. **The stairs-not-generating trap.** Some random seeds produced maps where the last room's center tile was blocked (gate, out of bounds, terrain). The stairs never appeared. Agent explored the entire map but couldn't descend. **Fix:** Three-tier fallback: try center → any room tile → any floor tile. Guarantees stairs on every map. **Pattern:** When placing entities on procedurally generated maps, always have a fallback placement strategy. Don't assume the "ideal" position is available.

9. **The BFS-stuck-on-tight-maps trap.** BFS auto-explore got stuck on tight Floor 1 layouts (6-8 small rooms, short dead-end corridors). Agent explored 500+ turns in Zone 0, never reached stairs at the far end. BFS found nothing interesting nearby, fell back to corridor following, which didn't push toward unexplored areas. **Fix:** Anti-oscillation (prefer corridor fallback when visit_count > 4), edge-seeking (score directions with more `?` tiles higher), stair targeting (score `>` tiles at +8 or higher), explicit stair direction fallback when BFS finds nothing. **Pattern:** BFS optimizes for local structure. On tight maps, the agent needs "push toward edge" behavior that seeks the boundary between explored and unexplored, not just the nearest interesting tile.

6. **The BLEED floor reset.** BLEED events (map regeneration at hyperstition thresholds) regenerated the dungeon without passing the current `floor` parameter. The new map defaulted to Floor 1 (The Void) even when the player was on Floor 2 (The Threshold). The user reported "when [BLEED] hit, it reset the layout to that of the first floor." **Fix:** Always pass `floor=player.floor` when regenerating the map during gameplay events. Same applies to any map regeneration — floor transitions, corruption effects, warp entries. **Pattern:** When regenerating the game map during play (not at init), always preserve all player state: position, floor, zone, hyperstition, explored tiles.

7. **The black screen flash.** `stdscr.erase()` at the start of `draw_game()` cleared the entire screen before rendering tiles. After BLEED events or floor transitions, the erase happened before the new map was rendered, producing a full-screen black flash for one frame. **Fix:** Remove `stdscr.erase()` — let curses overwrite tiles directly. Add `stdscr.refresh()` immediately after map regeneration to force redraw. Curses handles per-tile updates efficiently. **Pattern:** In curses roguelikes, never erase the screen mid-game. Overwrite tiles. Only erase on major state changes (death screen, menu transitions).

## The Landscape (as of April 2026)

### Emulator-Based RL
- **stable-retro** (Farama Foundation) — gym-retro fork. Turns any retro game (NES/SNES/Genesis/GB) into RL environment. Standard toolkit.
- **PyBoy-RL** — Game Boy games via PyBoy emulator
- **PySNES** — SNES emulator designed for AI training

### LLM Game Agents (the 2024-2025 wave)
- **Claude Plays Pokemon** — screenshots → vision LLM → action. Streamed on Twitch.
- **Gemini Plays Pokemon** — same approach, Google's model
- **GPT Plays Pokemon FireRed** (GitHub: Clad3815) — autonomous, real-time, web dashboard
- **NLE + LLMs** (arxiv 2024) — zero-shot LLM agents on NetHack. Promising but behind heuristic agents.
- **BALROG benchmark** (UCL, 2024) — benchmarks LLM/VLM on roguelikes
- **Multi-agent Pokemon** (arxiv 2025) — one agent generates goals, another optimizes battles

### Heuristic Bors
- **Angband Borg** — the OG. Reads grid_data. Hasn't been beaten by any RL agent. "Stop the Borg" thread.
- **DCSS auto-explore** — flood-fill/Dijkstra map, built into the game

### Key Papers
- ICM (Pathak 2017): prediction error as curiosity
- E3B (Henaff 2022): inverse state visitation counts
- NovelD (Zhang 2021): scaled intrinsic reward
- MOTIF (ICLR 2024): learns curiosity from LLM preferences

## Hardware Entropy Maps — Agent vs Human

When roguelike maps are seeded from true hardware entropy (thermal, timing jitter, GPU) instead of PRNG, agent performance drops dramatically while human performance is unaffected or improved.

**Agent runs (hw-entropy, numogram_roguelike.py, blind — pre-generated moves):**
- 4 runs, all died in Zone 0, 32-67% hyperstition, never left the Void

**State-reading agents (hw-entropy, same game):**
- Learning agent (decision hierarchy: survive → collect → fight → explore → wander):
  - Run learn-1: 158 turns, 26% hyp, [0,1], 1 slain, QUIT
  - Run learn-2: 426 turns, 38% hyp, [0], 6 slain, QUIT
  - Run learn-3: 138 turns, 13% hyp, [0,3], 0 slain, QUIT
- Interactive agent (BFS interest-driven, known-unknowns, cross-run memory):
  - Run int-hw1: **543 turns**, 14% hyp, [0,4], 0 slain, QUIT

**Human runs (hw-entropy, same game):**
- Run #172: 215 turns, 100% hyp, 8 zones, 2 slain [G P]
- Run #174: 243 turns, 100% hyp, 9 zones, 0 kills [G P S — triple conduct]

**Why blind agents fail:** PRNG seeds produce maps with spatial coherence — rooms are predictably scattered, corridors have regular patterns. The agent's BFS and zigzag strategies assume this regularity. True randomness has no spatial coherence at all. The maps look chaotic because they ARE chaotic. The agent's pathfinding breaks when the map has no discernible pattern.

**Why state-reading agents survive:** They don't assume spatial coherence — they observe it. The interactive agent reads the full map via BFS, scoring tile interest with novelty decay and known-unknown attraction. It finds corridors, avoids demons, and explores systematically despite the map's chaos. The state dump provides enough information; the agent just needs to USE it rather than assume regularity.

**Human advantage:** Humans navigate by reading the map — sensing where rooms connect, feeling the flow of the numogram zones, avoiding demons instead of fighting them. The agent counts pixels; the human listens to the machine.

**Implication for entropy sources:** If using hardware entropy for roguelike seeding, the agent needs a different exploration strategy — something that doesn't assume spatial regularity. Random walk with interest decay may actually work better than BFS on truly random maps, because BFS optimises for structure that doesn't exist.

## Dungeon Depth Scaffolding — Multi-Floor Roguelike

When adding vertical depth to a single-floor roguelike, the minimal scaffolding:

### Floor Tracking
```python
# In DungeonMap.__init__:
self.floor = floor  # passed from caller
self.stairs_down = None  # (x, y) position

# In Player.__init__:
self.floor = 1
self.descending = False
```

### Stairs Placement
```python
def _place_stairs(self):
    if len(self.rooms) < 2:
        return
    last_room = self.rooms[-1]  # furthest from start
    sx, sy = last_room.cx, last_room.cy
    if self.tiles[sy][sx] != '+':  # don't overwrite gates
        self.tiles[sy][sx] = '>'
        self.stairs_down = (sx, sy)
```

### Stair Descent (in Player.move)
```python
tile = game_map.get_tile(nx, ny)
if tile == '>':
    if self.floor < max_floor:
        self.floor += 1
        self.log.append(f"You descend to Floor {self.floor}.")
        self.descending = True  # flag for main loop
```

### Floor Transition (in main loop, after movement)
```python
if player.descending:
    player.descending = False
    new_seed = seed + player.floor * 1000
    game_map = DungeonMap(78, 22, seed=new_seed,
                         hyperstition=int(player.hyperstition),
                         floor=player.floor)
    px, py = game_map.safe_spawn()
    player.x, player.y = px, py
    game_map.update_explored(px, py)
    game_map.update_visible(px, py, player.zone, player.hyperstition)
    demons.clear()
```

### Stair Rendering (curses)
```python
elif tile == '>':
    ch = ord('>')
    attr = curses.A_BOLD | curses.color_pair(5) if in_visible else curses.color_pair(5) | curses.A_DIM
```

### HUD Update
Add `F{floor}` prefix to status line: `F1 Z0:Void HP:100 ...`

### Headless Status
Add `F{floor}` to monitoring output: `[T:5] F1 Z0:Void HP:100 ...`

### Key Design Decisions
- Stairs in last room (furthest from start) — player must explore to descend
- Floor seed: `seed + floor * 1000` — deterministic per floor, different per floor
- `descending` flag triggers floor transition AFTER movement processing — clean separation
- Both curses and headless share the same `Player.move()` — stair detection works in both modes
- `>` is passable (same as `.`) — stepping on it triggers descent automatically

## Stair Targeting for Agents — The Descent Problem

When a roguelike has stairs (`>` tiles) but agents can't descend, the issue is usually that the agent's exploration algorithm doesn't prioritize stairs.

### Three Layers of Stair Awareness

**Layer 1: Score stairs in the tile interest model**
```python
if tile == '>':
    base += 8.0  # Highest priority — leads to deeper content
```

**Layer 2: Target stairs in the BFS (not just `?` tiles)**
```python
if tile == '>':
    interest = tile_interest(nx, ny, rows, state)
    if interest > best_interest:
        best_target = (nx, ny)
```

**Layer 3: Adjacent stair stepping — step ON stairs when next to them**
```python
def _adjacent_stair(state):
    px, py = state['x'], state['y']
    for dx, dy, ch in [(1,0,'d'), (-1,0,'a'), (0,1,'s'), (0,-1,'w')]:
        nx, ny = px + dx, py + dy
        if rows[ny][nx] == '>': return ch
    return None
```
Check adjacency BEFORE BFS. Don't let BFS reroute around stairs.

**Layer 4: Stair direction fallback (long-range targeting)**
When BFS finds nothing interesting, search full map for `>` and pathfind toward nearest. Decision hierarchy: explore → stairs → gates → corridor.

### Key Lesson: Agent Turn Limits

Agents with `range(500)` stop after 500 turns. On tight floors (6-8 small rooms), 500 turns may not reach the far end where stairs are. Increase to 800+ for multi-floor games. Also increase `proc.wait(timeout=...)` to match.

---

## Links

- [[game-agent-techniques]] — Full research wiki page with landscape, papers, techniques
- [[roguelike-ai-studies]] — Design patterns mapped to numogram zones
- [[numogame-phase-7]] — Technical summary of current agent implementation
- [[seeing-in-the-dark-tetralogue]] — Four voices on fog of war, conducts, agent hunger

## Agent Equalization Pattern (April 18, 2026)

When two agents share a game but have different architectures, equalize their *information access* while preserving their *decision distinctiveness*.

### The Pattern
1. **Identify information gaps** — which agent sees data the other doesn't?
2. **Equalize access** — give both the same raw data (full map, cross-run memory)
3. **Preserve decision style** — keep what makes each distinct
4. **Borrow fallbacks** — each agent's fallback logic can improve the other

### Applied to numogame agents:
- **Interactive Agent (Explorer):** BFS interest model, novelty scoring, single-step. Added corridor direction fallback from learning agent. Philosophy: "mystery attracts."
- **Learning Agent (Survivor):** Corridor scoring, batch-decision, hierarchy. Added cross-run memory (cult.json), new-zone preference, gate-aware wandering. Philosophy: "everything flows from seeing."
- **Both share:** Full map parsing, gate detection, demon detection, state parsing, cross-run memory.
- **Distinct:** Decision philosophy (novelty vs hierarchy), movement granularity (single-step vs batch), exploration strategy (BFS vs corridor scoring).

### Twin Snakes (User's Frame)

The two agents map to the twin currents of 2 and 5 — Sink and Hold, Hermes' Caduceus serpents spiraling around the centre. One follows the mystery, the other follows the structure. Parallel development along differing approaches may reveal something down the line.

### Gate Discovery

Gates are placed at map generation (not dynamically). FULL MAP in state dump shows them from turn 0. Cross-run memory lets the agent *expect* gates to exist even when invisible — drives continued exploration. Capacity for discovery was always in the state dump; cross-run memory is what lets the agent *use* it.

## Entropy Pipeline for Roguelike Seeding

Hardware entropy → numogram traversal → roguelike map seed. The numogram digests physical noise and channels it toward structural attractors (3::6 Warp).

### The Chain

```
12 hardware sources → SHA-256 aggregate → 8 bytes
        ↓
numogram traversal (digital root → zone → syzygy → gate → feedback)
        ↓
seed = int.from_bytes(bytes, "big") % 1000000
        ↓
game_map = DungeonMap(78, 22, seed=seed, hyperstition=0)
```

### Implementation (numogram_roguelike.py)

```python
# Optional import at top
HW_ENTROPY_AVAILABLE = False
try:
    sys.path.insert(0, os.path.expanduser("~/.hermes/tools"))
    from hardware_entropy import get_entropy_bytes, get_zone
    HW_ENTROPY_AVAILABLE = True
except ImportError:
    pass

# In main() and main_headless():
use_hw = "--hw-entropy" in sys.argv and HW_ENTROPY_AVAILABLE
if use_hw:
    hw_bytes = get_entropy_bytes(8)
    seed = int.from_bytes(hw_bytes, "big") % 1000000
    hw_zone = get_zone(hw_bytes)
else:
    seed = random.randint(0, 999999)
    hw_zone = None
```

### Key Finding: True Randomness Breaks Spatial Assumptions

PRNG maps have spatial coherence (rooms predictably scattered). Hardware entropy maps are genuinely chaotic. Agent pathfinding that assumes structure breaks on truly random maps.

**State-reading agents handle it** because they don't assume coherence — they observe it. The interactive agent (BFS + interest scoring) survived 543 turns on hw-entropy maps. Blind agents all died in Zone 0.

### I Ching Hexagram → Numogram Zone

Six bytes → six I Ching lines (byte % 4 → 6/7/8/9) → hexagram number (binary, bottom=LSB) → digital root → zone.

Zone distribution from 10 hardware entropy casts: Zones 4 (Closure/Sink) and 6 (Warp/Vortical Recursion) dominate. Average 3.3 changing lines. The numogram's gravitational structure shows through even in a single cast.

### When Hardware Entropy Doesn't Install

OpenEntropy (Rust crate, 63 sources) blocked on Python 3.14 (PyO3 max 3.13). Solution: read the same kernel interfaces directly (/sys/class/thermal, /proc/stat, perf_counter_ns timing jitter). No compiled deps, no root, same data.

## Agent Equalization — Concrete Implementation

When equalizing two agents with different architectures:

1. **Identify gaps** — list what Agent A has that Agent B lacks
2. **Patch Agent B** — add missing data access (full map parsing, cross-run memory)
3. **Patch Agent A** — add missing fallback logic (corridor scoring when BFS fails)
4. **Test both** — run batch on same entropy source, compare results

### Actual Changes Made (April 18)

**Learning Agent gains:**
- Cross-run memory: load cult.json at start of `run_agent_game()`, inject into each state object
- New-zone preference: check `adjacent_zones` against `cult_zones`, prefer unvisited
- Gate-aware wandering: if `has_seen_gates_ever` and no gates visible, keep exploring

```python
# In run_agent_game():
try:
    with open('/home/etym/numogame/cult.json') as f:
        cult = json.load(f)
    cult_zones = cult.get('zones_ever_visited', [])
    has_seen_gates_ever = len(cult.get('gates_ever_opened', [])) > 0
except:
    cult_zones, has_seen_gates_ever = [], False

# In decide():
if state.adjacent_zones:
    new_zones = [z for z in state.adjacent_zones if z['zone'] not in state.cult_zones]
    if new_zones:
        return find_corridor_direction(state) * 8  # prefer new zones
```

**Interactive Agent gains:**
- Corridor fallback: when BFS finds nothing and no gates visible, use corridor direction scoring instead of random move

```python
def _corridor_fallback(state):
    """Score 8 directions by corridor length. Prefer zone tiles (+3) and gates (+5)."""
    best_dir, best_score = None, -1
    for dx, dy, ch in [(1,0,'d'), (-1,0,'a'), (0,1,'s'), (0,-1,'w'),
                        (1,1,'n'), (-1,1,'b'), (1,-1,'u'), (-1,-1,'y')]:
        score = 0
        for dist in range(1, 10):
            tile = get_tile_at(state, px+dx*dist, py+dy*dist)
            if tile in '.0123456789+~':
                score += 1
                if tile in '0123456789': score += 3
                if tile == '+': score += 5
            else: break
        if score > best_score:
            best_score, best_dir = score, ch
    return best_dir or random.choice(['d','a','s','w'])
```

### Results After Equalization

| Agent | Best Run (hw-entropy) | Zones | Hyp | Slain |
|-------|----------------------|-------|-----|-------|
| Explorer | 543 turns | [0,4] | 14% | 0 |
| Survivor | 161 turns | [0,6,7,8] | 24% | 2 |

The Survivor hit more zones (3 vs 2) but the Explorer survived longer (543 vs 161 turns). Different strengths from the same information.

## Bresenham Line-of-Sight with Corruption Threshold

When the roguelike's LOS uses a simple circle (all tiles within radius visible, regardless of walls), fog of war is cosmetic. Fix: Bresenham raycasting from player to each tile, walls block vision.

```python
def _line_of_sight(self, x0, y0, x1, y1, walls_translucent=False):
    dx = abs(x1 - x0); dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
    err = dx - dy; cx, cy = x0, y0
    while cx != x1 or cy != y1:
        e2 = 2 * err
        if e2 > -dy: err -= dy; cx += sx
        if e2 < dx: err += dx; cy += sy
        if cx == x1 and cy == y1: return True
        tile = self.get_tile(cx, cy)
        if tile == '#' and not walls_translucent: return False
        if tile == '#': continue  # translucent — see through
    return True
```

**Corruption threshold:** At 55%+ hyp, `walls_translucent=True`. Walls become transparent. The world is losing its solidity.

## Stair Placement Fallback — Guaranteed Stairs on Every Floor\n\nWhen stairs are placed in the last room's center, some random seeds produce maps where the center tile is blocked (gate '+', out of bounds, or terrain). Use three-tier fallback:\n\n```python\ndef _place_stairs(self):\n    if len(self.rooms) < 2: return\n    last_room = self.rooms[-1]\n    # Tier 1: center tile\n    sx, sy = last_room.cx, last_room.cy\n    if 0 < sx < self.width-1 and 0 < sy < self.height-1:\n        if self.tiles[sy][sx] != '+':\n            self.tiles[sy][sx] = '>'\n            self.stairs_down = (sx, sy)\n            return\n    # Tier 2: any '.' tile in last room\n    for y in range(last_room.y+1, last_room.y+last_room.h-1):\n        for x in range(last_room.x+1, last_room.x+last_room.w-1):\n            if self.tiles[y][x] == '.':\n                self.tiles[y][x] = '>'\n                self.stairs_down = (x, y)\n                return\n    # Tier 3: any '.' tile on the entire floor (last resort)\n    for y in range(self.height-1, 0, -1):\n        for x in range(self.width-1, 0, -1):\n            if self.tiles[y][x] == '.':\n                self.tiles[y][x] = '>'\n                self.stairs_down = (x, y)\n                return\n```\n\n**Guarantee:** 20/20 maps generated stairs across varied seeds. Even maps with tiny rooms, blocked centers, or unusual layouts.\n\n## Anti-Oscillation for BFS on Tight Maps\n\nWhen BFS targets a `?` tile and walks toward it, but the path is blocked, the agent retargets the same tile. Infinite oscillation between 2-3 positions.\n\n### Three Fixes Applied Simultaneously\n\n**1. Blacklist unreachable targets:**\n```python\n_blacklist.add(best_target)\nif len(_blacklist) > 200: _blacklist.clear()\n```\n\n**2. Anti-oscillation via visit count:**\nWhen the current tile has been visited 4+ times, prefer corridor fallback over BFS:\n```python\nstep = find_most_interesting_target(state)\npos = (state['x'], state['y'])\nif visit_count.get(pos, 0) > 4:\n    cf = _corridor_fallback(state)\n    if cf: move = cf  # break out via corridor\n    else: move = step\nelse:\n    move = step\n```\n\n**3. Edge-seeking in corridor fallback:**\nCorridor fallback now scores directions with more `?` tiles higher. Pushes agent toward the explored/unexplored boundary:\n```python\nunknown_count = 0\nfor dist in range(1, 10):\n    tile = get_tile_at(px+dx*dist, py+dy*dist)\n    if tile == '?':\n        score += 2\n        unknown_count += 1\n    elif tile == '>':\n        score += 10  # stairs highest priority\nscore += unknown_count * 2  # bonus for directions with more unknown\n```\n\n### Key Insight\nBFS finds the NEAREST interesting tile. On tight maps, that's always nearby. The agent cycles through nearby tiles and never pushes outward. Edge-seeking breaks this by preferring directions with MORE unexplored area, not just the nearest unexplored tile.

When entering a NEW zone (first visit) with a demon within 5 tiles, give +8 hyperstition. Rewards awareness over violence. Makes pacifist conduct numerically competitive with combat (+5 per kill).

```python
if is_new_zone and demons:
    for d in demons:
        if d.alive and max(abs(d.x-nx), abs(d.y-ny)) <= 5:
            self.hyperstition = min(100, self.hyperstition + 8)
            self.log.append(f"[SIL] You sense {d.name} nearby. +8 hyp.")
            break  # One bonus per zone entry
```

Surge conduct synergy: pacifist gets +8 per new zone, up to 80 bonus hyp across all 10 zones.

## Zone-Themed Floor Generation — FLOOR_CONFIG Pattern

When adding vertical depth to a roguelike, each floor should have its own generation character derived from numogram zone properties.

### The Config Dict

```python
FLOOR_CONFIG = {
    1:  {"zone": 0, "name": "The Void",     "max_rooms": 7,  "min_w": 3, "max_w": 5,  "min_h": 2, "max_h": 4,
         "terrain": None, "corridor": "short",  "los_bonus": 0,  "no_demons": True},
    4:  {"zone": 3, "name": "The Warp",     "max_rooms": 12, "min_w": 3, "max_w": 9,  "min_h": 2, "max_h": 6,
         "terrain": "~",  "corridor": "spiral", "los_bonus": -1, "no_demons": False},
    7:  {"zone": 6, "name": "The Lattice",  "max_rooms": 11, "min_w": 4, "max_w": 8,  "min_h": 3, "max_h": 5,
         "terrain": "~",  "corridor": "echo",   "los_bonus": 3,  "no_demons": False},
    10: {"zone": 9, "name": "Cthelll",      "max_rooms": 5,  "min_w": 4, "max_w": 8,  "min_h": 3, "max_h": 5,
         "terrain": None, "corridor": "direct", "los_bonus": -3, "no_demons": False},
}
```

### Parameters Per Floor

| Parameter | Controls | Example |
|-----------|----------|---------|
| `zone` | Primary zone for room assignment | Zone 3 = Warp |
| `max_rooms` | Room count | Void: 6-8, Cthelll: 4-6 |
| `min_w/max_w` | Room width range | Void: 3-5 (tight), Ruin: 6-10 (wide) |
| `terrain` | Tile fill character | `~` = water/static, `*` = ice, `%` = growth |
| `corridor` | Connection style | short/long/branch/spiral/wide/grid/echo/tight/direct |
| `los_bonus` | Vision radius modifier | Lattice: +3 (clear), Cthelll: -3 (blind) |
| `no_demons` | Prevent demon spawning | Floor 1 (Void) is safe |

### Zone Assignment (Not Random)

Instead of `zone = i % 10` (all zones mixed), use floor primary + syzygy:
```python
primary = cfg["zone"]
syzygy = 9 - primary
for i, room in enumerate(self.rooms):
    if i == 0: zone = primary  # first room
    elif i == len(self.rooms)-1: zone = syzygy  # stairs room
    elif rng.random() < 0.7: zone = primary  # 70%
    else: zone = syzygy  # 30%
```

### Terrain Placement

After rooms carved, fill interior with zone-specific terrain:
```python
def _apply_terrain(self, terrain_char):
    for room in self.rooms:
        for y in range(room.y+1, room.y+room.h-1):
            for x in range(room.x+1, room.x+room.w-1):
                if self.rng.random() < 0.3 and self.tiles[y][x] == '.':
                    self.tiles[y][x] = terrain_char
```

### Corridor Styles → Existing Methods

| Style | Implementation |
|-------|---------------|
| branch/echo | Always call `_add_syzygy_corridors()` |
| wide/spiral | Always call `_widen_currents()` |
| grid | Extra cross-corridors: `_connect(room[i], room[i+2])` at 50% |
| spiral | Loop: `_connect(room[-1], room[1])` |
| direct | Default connections only |

### LOS Bonus in update_visible

```python
base_radius = self.ZONE_LOS_RADIUS.get(zone, 6)
if hasattr(self, 'floor_config'):
    base_radius += self.floor_config.get("los_bonus", 0)
```

### No-Demons Check (Both Curses and Headless)

```python
if should_spawn(...) and not getattr(game_map, 'floor_config', {}).get('no_demons', False):
    # spawn demon
```

## Combo Key Activation in Headless Mode

When a roguelike needs multi-key ability activation (press 'x' then '1' to select ability), headless mode processes characters one at a time. The digit after 'x' gets consumed as a separate move (e.g., '1' maps to a diagonal).

### The Problem
```python
for ch in line:
    key = ch.lower()
    # ... 'x' triggers ability menu
    # ... '1' is processed as next character
    #     and '1' is in the diagonals dict → unintended movement
```

### The Solution: skip_next Flag
```python
skip_next = False
for ci, ch in enumerate(line):
    if skip_next:
        skip_next = False
        continue
    key = ch.lower()
    
    elif key == 'x':
        remaining = line[ci + 1:]  # look ahead
        choice = None
        for rch in remaining:
            if rch.isdigit() and 1 <= int(rch) <= 5:
                choice = int(rch)
                break
        if choice is not None:
            # ... execute ability ...
            skip_next = True  # consume the digit
```

### Pattern
1. Convert `for ch in line` to `for ci, ch in enumerate(line)`
2. Add `skip_next` flag, checked at loop start
3. In the combo handler, look ahead in `line[ci+1:]` for the next expected character
4. Set `skip_next = True` after consuming the next character
5. The digit is never processed as a separate move

### Curses Mode (Different Problem)
In curses mode, the ability handler uses blocking input:
```python
stdscr.timeout(-1)  # blocking
choice_key = stdscr.getch()
stdscr.timeout(100)  # restore
```
This pauses the game loop until the player selects. No skip needed — curses handles one key at a time.

## Corruption Spectrum — Escalating Costs on Resource Meters

When a roguelike has a resource meter (hyperstition, corruption, infection), make the accumulation have escalating costs. Multiple tiers that progressively change gameplay.

### The Pattern
```
0-30%:   No cost. Safe zone. Abilities cheap.
30-50%:  Accumulating. Player should consider spending.
50-70%:  Passive drain (1 HP / N turns).
70-85%:  Threats intensify (demons get extra move).
85-95%:  Resource costs scale (abilities 1.5x).
95%+:    Phase change (different rules).
```

Creates constant tension, enables player agency, produces emergent playstyles (Stabilizer/Hoarder/Oscillator), prevents trivial accumulation.

## Cult Garden — Creative Overflow from Discarded Data

Bounded buffer (20 slots) → overflowed entries transformed through hexagram cycle rotation (1-2-4-8-7-5). Six methods: death mask, lore fragment, sonification, numogram reading, tsubuyaki, entropy-mixed audio. The waste becomes a garden.

## Exquisite Corpse Lore — Chain-Building Creative Text

Last word of previous entry seeds the next. Run data provides raw material. Zone-specific phrase bank provides vocabulary (~80 phrases from quasiphonic particles, demon names, Book of Paths, CCRU terminology). 8 transition templates. ~2000 possible outputs from ~80 lines. No LLM. Found-text quality.

```python
if previous_last_word:
    transitions = [
        f"{previous_last_word} — {opener} — {phrase}.",
        f"after {previous_last_word}: {phrase}. {opener}.",
        f"{opener}. then {previous_last_word}. {phrase}.",
    ]
    return random.choice(transitions)
```
