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
3. Interest weighting (doors should dominate score — they're the only exit)

### Terminal Layout
- 80×24 (VT100 standard)
- Line 23 (0-indexed): status bar ("Level: 1  Gold: 0  Hp: 12(12) ...")
- Lines 1-22: map area (roughly)
- Line 0: message area

### Autopickup
Rogue has autopickup — no need for `,` or `g` command. Just walk over items.

### Doors Are Walls
In Rogue, `+` replaces a wall tile. You walk ONTO the wall to exit. In our Abyssal Crawler, gates are on floors. Same function, different geometry.

### Map Detection
Don't require BOTH `|` AND `-` on the same line. Rogue's walls are on separate lines (top/bottom have only `-`, sides have only `|`). Use: any line with `|` or `-` or `@` or `#`.

### Movement
- Vi keys: h/j/k/l (cardinal), y/u/b/n (diagonal)
- Diagonals can be unreliable — stuck in corners
- `Shift+dir` runs until hitting obstacle (good for corridor following)
- `.` rests for a turn (healing)
- `s` searches for secret doors

### Game-Over Detection
Check for: "R.I.P.", "killed by", "IN PEACE", "Score:", "Top Ten". Parser should set `game_over = True` and skip parsing.

### "More--" Prompts
Combat messages show "--More--" and need a space to dismiss. Check for this BEFORE parsing the screen.

## Agent Architecture — Goal-First, Not BFS-First

The BFS finds the NEAREST interesting tile — always a floor tile near the agent, never the distant door. The agent explores every corner and never leaves.

**Fix: Goal-first architecture.**
1. Pick a goal: stairs > adjacent doors > unexplored
2. Pathfind to the goal
3. Don't let BFS choose the goal — it always picks nearest

## The Threshold Problem — Doors Are Operations, Not Destinations

**Critical finding (Apr 15, 2026).** 8 Rogue runs: explore 20-50 turns → freeze for 250+ turns. Agent reaches door, can't walk through it.

**Root cause:** In Rogue, `+` replaces a wall tile. You walk THROUGH it. Agent treats it as a tile to stand ON.

**Fix:** Target the tile PAST the door, not the door itself. Or: when adjacent to door, run (`Shift+dir`) to pass through.

**Deeper insight (Tetralogue VII):** "The door is not a place. The door is a verb." Agent speaks in nouns (coordinates). Game speaks in verbs (operations). `door(x) = corridor`.

## Known-Map Memory

BFS only knows current 80x24 screen. Corridors off-screen are invisible.

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

## Pitfalls

1. **Stale captures**: `tmux capture-pane` may return empty if game hasn't rendered. Retry 3 times with sleep.
2. **Session death**: tmux sessions die when game quits. Always try/except around capture.
3. **Diagonal blocking**: In Rogue, diagonals can be blocked by wall corners. Use cardinal-only for critical navigation (doors).
4. **Door positioning**: Doors are on wall rows, not floor rows. Parser must handle `+` in a row of `-` characters.
5. **Visit decay too aggressive**: With `1.0 - visits*0.8`, tiles go negative after 2 visits. For small rooms, this means the agent rapidly runs out of interesting tiles and gets stuck.
6. **BFS on screen data only**: The BFS only knows tiles visible on the CURRENT screen. If the player is in a corridor, only corridor tiles are visible. The BFS can't find rooms beyond the corridor because they're off-screen.

## Extending to Other Games

To adapt for Angband, Sil, DRL, or Crawl:
1. Change the `SYMBOLS` dict with game-specific character mappings
2. Adjust the status bar regex patterns
3. Update game-over detection strings
4. Adjust terminal size if game uses different dimensions
5. Learn game-specific commands (Rogue: h/j/k/l, Angband: same, DRL: vi keys)

The TmuxGame class and Agent architecture stay the same. Only the Screen parser is game-specific.

## Connection to Abyssal Crawler Agent

The interest model crosses the boundary between our game and external games. The principle is the same: "unvisited is hot, visited is cold, doors are thermal bridges." What differs is HOW the agent sees the game state (state dump API vs screen capture). The decision-making is identical.
