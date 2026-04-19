---
name: roguelike-screen-agent
category: gaming
description: Play any terminal roguelike via tmux screen capture — external game agent pattern
triggers: ["roguelike", "tmux", "screen capture", "external game", "agent", "rogue", "angband", "brogue", "sil"]
---

# Roguelike Screen Agent — Playing External Games via tmux

Use when: you want an AI agent to play a terminal roguelike you DIDN'T write. Unlike the Abyssal Crawler (which has a built-in state dump API), external games only show their state on screen. The agent must READ THE SCREEN like a human does.

## Architecture

```
tmux session (the game process)
  → tmux capture-pane (read screen as ASCII text)
    → Screen parser (extract structured data from ASCII)
      → Agent decision (interest-driven BFS)
        → tmux send-keys (send input)
          → repeat
```

## Three Classes

### TmuxGame — Generic Terminal Interface

```python
class TmuxGame:
    def __init__(self, session, command, w=80, h=24):
        self.session = session
        subprocess.run(['tmux','kill-session','-t',session], capture_output=True)
        env = os.environ.copy(); env['TERM'] = 'xterm-256color'
        subprocess.run(['tmux','new-session','-d','-s',session,
                       '-x',str(w),'-y',str(h),command], env=env)
        time.sleep(3)
    
    def capture(self):
        return subprocess.run(['tmux','capture-pane','-t',self.session,'-p'],
                             capture_output=True, text=True).stdout
    
    def send(self, k):
        subprocess.run(['tmux','send-keys','-t',self.session,k],
                      capture_output=True)
    
    def quit(self):
        self.send('Q'); time.sleep(0.3); self.send('y'); time.sleep(0.5)
        subprocess.run(['tmux','kill-session','-t',self.session],
                      capture_output=True)
```

Works with: rogue, angband, sil, drl, brogue-ce, crawl, and any curses-based game.

### Screen Parser — Game-Specific

Each game needs its own parser. The parser extracts from the ASCII screen:
- Player position (@)
- Monsters (character → type mapping)
- Items (character → type mapping)
- Terrain (walls, floors, doors, corridors, stairs)
- Status bar (HP, level, gold, etc.)
- Messages (combat log, event text)
- Game-over detection

The parser should be a class that takes raw text and produces structured data. Keep it simple — don't try to understand the game's internal state. Just parse what's visible.

### Agent — Decision Loop

The agent reads parsed screen state and decides what to do. The decision hierarchy:
1. SURVIVE: flee from danger at low HP
2. FIGHT: attack adjacent enemies if healthy
3. HEAL: rest if damaged and safe
4. COLLECT: walk toward items
5. DESCEND: go down stairs when ready
6. EXPLORE: BFS toward most interesting unvisited tile
7. SEARCH: look for secret doors when stuck

## Context-Dependent Interest (April 15 Evening)

Static interest scores fail because the same tile is more or less interesting depending on the agent's context.

```python
def _interest(self, x, y, screen):
    """Empty rooms are cold. Exits are hot. Context changes what matters."""
    # Wall check: BOTH known_walls AND current screen walls
    if (x,y) in self.known_walls: return -999
    if screen and (x,y) in screen.walls: return -999
    
    in_corridor = (px,py) in self.known_corridors
    is_door = (x,y) in self.known_doors
    is_corridor = (x,y) in self.known_corridors
    is_stairs = self.known_stairs and (x,y) == self.known_stairs
    
    if (x,y) not in self.visited:
        sc = 8.0  # mystery
        if is_stairs: sc += 20.0
        if is_door and not in_corridor: sc += 10.0  # room exit
        if is_corridor and not in_corridor: sc += 8.0  # room exit
        return sc
    
    # Visited: room is dying
    v = self.vcount.get((x,y), 1)
    sc = -2.0 - v*0.5  # goes cold fast
    
    # What survives death: exits only
    if is_stairs: sc += 15.0
    if is_door: sc += 8.0
    if is_corridor: sc += 6.0
    return sc
```

**Key principle:** Once a room is empty, the ONLY interesting thing about it is what it leads to. The room dies. The exits live.

**Context switches:**
- In room → doors/corridors are hot (exits)
- In corridor → corridor ends are hot (lead to rooms)
- Low HP → items are hot (+15 instead of +6)

## Smart Movement — Cardinal vs Diagonal

```python
def _move(self, dx, dy, screen=None, run=True):
    """Cardinal in corridors, diagonal in open rooms."""
    dx = max(-1,min(1,dx)); dy = max(-1,min(1,dy))
    
    # Default: cardinal (reliable, works through doors)
    if abs(dx) >= abs(dy):
        ch = {(1,0):'L',(-1,0):'H'}.get((dx,0), 'J')
    else:
        ch = {(0,1):'J',(0,-1):'K'}.get((0,dy), 'L')
    
    # In open rooms with diagonal target: use diagonal
    if screen and dx != 0 and dy != 0:
        adj_open = sum(1 for ddx,ddy in [(1,0),(-1,0),(0,1),(0,-1),
                       (1,1),(-1,1),(1,-1),(-1,-1)]
                      if (px+ddx,py+ddy) in (screen.floors|screen.corridors|screen.doors))
        if adj_open >= 5:  # open area — diagonals safe
            diag = {(1,1):'N',(-1,1):'B',(1,-1):'U',(-1,-1):'Y'}
            ch = diag.get((dx,dy), ch)
    
    return ch if run else ch.lower()
```

**When to use each:**
- Cardinal: doors, corridors, fights, flee, any critical navigation
- Diagonal: open room exploration (5+ adjacent open tiles), item collection in corners
- Running (capital): default for general movement — passes through doors naturally

## Interest Model (static — for reference, prefer context-dependent above)
- Unvisited: 8.0 (mystery — what's there?)
- Door: +5.0 (gateway to unknown territory)
- Stairs: +10.0 (gateway to deeper levels)
- Item: +6.0 (known reward)
- Monster (distant): +3.0 (danger = interest)
- Visited: 1.0 - (visits × 0.8) (decays fast — boring after 2 visits)
- Dead end: -2.0 (visited and no exits)
- Wall: -999 (impassable)

The agent is a heat engine flowing from cold (visited) to hot (unvisited). Doors are thermal bridges connecting cold rooms to hot corridors.

```python
def _tile_interest(self, x, y, screen):
    if (x,y) in screen.walls: return -999
    if (x,y) not in self.visited:
        score = 8.0
        if (x,y) in screen.doors: score += 5.0
        if screen.stairs and (x,y) == screen.stairs: score += 10.0
        return score
    visits = self.visit_count.get((x,y), 1)
    score = 1.0 - visits * 0.8
    if (x,y) in screen.doors: score += 3.0
    if (x,y) in screen.corridors: score += 1.0
    return score
```

## Door-Through Fix (BREAKTHROUGH — April 15)
The agent reaches a door and can't walk through it. Root cause: agent treats doors as destinations (walk TO), not operations (walk THROUGH).

**Fix:** When agent position is ON a door tile, don't pick a new goal. Keep walking in the same direction. The door is a passage, not a room.

```python
# In _decide(), BEFORE goal selection:
if (px,py) in screen.doors:
    # Walk toward adjacent corridor or unvisited floor
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        tx, ty = px+dx, py+dy
        if (tx,ty) in screen.corridors or (tx,ty) not in self.visited:
            return run_direction(dx, dy)  # capital = run in Rogue
    # No corridor visible — keep walking
    return random.choice(['L','H','J','K'])
```

**Why it works:** In Rogue, doors are wall tiles (`+` in a row of `-`). The player walks FROM floor THROUGH door TO corridor in one step. The agent was reaching the door and immediately picking a new goal, turning around. The fix forces the agent to keep walking past the door into the corridor.

**Three thresholds identified:**
1. Door traversal (solved — this fix)
2. Screen boundary (known-map memory across captures)
## Rogue-Specific Learnings

### Terminal Layout
- 80×24 (VT100 standard)
- Line 23 (0-indexed): status bar ("Level: 1  Gold: 0  Hp: 12(12) ...")
- Lines 1-22: map area (roughly)
- Line 0: message area

### Autopickup
Rogue has autopickup — no need for `,` or `g` command. Just walk over items.

### Doors Are Walls — The Threshold Problem
In Rogue, `+` replaces a wall tile. You walk ONTO the wall to exit. In our Abyssal Crawler, gates are on floors. Same function, different geometry.

**Key finding:** "The door is not a place. The door is a verb." (Tetralogue VII). Doors are operations (walk THROUGH), not destinations (walk ONTO). The agent treats doors as coordinates. The game treats doors as transformations. `door(x) = corridor`.

**Fix:** When the agent is ON a door tile, keep walking in the same direction. Don't pick a new goal. The door is a passage, not a destination.

### Running Passes Through Doors
`Shift+capital` (L/H/J/K) runs until hitting an obstacle. Running passes through doors naturally. Walking stops on them. Default to running for all non-combat movement.

### Map Detection
Don't require BOTH `|` AND `-` on the same line. Rogue's walls are on separate lines (top/bottom have only `-`, sides have only `|`). Use: any line with `|` or `-` or `@` or `#`.

### Movement
- Vi keys: h/j/k/l (cardinal), y/u/b/n (diagonal)
- Diagonals can be unreliable — stuck in corners
- `Shift+dir` runs until hitting obstacle (passes through doors)
- Cardinal for corridors/doors, diagonal for open rooms (8+ adjacent passable)
- `.` rests for a turn (healing)
- `s` searches for secret doors

### Game-Over Detection
Check for: "R.I.P.", "killed by", "IN PEACE", "Score:", "Top Ten". Parser should set `game_over = True` and skip parsing.

### "More--" Prompts
Combat messages show "--More--" and need a space to dismiss. Check for this BEFORE parsing the screen.

### Dungeon Structure — The Tree Model (from Brogue articles)
The dungeon is a **tree rooted at the starting room** (room accretion algorithm). Every corridor is a branch. Every door is a fork. Exploration is tree traversal:
1. Follow a branch to its end (room or dead end)
2. Backtrack to the nearest fork (door)
3. Take the unexplored branch
4. Repeat until the tree is fully traversed

Loops are added AFTER the tree is built. The agent should prioritize tree traversal — loops are bonus shortcuts.

### Corridor Entities
Treat corridors as entities, not just tiles:
- `tiles`: connected set of `#` positions
- `endpoints`: where corridor meets room/door (room entrances)
- `length`: number of tiles

Detect via flood fill from accumulated known_corridors (not just current screen). When in a corridor, walk toward unvisited endpoints.

### Context-Dependent Interest Scoring
Interest scores change based on agent context:
- In a room: doors +10 (exits), corridors +8
- In a corridor: endpoints +10 (room entrances), doors +2
- Empty room: tiles decay to -2.0 - visits²×0.5 (exponential decay)
- Low HP: items +15 (survival instinct)
- Stairs always +20 (the furnace)

"Empty rooms die. Exits live."

### Stuck Recovery — Syzygy Riding and Oblique Strategies
**Stagnation** (same position 8+/12 turns): oblique strategy — search, rest, or run randomly.
**Oscillation** (2-3 positions in 12 turns): syzygy riding — commit to one direction along the oscillation axis.

Stuck counter only resets on ACTUAL movement, not on recovery attempt. Otherwise it oscillates between 0-1.

### Cross-Run Memory
`~/.rogue_memory.json` persists: runs, max_depth, total_gold, deaths, doors_walked.
Semantic concepts persist: "doors lead somewhere" not "door at (42,13)".

## Pitfalls

1. **Stale captures**: `tmux capture-pane` may return empty if game hasn't rendered. Retry 3 times with sleep.
2. **Session death**: tmux sessions die when game quits. Always try/except around capture.
3. **Diagonal blocking**: In Rogue, diagonals can be blocked by wall corners. Use cardinal-only near walls/doors.
4. **Door positioning**: Doors are on wall rows, not floor rows. Parser must handle `+` in a row of `-` characters.
5. **Visit decay too aggressive**: With `1.0 - visits*0.8`, tiles go negative after 2 visits. Use exponential: `-2.0 - v²×0.5`.
6. **BFS on screen data only**: The BFS only knows tiles visible on the CURRENT screen. Use accumulated known_* sets for pathfinding.
7. **Stuck counter reset**: Don't reset in recovery attempt — only reset when position ACTUALLY changes. Otherwise counter oscillates 0-1.
8. **Running overshoot**: `Shift+dir` passes through the target. Use running for corridors/doors, walking for precise positioning.
9. **Wall oscillation**: Agent runs into wall, stuck recovery sends random direction, agent runs into another wall. Syzygy riding commits to one axis.

## The Threshold Problem — Doors Are Operations, Not Destinations

**Critical finding (Apr 15, 2026).** 8 Rogue runs: explore 20-50 turns → freeze for 250+ turns. Agent reaches door, can't walk through it.

**Root cause:** In Rogue, `+` replaces a wall tile. You walk THROUGH it. Agent treats it as a tile to stand ON.

**Fix:** Target the tile PAST the door, not the door itself. Or: when adjacent to door, run (`Shift+dir`) to pass through.

**Deeper insight (Tetralogue VII):** "The door is not a place. The door is a verb." Agent speaks in nouns (coordinates). Game speaks in verbs (operations). `door(x) = corridor`.

## DFS Commitment — Tree Traversal (BREAKTHROUGH — April 16)

The agent oscillates between corridor entrances because it re-evaluates every turn. The fix: commit to a target and don't change until reached or blocked. This is depth-first tree traversal — follow a branch to its end before backtracking.

```python
# At TOP of _decide (override everything except critical HP < 20%):
if self.committed_target and pct > 0.2:
    tx, ty = self.committed_target
    dist = abs(tx-px) + abs(ty-py)
    if dist == 0:
        self.committed_target = None  # reached — keep running same direction
        if self.last_action.upper() in ('L','H','J','K'):
            return self.last_action
    elif self.committed_steps > 60:
        self.committed_target = None  # branch exhausted
    else:
        self.committed_steps += 1
        return self._move(tx-px, ty-py, screen, run=True)

# When entering a corridor — commit to one endpoint
for corr in self.corridors:
    if (px,py) in corr['tiles']:
        targets = [e for e in corr['endpoints'] if e not in self.visited]
        if targets:
            target = min(targets, key=lambda e: abs(e[0]-px)+abs(e[1]-py))
            self.committed_target = target
            self.committed_steps = 0
            return self._move(target[0]-px, target[1]-py, screen, run=True)
```

**Results:** Without DFS: 37 floors (oscillation). With DFS: 216 floors (near-complete level).

## Angband-Specific (April 16 — Extended)

Text mode: `angband -mgcu -n -uborg`. The `-n` flag starts new character, `-uborg` uses savefile "borg".

### Vi Keys Don't Work
Angband curses mode (`-mgcu`) does NOT support vi keys (h/j/k/l). Use:
- Numpad: 8=Up, 2=Down, 4=Left, 6=Right, 7/9/1/3=diagonals
- Arrow keys: Up/Down/Left/Right (also work)
Tested April 16 — vi keys are silently ignored, arrows and numpad both work.

### Character Creation
With `-n` flag, Angband shows "New character based on previous one" confirmation screen.
Key: send 'y' (not Enter) to accept. Screen text: `['Y': use as is; 'N': redo; ...]`

### `-more-` Prompt (CRITICAL)
Angband uses `-more-` (lowercase, single dash), NOT `--More--` (capitalized, double dash like NetHack).
This prompt intercepts ALL input — agent freezes if not detected.
Dismiss with space bar, not ESC.

### Cascading Dialogs
After `-more-` (space), Angband often shows a follow-up dialog:
- "Inscribe with what?" → ESC to dismiss
- "Ignore which item?" → ESC to dismiss
- "Inscribe an object ({)" → ESC to dismiss
Agent must loop dialog detection until screen is clean.

### `>` vs `<` Stairs — Critical Distinction
- `>` (down stairs): PRIORITY — always descend when visible
- `<` (up stairs): FALLBACK — only go up when level explored and no `>` found
Parser must track both separately: `stairs_down` and `stairs_up`.
Agent should NOT go up `<` immediately — explore the floor first.

### Searching and Hidden Doors (April 16)
When stuck or in tiny rooms (< 20 floors visible), search with `s` key. Angband searches all 8 adjacent tiles for hidden doors. Warriors have low search skill (~11%), so many searches may be needed.

`+` (closed door) and `'` (open door) should be parsed as walkable floors and high-interest targets (+15 in BFS). Doors lead to new corridors and rooms.

**Proactive search:** When in a tiny room with no stairs visible, search 50% of the time even when not stuck. The agent may be walking between 4 tiles without realizing it needs to find exits.

**Door priority:** When doors appear after searching, walk toward them immediately — they're the way out.

### Stuck-vs-Stairs Priority Conflict
**Problem:** Search behavior at priority 5 fires before stairs commitment at priority 0. Agent searches forever even when stairs are visible.

**Root cause:** `self.stuck > 1` triggers search. Stuck counter increments every turn position doesn't change. Search returns `s` (no position change), stuck counter stays high. Stairs never get a chance to fire.

**Fix:** Reset stuck when stairs visible:
```python
if self.stuck > 1:
    if s.stairs_down or s.stairs_up:
        self.stuck = 0  # we CAN see stairs — not really stuck
```
This lets the stairs commitment at priority 0 fire on the next turn.

### Door Detection (`+`/`'`)
Parse closed doors (`+`) and open doors (`'`) as walkable floors. Doors are high-interest targets (+15 in BFS) — they lead to new corridors and rooms. Track in `s.doors` list.

### Proactive Search in Tiny Rooms
When visible floor count is very low (< 20 tiles) and no stairs visible, search 50% of the time even when NOT stuck. The agent walks between 4 tiles without realizing it needs to find exits.

```python
# 5.5 TINY ROOM — proactive search even when not stuck
if len(s.floors) < 20 and not s.stairs_down and not s.stairs_up and not self._is_town(s):
    if random.random() < 0.5:
        return 's'  # search half the time in tiny rooms
```

This fires BEFORE BFS exploration — the agent searches instead of walking in circles.

### Town Death — Hostile NPCs
Town has hostile NPCs (village drunks, Farmer Maggot's dogs). They hit hard. Avoid or flee. The agent died at turn ~142 to a town drunk with Zuiquan.

### Grok's Chunked Diving Curriculum
From Grok Angband conversation (~/obsidian/hermetic/raw/Grok Angband conversation.md):
- Phase 1: Shallow grinding (L1-10), build basics, learn monster behaviors
- Phase 2: Chunked diving (5-15 levels, then recall to town)
- Phase 3: Deep dive to Morgoth
- "Depth > everything" — deeper kills level you faster, better loot
- Word of Recall scrolls for safe retreat
- Town is the strategic anchor, not just a safe zone

### HP-Gated Descent (April 16)
Don't descend with low HP. Town drunks and out-of-depth monsters are lethal. Gate descent at 60%+ HP (`pct > 0.6`). The agent died at turn 197 after descending to L1 with only 13/20 HP.

### Death Detection Fix
Angband shows "RIP" (without periods), not "R.I.P." The game_over check must include both forms plus "the Rookie" (character title on death screen).
**Problem:** Agent oscillates entering/leaving the same store — BFS routes back because store tile is in `all_pass`.

**Fix:** Use `visited_stores` set (by store number). Mark visited when agent is ADJACENT (within 1 tile), not just ON. BFS excludes visited stores from `all_pass`. `_town_stores_visited` checks `visited_stores`. Reset on town return (fresh stock).

Key: `abs(s.pos[0] - sx) <= 1 and abs(s.pos[1] - sy) <= 1` — mark NEAR, not ON.

**Class-aware shopping:** Warriors skip spellbooks, INT/WIS items, staves/wands/rods. Buy: Cure potions, Recall, food, Phase Door, STR/DEX/CON stat potions. Price-aware: only buy what we can afford.

### Status-Bar Stair Detection
When `<` or `>` aren't visible on the map (tiny rooms), Angband shows "Up staircase" or "Down staircase" in the status bar. Parse this as fallback:
```python
if 'Up staircase' in line or 'up staircase' in line:
    if not self.stairs_up and self.pos:
        self.stairs_up = self.pos  # standing on it
```
This prevents the agent from being trapped in tiny rooms with invisible stairs.
Angband regenerates dungeon levels when you return to town and descend again.
Fresh layout, fresh stair placement each time. Agent can use this as "chunked diving":
1. Descend from town via `>`
2. Explore new level, look for `>` to go deeper
3. If no `>` found after 200 turns, go back up via `<`
4. In town, find new `>` and descend to fresh level
Shopping in town between dives (future work).

### Floor Characters
`·` (U+00B7 middle dot), `§` (U+00A7 section sign), `.` (period). All are floors.
Parser: `FLOOR = set('.·§')`

### Display Layout
- Left ~66 columns: map
- Right sidebar: stats (class name, level, STR/INT/WIS/DEX/CON)
- Sidebar text gets parsed as "monsters" (false positives) — cosmetic issue, doesn't block movement
- Status bar at bottom: HP, Gold, Depth, "Open floor"/"Town" indicator

### Stuck Detection in Tiny Rooms
Agent can get stuck in 3-tile rooms with only `<` stairs. Key fix:
- Track `known_stairs_up` across turns (stairs may scroll off screen)
- When go_up triggers, walk toward REMEMBERED stairs position, not just visible ones
- `level_turns` counter: go up after 200 turns without finding `>`

### Status Display Format
`T:25 @(46,16) HP:20 D:L1 F:3 M:7 [U-] L22 stuck:0`
- [U-]: up stairs visible, no down stairs
- [-D]: down stairs visible, no up stairs
- [UD]: both visible
- [--]: no stairs visible
- L22: 22 turns spent on current level

## Angband Town & Shopping (April 16 — BFS Navigation)

### BFS Pathfinding for Town
Direct-line `_move` gets stuck on town walls. Use `_bfs_to(target, s)` — BFS from agent to specific coordinate. Excludes visited stores from `all_pass`. Adds stairs to passable set.

### Store Detection — Adjacency Check
Sidebar digits (STR:18, INT:8) parsed as stores. Fix: only detect digits adjacent to `#` walls (buildings). `_is_building(y, x)` checks 8 neighbors for `#`.

### Store Visit Loop (3-layer bug)
**Symptom:** Agent oscillates entering/leaving same store.
**Root causes:** (1) stores in `self.visited` → BFS can't route through, (2) `_town_stores_visited` checked positions not store numbers, (3) store menu only visible ~1 frame.
**Fix:** `visited_stores` set by NUMBER. Mark ADJACENT (within 1 tile). BFS excludes visited. Reset on town return.

```python
# Mark when NEAR, not ON
for sx, sy, sn in s.stores:
    if abs(s.pos[0] - sx) <= 1 and abs(s.pos[1] - sy) <= 1:
        if sn not in self.visited_stores:
            self.visited_stores.add(sn)
```

### Class-Aware Shopping
Warriors skip: Books of Magic, INT/WIS items, staves/wands/rods.
Buy (all classes): Cure potions (25g), Recall (150g), Rations (5g), Torches (2g), Lanterns (35g), Flasks of oil (3g), Phase Door (15g).
Warriors add: STR/DEX/CON stat potions (800g).

### Search-on-Stuck
When stuck: 80% search (`s`), 20% move (random direction). Angband's `s` reveals hidden doors (`+`) in adjacent walls. Takes many tries.
**Critical:** Reset stuck when stairs visible — otherwise search blocks descension.

### ANSI Color Capture
`tmux capture-pane -p -e` preserves 256-color ANSI. Angband GCU codes: `\033[38;5;Nm`. Key: 145=floor gray, 152=wall blue, 51=cyan, 160=red, 188=white.

### AAR Logging
`~/.angband_runs.jsonl` + checkpoint fallback (SIGKILL bypasses try/finally). Track: depth, turns, stores, kills (message parsing), items, artifacts (`{name}`).

### Game Over Detection
Angband curses: "RIP" (no periods). Check: 'R.I.P.', 'RIP', 'killed by', 'the Rookie'.

### Wall Collision Messages
"There is a wall in the way!" is a game message, not a dialog. Filter it out or agent sends ESC forever.

### Progressive Turn Budget (April 16)
Each dungeon visit gets more turns as the player gets stronger:
```python
def _turn_budget(self, depth):
    visits = self.level_visits.get(depth, 1)
    return 200 + (visits - 1) * 75  # 200, 275, 350, 425, ...
```
`level_visits` resets when depth changes. Track in run loop: `self.level_visits[depth] = self.level_visits.get(depth, 0) + 1`.

### `visited_stores` Reset on Town Return
When depth changes to town (`self._is_town(s)`), reset `visited_stores = set()`. Stores restock — agent should visit them again on each town trip.

### Walls Aren't Dialogs
"There is a wall in the way!" is a GAME MESSAGE, not a dialog. Filter it in `_check_dialog` or the agent sends ESC forever (never moves).
```python
if 'wall in the way' in raw:
    return False
```

### Stuck Reset When Stairs Visible
When stuck > 1 but stairs are visible on screen, reset stuck counter. Otherwise search behavior blocks the stairs commitment at priority 0.
```python
if self.stuck > 1:
    if s.stairs_down or s.stairs_up:
        self.stuck = 0  # we CAN see stairs — not really stuck
```

### Store Detection — `_is_building()` Adjacency Check
Sidebar digits (STR:18, INT:8) look like stores. Filter: only detect digits adjacent to `#` walls.
```python
def _is_building(self, y, x):
    for dy in range(-1, 2):
        line = self.lines[y + dy] if 0 <= y + dy < len(self.lines) else ''
        for dx in range(-1, 2):
            if dy == 0 and dx == 0: continue
            cx = x + dx
            if 0 <= cx < len(line) and line[cx] == '#':
                return True
    return False
```

### BFS Pathfinding for Targeted Movement — `_bfs_to(target, s)`
Separate from exploration BFS. Finds shortest path to specific coordinate. Excludes visited stores from passable set. Used for store navigation and stair approach.
```python
def _bfs_to(self, target, s):
    all_pass = s.floors | self.known_floors
    for sx, sy, sn in s.stores:
        if sn not in self.visited_stores:  # exclude visited stores
            all_pass.add((sx, sy))
    # Standard BFS from s.pos to target, return first step
```

### Store Entry Is Automatic
Walking onto a store number tile opens the store menu automatically. No need to press Enter or direction keys. But the menu is only visible ~1 frame before agent processes it.

### Kill and Item Tracking from Messages
Parse top 3 lines of screen for kill messages (\"slain the Kobold\") and item pickup (\"found a Potion\"). Use regex: `r'(?:slain|destroyed|killed)\\s+(?:the\\s+)?([A-Z][a-z]+)'`.

### AAR Logging — JSONL + Checkpoint
Write run data to `~/.angband_runs.jsonl` at end of run. Also write checkpoint to `~/.angband_runs_checkpoint.json` every 100 turns (SIGKILL bypasses try/finally).

## Debugging Angband Agents (April 16)
When stuck, check: (1) tmux screen — what's actually visible? (2) has_dialog — false positive from wall messages? (3) BFS return — is it None or a valid key? (4) Do keys work? Test manually. (5) Sidebar digits parsed as stores? (6) visited_stores loop? (7) Stair detection from status bar?

Key insight: "There is a wall in the way!" triggered dialog detection → agent sent ESC forever → never moved. Fix: 1-line filter. Hardest bugs have simplest fixes.

Text mode: `angband -mgcu`. Floor character: § (U+00A7) or · (U+00B7). Character creation: send Enter to accept defaults. ESC pitfall: sending ESC every turn may OPEN menus. Only send ESC when dialogs detected. Town level: agent starts in town, needs `>` to descend to dungeon.

**Fix:** `self.known_floors |= screen.floors` each turn. BFS uses accumulated known tiles.

## Cross-Run Memory

Persist `~/.rogue_memory.json` with runs, max_depth, deaths. Agent carries concepts across runs.

## Movement

- Walk (h/j/k/l): for doors, items, precise nav
- Run (H/J/K/L): for corridors, overshoots doors
- Diagonals (y/u/b/n): unreliable, use cardinal for critical nav

## Room Exhaustion

70%+ nearby tiles visited → force door/corridor exit.

## BFS with Interest Scoring — Screen Context Required

The BFS pathfinding must receive the current screen for two reasons:
1. Wall detection: check `screen.walls` AND `self.known_walls` (known_walls is empty on first turn)
2. Interest scoring: `_interest()` needs context (in_corridor, hp, items) from the screen

```python
# Pass screen to _pathfind
step = self._pathfind(s.pos, goal, passable, s)

# In _pathfind, pass screen to _interest
sc = self._interest(cx, cy, s)  # NOT None

# In _interest, check both wall sources
if (x,y) in self.known_walls: return -999
if screen and (x,y) in screen.walls: return -999  # current screen walls
```

## Corridor Entities — Treat Corridors as Structures

Don't treat corridors as individual tiles. Detect connected corridor structures and treat them as entities with endpoints.

```python
def _detect_corridors(self, screen):
    """Detect connected corridor structures from accumulated known tiles."""
    all_corridors = self.known_corridors | (screen.corridors if screen else set())
    all_floors = self.known_floors | (screen.floors if screen else set())
    all_doors = self.known_doors | (screen.doors if screen else set())
    
    visited = set()
    self.corridors = []
    
    for tile in all_corridors:
        if tile in visited: continue
        # BFS to find connected corridor tiles
        corr_tiles = set()
        queue = [tile]
        while queue:
            cx, cy = queue.pop()
            if (cx,cy) in visited or (cx,cy) not in all_corridors: continue
            visited.add((cx,cy))
            corr_tiles.add((cx,cy))
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                if (cx+dx,cy+dy) in all_corridors and (cx+dx,cy+dy) not in visited:
                    queue.append((cx+dx,cy+dy))
        
        if len(corr_tiles) < 2: continue
        
        # Endpoints: corridor tiles adjacent to rooms/doors
        endpoints = set()
        for (cx,cy) in corr_tiles:
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                if (cx+dx,cy+dy) in all_floors or (cx+dx,cy+dy) in all_doors:
                    endpoints.add((cx+dx,cy+dy))
        
        self.corridors.append({'tiles': corr_tiles, 'endpoints': endpoints, 'length': len(corr_tiles)})
```

**Usage in decision:** When in a corridor, walk toward unvisited endpoints (room entrances).

## Stuck Recovery — Exclude Rest, Force Direction Change

**Problem:** Agent rests (`.`, HP recovery) and stuck counter increments because position doesn't change. After 1 turn of resting, stuck recovery fires and moves the agent away from healing.

**Fix:** Track `last_action`. Exclude `.` from stuck detection.

```python
# In run loop:
act = self._decide(screen)
self.last_action = act

# In stuck detection:
if screen.pos == self.last and self.last_action != '.':
    self.stuck += 1  # NOT resting
elif screen.pos != self.last:
    self.stuck = 0   # actually moved
```

**Stuck recovery:** After 1 turn stuck (not 3+), try random cardinal direction. Don't wait — the agent is probably hitting a wall.

```python
if self.stuck > 1:
    self.stuck = 0
    return random.choice(['h','j','k','l'])
```

## Heal Threshold — Only Rest When Critically Low

**Problem:** Agent rests when HP is 11/12 (below max). Gets stuck in rest loop.

**Fix:** Only rest when HP is genuinely low (< 30% of max), not just below max.

```python
if pct < 0.3 and not screen.monsters:  # NOT pct < 0.5
    return '.'  # rest
```

## Pitfalls

1. **Stale captures**: `tmux capture-pane` may return empty if game hasn't rendered. Retry 3 times with sleep.
2. **Session death**: tmux sessions die when game quits. Always try/except around capture.
3. **Diagonal blocking**: In Rogue, diagonals can be blocked by wall corners. Use cardinal-only for critical navigation (doors).
4. **Door positioning**: Doors are on wall rows, not floor rows. Parser must handle `+` in a row of `-` characters.
5. **Visit decay too aggressive**: With `1.0 - visits*0.8`, tiles go negative after 2 visits. For small rooms, this means the agent rapidly runs out of interesting tiles and gets stuck.
6. **BFS on screen data only**: The BFS only knows tiles visible on the CURRENT screen. If the player is in a corridor, only corridor tiles are visible. The BFS can't find rooms beyond the corridor because they're off-screen.

## Brogue — Graphical Rendering (April 16)

Brogue uses graphical rendering (SDL). No text output via tmux capture-pane.
The `-G` flag ENABLES graphical tiles (not disables). There's no `--no-graphics`.

**Conclusion:** Brogue can't be played via tmux. Need VNC/X11 or a different approach.

## Angband — Text Mode Works (April 16)

Angband works in text mode with `-mgcu` flag:
```
angband -mgcu
```

**Floor character:** Angband uses `·` (middle dot, U+00B7) for floors, not `.` (period).
Some terminals render as `§` (section sign, U+00A7).
Parser: `FLOOR = set('.·§')`

**Display layout:**
- Map is left ~66 columns
- Right sidebar has stats and inventory
- Status bar at bottom: HP, Gold, Depth, stats
- `@` = player, `#` = walls, `·` = floors, `<`/`>` = stairs, `%` = monsters

**Character creation:** Send Enter repeatedly to accept defaults (race, class, name).

**ESC pitfall:** Sending ESC every turn may OPEN menus instead of closing them.
Only send ESC when dialogs are actually open (detected by specific text patterns).

## DFS Commitment — Tree Traversal (BREAKTHROUGH — April 16)

The agent oscillates between corridor entrances because it re-evaluates every turn. The fix: **commit to a target and don't change until reached or blocked.**

```python
# In __init__:
self.committed_target = None
self.committed_steps = 0
self._last_target_dist = None

# At TOP of _decide (before flee/fight/heal — override everything except critical HP):
if self.committed_target and pct > 0.2:
    tx, ty = self.committed_target
    dist = abs(tx-px) + abs(ty-py)
    if dist == 0:
        self.committed_target = None  # reached
    elif self.committed_steps > 60:
        self.committed_target = None  # branch exhausted
    else:
        self.committed_steps += 1
        return self._move(tx-px, ty-py, screen, run=True)

# When finding a corridor endpoint:
self.committed_target = target
self.committed_steps = 0
self._last_target_dist = abs(target[0]-px) + abs(target[1]-py)

# When entering a corridor — commit to one endpoint
for corr in self.corridors:
    if (px,py) in corr['tiles']:
        targets = [e for e in corr['endpoints'] if e not in self.visited]
        if targets:
            target = min(targets, key=lambda e: abs(e[0]-px)+abs(e[1]-py))
            self.committed_target = target
            self.committed_steps = 0
            return self._move(target[0]-px, target[1]-py, screen, run=True)
```

**Why it works:** The agent commits to a destination and doesn't change targets mid-path. This prevents oscillation at corridor entrances and dead ends. The commitment overrides all other decisions (except critical HP < 20%).

**When commitment clears:**
- Target reached (dist == 0)
- Branch exhausted (60+ steps toward same target)
- Blocked (distance increases — agent hit a wall)

**Results:** v1-v12 oscillated between 2 positions. v13 with DFS commitment explored 216 floors.

## The Dungeon Is a Tree (from Brogue Room Accretion)

The Brogue room accretion algorithm produces dungeons that are **trees rooted at the starting room**. This means:

- Every room connects to exactly one parent (except the root)
- Every corridor is a branch
- Every door is a fork
- Exploration = depth-first tree traversal

**Agent implication:** Follow branches to endpoints, explore rooms, backtrack to forks, take unexplored branches. This is systematic exploration, not random wandering.

```python
# Tree traversal algorithm:
# 1. In room → find doors → run through (running passes through doors)
# 2. In corridor → commit to endpoint → follow it
# 3. At endpoint → enter room → explore → backtrack to corridor
# 4. At fork (door) → take unexplored branch
# 5. Repeat until tree is fully traversed
```

## Dead-End Backtracking

When the agent reaches a dead end, it should backtrack toward the nearest unvisited door or corridor.

```python
if self.stuck > 1:
    backtrack_targets = []
    for door in screen.doors | self.known_doors:
        if door not in self.visited:
            backtrack_targets.append(door)
    if backtrack_targets:
        target = min(backtrack_targets, key=lambda t: abs(t[0]-px)+abs(t[1]-py))
        self.committed_target = target
        return self._move(target[0]-px, target[1]-py, screen, run=True)
```

## HP Management — Don't Fight When Hurt

```python
# Flee below 40%, dangerous monsters below 55%
# Fight only above 60%
# Rest below 40% when no monsters, always rest below 30%

if pct < 0.4 and not screen.monsters:
    return '.'  # rest

if pct > 0.6:  # only fight when healthy
    for mpx,mpy,ch in screen.monsters:
        if screen.adj(screen.pos, (mpx,mpy)):
            return self._move(mpx-px, mpy-py, screen, run=False)
```

## Cross-Run Memory for Stair Knowledge

Agent knows stairs exist from ANY previous run. Actively seeks them.

```python
self.memory['knows_stairs'] = True  # always remember

# When stairs known but not found — seek unvisited corridor endpoints
if self.memory.get('knows_stairs') and not self.known_stairs:
    for corr in self.corridors:
        for ep in corr.get('endpoints', []):
            if ep not in self.visited:
                self.committed_target = ep  # stairs might be there
                return self._move(ep[0]-px, ep[1]-py, screen, run=True)
```

## Connection to Abyssal Crawler Agent

The interest model crosses the boundary between our game and external games. The principle is the same: "unvisited is hot, visited is cold, doors are thermal bridges." What differs is HOW the agent sees the game state (state dump API vs screen capture). The decision-making is identical.

## Running as Default Movement (April 15)

Capital letters (H/J/K/L) run until hitting obstacle. This naturally passes through doors and covers corridors. Use running as the DEFAULT for all non-combat movement.

```python
# Default: running (capital)
# Fights/flee: walking (lowercase) — don't run past enemy
# Rest: '.' only when HP < 30%
```

**Why running works for doors:** In Rogue, you don't stop ON a door. You walk THROUGH it. Running continues through the door into the corridor. Walking stops on the door tile.

## Area Stagnation Detection (April 15)

Position stagnation (same tile) is different from area stagnation (oscillating in small area). Need both.

```python
# Track recent positions
if len(recent_positions) >= 10:
    xs = [p[0] for p in recent_positions]
    ys = [p[1] for p in recent_positions]
    if max(xs)-min(xs) <= 3 and max(ys)-min(ys) <= 3:
        # Area stagnation — agent in 3x3 area for 10+ turns
        self.stuck = max(self.stuck, 5)
```

## Syzygy Riding for Oscillation (April 15)

When agent oscillates between 2-3 positions, it's trapped in a syzygy pair. Don't break it — ride it outward.

```python
# Detect oscillation: 2-3 unique positions in last 12 turns
from collections import Counter
pos_counts = Counter(recent_positions[-12:])
if len(pos_counts) <= 3:
    # Syzygy detected — ride it along dominant axis
    xs = [p[0] for p in pos_counts.keys()]
    ys = [p[1] for p in pos_counts.keys()]
    if max(xs)-min(xs) > max(ys)-min(ys):
        return random.choice(['L','H'])  # horizontal syzygy
    else:
        return random.choice(['J','K'])  # vertical syzygy
```

## Oblique Strategies for Stagnation

When agent is at same position 8+ of last 12 turns, trigger creative intervention.

```python
# Stagnation: same position 8+ turns
most_common_pos, count = pos_counts.most_common(1)[0]
if count >= 8:
    # Oblique strategy: try something different
    strategies = ['s', '.', random.choice(['L','H','J','K'])]
    return random.choice(strategies)
```

## Exponential Visit Decay

Tiles die exponentially. Agent forced to find new territory.

```python
v = self.vcount.get((x,y), 1)
sc = -2.0 - v*v*0.5  # v=1:-2.5, v=2:-4, v=3:-6.5, v=4:-10, v=5:-14.5
```
