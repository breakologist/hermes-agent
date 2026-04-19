---
name: angband-agent
category: gaming
description: Angband-specific agent techniques — initialization, town navigation, store mechanics, dialog handling, progressive turn budget, AAR logging
triggers: ["angband", "town", "store", "shopping", "chunked diving", "AAR", "after-action"]
---

# Angband Agent — The Hungry Borg in Middle-earth

Use when: building or refining an AI agent that plays Angband via tmux screen capture. Covers Angband-specific pitfalls, town behavior, store mechanics, dialog handling, and run logging.

## Text Mode
```
angband -mgcu -n -uborg
```
- `-mgcu`: curses text mode (required for tmux capture)
- `-n`: start new character (skips savefile menu)
- `-uborg`: use savefile "borg" (avoids conflicting with user's save)

## Critical Pitfalls (Discovered via Trial and Error)

### 1. Vi Keys Don't Work
Angband curses mode does NOT support h/j/k/l. Tested April 2026 — vi keys are silently ignored.
**Use numpad:** 8=Up, 2=Down, 4=Left, 6=Right, 7/9/1/3=diagonals
**Or arrows:** Up/Down/Left/Right also work.

### 2. `-more-` Prompt (Lowercase, Single Dash)
Angband uses `-more-` (NOT `--More--` like NetHack). This prompt intercepts ALL input.
**Dismiss with space bar.** Agent freezes silently if not detected.
Pattern to match: `'-more-' in raw.lower()`

### 3. Character Creation Requires 'y' Key
With `-n` flag, Angband shows "New character based on previous one" confirmation.
Screen: `['Y': use as is; 'N': redo; 'C': change name/history; '=': set birth options]`
**Send 'y' to accept.** Enter does NOT work on this screen.

### 4. Cascading Dialogs
After `-more-` (space), Angband often shows follow-up dialogs:
- "Inscribe with what?" → ESC
- "Ignore which item?" → ESC
- "Inscribing 2 Books... -more-" → space, then inscribe dialog → ESC
Agent must loop dialog detection until screen clears.

### 5. Store Menus
Walking onto a store number opens the store menu. Detection:
- Frame: `+--------------------------------------+`
- Menu items: `Items`, `Action commands`, `Manage items`
- Status bar shows store name (e.g., "Black Market")
**Don't match store names** — they appear in status bar even outside stores.
Match: `'+--' in raw and 'Items' in raw and 'Action commands' in raw`
Or match: `'Store Inventory' in raw and 'Command for' in raw`
**Dismiss with ESC.**

## Town Behavior

### Store Detection
Town has 8 stores numbered 1-8 on the map:
1. General Store  2. Armory  3. Weaponsmith  4. Temple
5. Alchemy Shop  6. Magic Shop  7. Black Market  8. Home

**Sidebar digit contamination:** Sidebar text (STR:18, INT:8, DEX:18) contains digits 1-8 that get parsed as stores.
**Fix:** Only detect digits that are adjacent to `#` walls (buildings have walls, sidebar doesn't).
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

### BFS Pathfinding for Town
Direct-line movement (`_move(dx, dy)`) gets stuck on building walls in town.
**Must use BFS** to route around obstacles:
```python
def _bfs_to(self, target, s):
    """BFS pathfinding to a specific target. Returns first step or None."""
    all_pass = s.floors | self.known_floors
    for sx, sy, _ in s.stores:
        all_pass.add((sx, sy))
    # BFS from player to target...
```

### Town Visit Order
1. Visit all unvisited stores (walk to store number via BFS)
2. Enter store (automatic when stepping on number)
3. ESC to leave store menu
4. Mark store as visited
5. Find `>` stairs
6. Descend

## Dungeon Behavior

### Stair Priority
- `>` (down): PRIORITY — always descend when visible and HP > 30%
- `<` (up): FALLBACK — only go up after turn budget exhausted or no `>` found

**Detect separately:**
```python
self.stairs_up = None   # position of '<'
self.stairs_down = None # position of '>'
```

**Track across turns** — stairs may scroll off screen:
```python
if s.stairs_down: self.known_stairs = s.stairs_down
if s.stairs_up: self.known_stairs_up = s.stairs_up
```

### Progressive Turn Budget
More visits to a level = more turns allowed (player gets stronger with gear/XP):
```python
def _turn_budget(self, depth):
    visits = self.level_visits.get(depth, 1)
    return 200 + (visits - 1) * 75  # 200, 275, 350, 425, ...
```

When `level_turns > budget` and no `>` found, go up via `<` to town.
Dungeon regenerates on return — fresh layout, fresh stair placement.

### Interest Scoring
```python
# Unvisited tiles:
is_down: +25.0  # > always hot
is_store: +30.0  # stores are very interesting in town
is_item: +10.0
is_up: +2.0     # < only mildly interesting

# Visited tiles:
is_down: +20.0  # > stays hot
is_item: +5.0
# Everything else: -2.0 - visits × 0.5 (decays fast)
```

## Run Logging & AAR

### JSONL Log
Each run appends to `~/.angband_runs.jsonl`:
```json
{"run": 5, "timestamp": "...", "class": "Warrior",
 "total_turns": 600, "max_depth": "L1", "max_depth_ft": 50,
 "death_cause": "timeout", "stores_visited": [1,2,3,4,5,6,7,8],
 "max_stuck": 62, "events": [...]}
```

### Periodic Checkpoint
`timeout` sends SIGKILL which bypasses try/finally. Save checkpoint every 100 turns:
```python
if t % 100 == 0:
    with open('~/.angband_runs_checkpoint.json', 'w') as f:
        json.dump(self.run_data, f)
```

### AAR Generator
`angband_aar.py` reads JSONL + checkpoint, generates markdown reports with:
- Depth progression, turns, stores visited
- Cross-run patterns (depth trend, stuck frequency)
- Bug frequency analysis

## ANSI Color Support

Angband GCU outputs 256-color ANSI. Capture with:
```python
tmux capture-pane -t session -p -e  # -e preserves ANSI codes
```

Key colors: 152=pale blue (walls), 145=light gray (floors), 188=near white (dots), 160=red (monsters), 51=cyan.

Parse with `parse_ansi_line()` — extract `(fg_color, bg_color, char)` tuples.

## Pitfalls

1. **Orphaned processes:** Each `tmux kill-session` leaves an angband process. Always `pkill -9 angband` when cleaning up.
2. **SIGKILL:** `timeout` sends SIGKILL (not SIGTERM). try/finally doesn't run. Use periodic checkpoints.
3. **Store name false positives:** "Black Market" appears in status bar outside stores. Don't match store names for dialog detection.
4. **BFS `px` not defined:** When adding new BFS methods, ensure `px, py = s.pos` is at the top.
5. **Town depth detection:** Status bar shows "?" for depth in town, not "Town". Check `len(s.floors) > 300` as fallback.
6. **Map edge stuck:** Agent can walk to (x, 0) at top of map and get stuck. Add boundary awareness.
7. **Wall collision messages:** "There is a wall in the way!" triggers dialog detection if not explicitly excluded. Add `'wall in the way' in raw` → `return False` to `_check_dialog`.
8. **Store visit oscillation:** Agent enters store → browses → leaves → BFS routes back. Fix: `visited_stores` set by store NUMBER (not position). Mark visited when agent is ADJACENT (within 1 tile), not just ON the store. BFS excludes visited stores from `all_pass`. Reset `visited_stores` on town return.
9. **Tiny room search:** Agent lands in 4-tile rooms with no `>`. Searches aren't triggered because agent isn't "stuck" (it walks between tiles). Add proactive search: `if len(s.floors) < 20 and not s.stairs_down: return 's'` 50% of the time.
10. **Stuck vs stairs conflict:** Search-on-stuck overrides stairs commitment. Fix: reset stuck counter when stairs visible (`if s.stairs_down or s.stairs_up: self.stuck = 0`).
11. **Sidebar overwrites stairs position:** "Up staircase" in sidebar sets `stairs_up = player_pos` which is WRONG when player is adjacent but not ON stairs. This causes "I see no up staircase here." Fix: only use sidebar fallback when map parser didn't find `<`/`>`.
12. **`_is_town` must match L1:** DL1 pockets show "L1" not "Town" in sidebar. If `_is_town` returns False, agent tries `<` on surface (does nothing). Fix: match depth_label=='L1' and depth_ft==50.
13. **Direction prompts not detected:** "Direction or <click>" isn't in DIALOG_PATTERNS. Agent freezes on pending prompt. Fix: add 'Direction or', 'Direction:', 'which direction' to dialog patterns.

## Class-Aware Shopping (April 16)

Warriors can't use spellbooks. Skip patterns:
```python
skip_patterns = ['Book of', 'Spellbook', 'Intelligence', 'Wisdom', 'Staff', 'Wand', 'Rod']
```

Buy priorities (with max prices):
```python
buy_patterns = [
    ('Cure Light Wounds', 25), ('Word of Recall', 150),
    ('Ration', 5), ('Torch', 2), ('Flask of oil', 3),
    ('Phase Door', 15), ('Identify', 200),
    ('Strength', 800), ('Dexterity', 800), ('Constitution', 800),
]
```

When in buy prompt, prefer useful items over generic:
```python
if any(u in line.lower() for u in ['cure', 'recall', 'ration', 'torch', 'lantern', 'oil', 'phase']):
    return letter  # buy this one first
```

### Doors — Treat as Floors (Critical Fix)

The `+` character (closed door) must be added to `self.floors` during parsing. Without this, BFS cannot route through doors because `passable()` only returns `self.floors`. The agent gets trapped in tiny rooms adjacent to doors it can't "see" as walkable.

**Before fix:** Agent explored 3 tiles then froze for 500 turns, digging walls.
**After fix:** Agent explored 79 floors, found corridors, properly traversed the level.

```python
# In parser — doors are walkable:
elif ch in self.DOORS:
    self.doors.append((x, y))
    if ch in self.CLOSED_DOORS:
        self.closed_doors.append((x, y))  # track for interest scoring
    self.floors.add((x, y))  # treat all doors as walkable — bump to open
```

In Angband, walking into a closed door opens it automatically. The agent just walks into `+` and it opens. No `o` + direction needed.

Also works on the `_passable()` method — closed doors are already in floors, so BFS routes through them.

### Parser Character Set Collision — `+` in ITEMS (Critical Bug, April 17)

The `+` character appears in MULTIPLE character sets: `MONSTERS`, `ITEMS`, and `DOORS`. The parser checks in order: `@` → `ITEMS` → `FLOOR` → `DOORS` → `WALLS`. Since `+` was in `ITEMS`, it was caught as an item *before* reaching `DOORS`. Result: `s.closed_doors` was always empty, so the `'o' + direction` door-opening handler was dead code.

**Symptom:** Agent stuck for 292+ turns next to a visible closed door, never opening it. The door handler exists but never fires because `closed_doors` is empty.

**Fix:** Remove `+` from `ITEMS`:
```python
# BEFORE (broken):
ITEMS = set('!?)\]/\\=+|')  # + is caught before DOORS check

# AFTER (fixed):
ITEMS = set('!?)\]/\\=|')  # + removed — it's a closed door
```

**Verification:**
```python
print('+ in ITEMS:', '+' in AngbandScreen.ITEMS)        # Must be False
print('+ in DOORS:', '+' in AngbandScreen.DOORS)        # Must be True
print('+ in CLOSED_DOORS:', '+' in AngbandScreen.CLOSED_DOORS)  # Must be True
```

**Lesson:** When a character has multiple meanings in Angband's display, the parser check order determines classification. Always audit character set membership for overlaps. The `MONSTERS` set also contains `+` but isn't checked in the parser's if/elif chain, so it's harmless there — but `ITEMS` was the culprit.

### Door Opening — `o` + Direction vs Walking

Two ways to open a closed door in Angband:
1. **Walk into it** — automatic. The agent just sends a movement key toward the `+` and Angband opens it.
2. **`o` + direction** — explicit open command. Useful when you want to open without moving.

The agent currently uses approach 1 (walking) because doors are in `self.floors` so BFS routes through them. The `'o' + direction` handler at line 900 fires as a secondary optimization when the agent is adjacent to a closed door and hasn't moved yet.

### Hidden Doors — Search Strategy

- `s` command searches all 8 adjacent tiles
- Warriors have low search skill (~11%), need many searches
- Parse `+` (closed door) and `'` (open door) as walkable floors
- Doors are high-interest BFS targets (+15)
- When stuck: search 70% of the time, move 30%
- When in tiny room (<20 floors) without stairs: search 50% proactively
- When doors appear after searching: walk toward them immediately

### The Alter Key — What Is Diggable (April 17)

The `+` key (Alter) tests and digs walls. Behavior depends on the tile character:
- **Colon rubble** → clears (requires some digging power)
- **Dollar sign in walls** → treasure vein (gems or ore). Dollar also appears as floor gold item.
- **Hash regular wall** → can be broken but requires high digging power (pickaxe, dwarven race)
- **Town hash walls** → permanent. Cannot be broken. Agent wasted 500 turns before discovering this.
- **Hidden doors** → revealed by search key, NOT by alter key

**Strategy:** In town, skip digging entirely. In the dungeon, search first. Only use alter on colon rubble and dollar signs. Regular hash walls need a pickaxe or high strength to break quickly.

### Dollar Signs — Context Dependent

Dollar sign characters have three possible meanings:
1. Gold on floor (item, walkable)
2. Treasure vein in wall (breakable with alter)
3. Additional meaning (user to confirm — spoilers territory)

**Parser heuristic:** Count adjacent hash/colon/dollar tiles. If three or more are wall-type, treat as treasure vein. Otherwise treat as floor gold item.

### Town Walls Are Permanent

Town walls are permanent architecture. The agent spent 500 turns on level zero attempting to dig walls with a dagger. Town walls will never break. When stuck in town: walk randomly, search for hidden passages, or head for stairs.

**Detection method:**
```python
def _can_dig(self, s):
    """Town walls are permanent, dungeon walls are diggable."""
    return not self._is_town(s)
```

Guard ALL digging with `_can_dig(s)`. In town, the stuck handler should search and walk randomly instead of digging. The escape handler checks `_can_dig` before adding regular walls to dig targets.

### `_is_town()` Must Match DL1 Pockets (April 18)

The sidebar shows "50' (L1)" when in a pocket on DL1, NOT "Town". The original check `depth == 'Town'` failed, causing the agent to try going UP from DL1 (which does nothing — you're at the surface).

**Fix:** Match 'L1' and depth_ft==50 as town:
```python
def _is_town(self, s):
    depth = s.status.get('depth_label', '')
    depth_ft = s.status.get('depth_ft', 0)
    return depth in ('Town', 'L1') or depth_ft == 50 or len(s.stores) > 0 or len(s.floors) > 300
```

**Critical consequence:** If `_is_town` returns False for L1 pockets, `_go_up_stairs` sends `<` which does nothing on the surface. The agent sits there for 70+ turns sending `<` with no effect.

## Town Behavior — Streamlined (April 17)

### Skip Shopping, Just Dive

Starting gear (three rations, wooden torch, flask of oil) is enough for level one. With 143 gold there is nothing worth buying. Come back with loot.

```python
# In town: BFS straight to down stairs, descend immediately
if self._is_town(s) and s.stairs_down:
    if s.pos == s.stairs_down:
        return '>'
    step = self._bfs_to(s.stairs_down, s)
    if step:
        return step
```

Stairs are always on the outer wall of town. BFS finds them.

### Flee Town Hostiles

Dogs, drunks, Grip (unique), Wolf — all lethal at level one and two. Never fight in town. Flee all adjacent monsters when in town:

```python
for mpx, mpy, ch in s.monsters:
    if s.adj(s.pos, (mpx, mpy)):
        if self._is_town(s) or pct < 0.5:
            return self._move(px - mpx, py - mpy, s)  # flee
```

## Save-and-Quit When Trapped

If stuck 50+ turns in a tiny room with no doors, no treasure, no breakable targets:
- Save the character (capital Q, then y, then at-sign)
- Start a new game with a different name
- You can load the saved character later to investigate

```python
def _save_and_quit(self):
    self.game.send('Q')
    time.sleep(0.5)
    self.game.send('y')
    time.sleep(0.5)
    self.game.send('@')
    time.sleep(2)
    for _ in range(5):
        self.game.send(' ')
        time.sleep(0.2)
```

### Unique Character Names

Using the same username overwrites the save every run. Use unique names per run:

```python
names = ['borg', 'crawler', 'maw', 'dive', 'grip', 'worm', 'drift', 'slab',
         'hunger', 'depth', 'spoor', 'gnaw', 'rift', 'silt', 'mire', 'bone']
name = f"hungry-{names[run_num % len(names)]}-{run_num + 1}"
cmd = f'angband -mgcu -n -u{name}'
```

## Monster Parser — Sidebar Contamination (FIXED April 17)

The screen parser's `ch.isalpha()` caught Angband's sidebar text as monsters.
Reported M:28-81 when real monsters might be 0-5.

### Root Cause (User Correction)
The sidebar is on the LEFT, columns 0-12 (race, class, stats). The `x < 66` check was on the STORES branch, not the monster branch. The monster parser had NO column restriction at all — it caught lowercase letters at ANY column, including sidebar text like "t" from "STR: 18", "a" from "Warrior", "e" from "Level".

### Fix: Zone-Aware Parsing
```python
# Map area: rows 0-20, columns 13-79
# Sidebar: columns 0-12 (always skip)
# Status: rows 21-28 (Fed, Speed, etc. — skip)
elif (ch.islower() or ch.isupper()) and x >= 13 and y <= 20:
    self.monsters.append((x, y, ch))
```

### Key Insight
Each entity type (stores, monsters, items) needs its OWN zone guard. The `x < 66` on stores doesn't apply to monsters. Character set overlaps must be audited per entity type.

### Cross-Roguelike Pattern
Every terminal roguelike has scrolling map + fixed UI panels. Define zones explicitly:
- **Angband**: left sidebar cols 0-12, map cols 13-79, status rows 21-28
- **DCSS**: right panel, map left, messages bottom
- **Brogue**: bottom panel with border ╔═══

See also: `roguelike-screen-zones` skill for generic zone detection.

### C Command Backstop (Validation)
The screen parser can still inflate monster counts from status text at rows 21-22. Use Angband's `C` (nearby creatures) command as a backstop — call every 5 turns when screen count > 3, and replace inflated counts with real data.

```python
# In main loop, after creating AngbandScreen:
if len(s.monsters) > 3 and t % 5 == 0:
    real = self._scan_nearby_monsters()  # sends 'C', parses result
    if len(real) < len(s.monsters) and s.pos:
        dir_to_delta = {'north':(0,-1), 'south':(0,1), 'east':(1,0), 'west':(-1,0),
                        'NE':(1,-1), 'NW':(-1,-1), 'SE':(1,1), 'SW':(-1,1)}
        px, py = s.pos
        s.monsters = []
        for m in real:
            d = dir_to_delta.get(m['direction'], (0,0))
            mx = px + d[0] * m['distance']
            my = py + d[1] * m['distance']
            s.monsters.append((mx, my, m['char']))
```

The `_scan_nearby_monsters()` method sends `C`, captures "a Kobold (3 north)", parses with regex. Dismisses with Escape. More reliable than screen parsing but adds latency — only call when needed.

### Before/After
- **Before**: M:28-81 (sidebar characters counted as monsters)
- **After**: M:0-5 (real map monsters only, C validated every 5 turns)
- **Added**: uppercase monster detection (was missing entirely — only lowercase caught)

## Secret Door Discovery (Confirmed Working, April 17)

The `s` (search) command successfully revealed a hidden door. Message parsing caught "You have found a secret door." The agent walked through it.

**Key insight**: search reveals hidden doors, but only near walls. The agent needs to search wall-adjacent positions systematically, not just when stuck.

### Perimeter Search Logic
When all visible floors are explored and no `>` stairs found:
1. Find floor tiles adjacent to walls
2. BFS to nearest unsearched wall-adjacent tile
3. Send `s` at that position
4. Repeat until all wall-adjacent tiles searched
5. Then go up

### Secret Door as Item False Positive
"You have found a secret door" matches the item pickup regex. Filter it out:
```python
if 'secret door' not in item.lower():
    self.items_found.append(item)
```

## Interest Decay for Visited Floors (April 17)

Strong decay makes visited empty floors invisible quickly:
```python
v = self.vcount.get((x, y), 1)
sc = -2.0 - (v - 1) * 2.0  # first visit -2, second -4, third -6...
```
Stairs and items stay interesting even when visited.

## BFS Tie-Breaking (April 17)

BFS always picked the first tile with highest score, causing oscillation.
Fix: 30% randomization on equal-score tiles:
```python
if sc > best_s or (sc == best_s and random.random() < 0.3):
    best = (cx, cy); best_s = sc
```

## Level Regeneration Reset (April 17)

When level regenerates (going up and coming back down), reset exploration state:
```python
self.visited = {s.pos}
self.vcount = {}
self.recent_positions = deque(maxlen=20)
```

## Reroll Strategy — Search First (April 17)

Don't reroll tiny rooms immediately. Search 15 turns first, try digging rubble:
```python
if s.stairs_up and s.pos == s.stairs_up and self.level_turns > 15:
    # Try digging adjacent rubble/treasure
    if dig_targets and self.level_turns < 25:
        return '+' + random.choice(dig_targets)
    # Searched and dug, still nothing — reroll
    return '<'
elif s.stairs_up:
    # Walk to stairs, searching along the way
    if self.level_turns % 3 == 0:
        return 's'
    return self._move(...)
```

## Stuck Recovery — Must Be at Top of Decision Tree (April 17)

Stuck > 100 check must be OUTSIDE the `walkable_neighbors < 2` block:
```python
# 0.7a GENERAL STUCK RECOVERY — applies to ALL rooms
if self.stuck > 100 and s.stairs_up and not self._is_town(s):
    return self._go_up_stairs(s) or 's'
```
Rooms with 3+ walkable neighbors never triggered the old check.

## Walk Toward Stairs When BFS Fails (April 17)

When BFS can't reach stairs, walk directionally instead of save-and-quit:
```python
step = self._bfs_to(target, s)
if step:
    return step
# Can't BFS — walk toward stairs direction
return self._move(target[0] - px, target[1] - py, s)
```

## Ladder Data — Equipment Patterns (April 17)

Scraped 500 listings + 30 dumps from angband.live. Key findings:
- L1-3: avg 3 items (torch, weapon, body)
- L9-15: avg 7 items, all slots filling
- Cloak at 57% by L9-15 (agent should prioritize)
- Shield at 71%, boots at 71%
- Rogues dominate the ladder (25/50 winners)
- Diving: 21% cautious, 79% grind-heavy
- Fastest winner: 14,713 turns (Hobbit Mage)

## Food — Not Yet Tested at Scale (April 17)

Agent max run: 3511 turns. Fed went 89→65. Fallback eat every 2000 turns fires correctly. No starvation deaths yet — runs too short. At ~1% Fed per 150 turns, starvation would take ~12,000 turns.

## Don't Restrict Monster Detection to `MONSTERS` Set (April 17)

The `MONSTERS` set includes ALL letters (a-z, A-Z) plus symbols. Using `ch in self.MONSTERS` doesn't filter sidebar text. Use `ch.islower()` + proximity instead.

## File Locations
- Agent: `~/numogame/angband_agent.py` (~1408 lines)
- Ladder scraper: `~/numogame/scrape_angband_ladder.py`
- Run data: `~/.angband_runs.jsonl`
- Ladder data: `~/.hermes/angband_ladder_listings.json`, `~/.hermes/angband_early_deaths.json`
- Wiki: `~/.hermes/obsidian/hermetic/wiki/angband-agent-progress.md`, `angband-ladder-analysis.md`

Descending without exploring the current floor first often lands the agent in a three-tile pocket with no exits. The agent should explore enough to understand the floor layout before committing to stairs.

```python
# Only walk to stairs after exploring a bit
if s.adj(s.pos, s.stairs_down) and self.level_turns > 30:
    return self._move(stairs.x - px, stairs.y - py, s)
```

On level one: the agent needs to find stairs while exploring the room it is in, not rush to stairs and land in a dead end.

## Terminal Size

Angband map is roughly 66 by 21 plus status bar, so minimum 79 by 25. Use 80 by 32 for full visibility:
```python
tmux new-session -d -s session -x 80 -y 32 -c ~/ angband -mgcu -n -uname
```

## Escape Handler — Tiny Pocket Detection

When agent is stuck in a tiny pocket (two or fewer walkable neighbors) for more than five turns:

```python
walkable = [(px+dx, py+dy) for dx, dy in [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,-1),(-1,1),(1,1)]
            if (px+dx, py+dy) in s.floors]
if self.stuck > 5 and len(walkable) < 2:
    # 1. Break rubble and treasure walls only (not regular walls in town)
    # 2. If no breakable targets and stuck 50+: save and quit
    # 3. Search for hidden doors every third turn
```

### Escape Priority Order

```python
# 1. Dig rubble/treasure if adjacent
# 2. Save-and-quit at stuck 50+ in tiny room (<=25 floors)
# 3. Search for hidden doors every third turn
# 4. Walk randomly to find new search angles

# Save-and-quit fires REGARDLESS of diggable targets
# Walls might be diggable but take forever with a weapon
if self.stuck > 50 and len(s.floors) <= 25:
    self._save_and_quit()
    self._end_run(death_cause='saved')
    return None  # signal to main loop
```

## Oscillation Fix — Go Up When Explored

When the agent has visited ALL visible floors and no `>` stairs are found, it wastes 500+ turns oscillating between 3 positions at corridor ends. The fix: go UP `<` immediately instead of waiting for oscillation detection.

```python
# In BFS explore section:
visible_unvisited = s.floors - self.visited
if not visible_unvisited and not s.stairs_down:
    if s.stairs_up:
        if s.pos == s.stairs_up:
            return '<'
        return self._move(s.stairs_up[0] - px, s.stairs_up[1] - py, s)
    if self.known_stairs_up:
        if s.pos == self.known_stairs_up:
            return '<'
        step = self._bfs_to(self.known_stairs_up, s)
        if step:
            return step
    # No up stairs — save and quit
    self._save_and_quit()
    return None
```

This fires as soon as the level is fully explored, before oscillation detection at section 5.7.

## HP-Gated Descent

Don't descend with low HP. Town drunks (Zuiquan) and out-of-depth monsters are lethal.
```python
if s.stairs_down and pct > 0.6:  # Only descend at >60% HP
```
Died at turn 197 descending to L1 with 13/20 HP.

## Death Detection Fix

Angband shows "RIP" WITHOUT periods (not "R.I.P.").
```python
if any(p in raw for p in ['R.I.P.', 'RIP', 'killed by', 'Rest In Peace', 'the Rookie']):
```

## Turn Logging for Freeze Debugging

When the agent freezes, you need to see the screen state and decision history. Log every turn to a JSONL file:

```python
class TurnLogger:
    def __init__(self, path='/tmp/angband_turns.jsonl'):
        self.f = open(path, 'w')
    
    def log(self, **kwargs):
        self.f.write(json.dumps(kwargs) + '\n')
        self.f.flush()
    
    def close(self):
        self.f.close()
```

Log per turn:
- `t`: turn number
- `x, y`: player position
- `hp`: current HP
- `d`: depth label
- `st`: stuck counter
- `fl`: floor count
- `dr`: doors visible
- `act`: action taken
- `nearby`: 11-line screen capture around player (17 chars wide)

When the agent freezes, analyze with:
```python
# Position changes show where the agent moved
# Stuck counter shows oscillation patterns
# Screen state shows what the agent saw
```

## Status-Bar Stair Detection

When `<` or `>` aren't visible (tiny rooms), status bar shows "Up staircase" or "Down staircase":

**CRITICAL: Do NOT overwrite map-parsed stairs position with player position.**

The sidebar says "Up staircase" when the player is ADJACENT to stairs, not necessarily ON them. The old code did `self.stairs_up = self.pos` which overwrote the correct `<` position with the player's position. Then `_go_up_stairs` checked `s.pos == s.stairs_up` (always true) and sent `<` when NOT on stairs → "I see no up staircase here."

**Fix:** Only use sidebar fallback when map parser didn't find the stairs:
```python
if 'Up staircase' in line or 'up staircase' in line:
    if not self.stairs_up:
        self.stairs_up = self.pos  # fallback — map parser takes priority
if 'Down staircase' in line or 'down staircase' in line:
    if not self.stairs_down:
        self.stairs_down = self.pos
```

Map parser finds actual `<`/`>` positions from the map display. Sidebar just confirms the stairs EXIST on this level.

## Go-Up-Stairs Blocked by Pending Message (April 18)

The agent sends `<` repeatedly but never goes up. Position stays stuck, stuck counter climbs past 70.

**Root cause:** Angband may have a pending message ("You can't go up from here", "I see nothing there", etc.) that blocks ALL input. The agent's `<` keystrokes queue up behind the message instead of executing.

**Fix:** Add direction prompts to DIALOG_PATTERNS so they're detected and dismissed:
```python
DIALOG_PATTERNS = [
    # ... existing patterns ...
    'Direction or', 'Direction:', 'which direction',
]
```

The dialog detection loop sends Escape to dismiss prompts. Without this, "Direction or <click> (Escape to cancel)?" intercepts all subsequent input.

### Direction Prompt Source

Direction prompts come from `+` (Alter) or `o` (Open) commands. The `_handle_escape_pocket` handler sends `+` + direction to dig rubble. If the rubble position is wrong or the dig fails, the next turn starts with a pending direction prompt.

**Prevention:** Don't send `+` or `o` commands in town (walls are permanent, no doors to open in pockets).

## DL1 Pocket Escape Flow (April 18)

On DL1 (surface/town level), going UP (`<`) does nothing because you're at the surface. The agent must find `>` to descend into the dungeon.

But DL1 has POCKET ROOMS — tiny dead-end chambers connected to town via `<` stairs. These pockets have no `>` stairs. The escape flow:

```
Pocket (no >) → go UP via < → reach Town → find > → descend to DL2
```

**Implementation in `_go_up_stairs`:**
```python
def _go_up_stairs(self, s):
    if self._is_town(s):  # DL1 pocket or town
        if s.stairs_down:
            # > visible — descend
            if s.pos == s.stairs_down:
                return '>'
            return self._bfs_to(s.stairs_down, s)
        # No > visible — go UP to reach town (pockets connect via <)
        if s.stairs_up:
            if s.pos == s.stairs_up:
                return '<'
            return self._bfs_to(s.stairs_up, s)
        return self._search_wall(s)
    # Normal levels: go up to regenerate
    # ...
```

### Pocket Room Type Detection

Classify rooms to handle pockets early:
```python
def _room_type(self, s):
    if self._is_town(s):
        return 'town'
    n = len(s.floors)
    doors = len(s.doors) + len(s.closed_doors)
    if n <= 12 and doors == 0 and not s.stairs_down:
        return 'pocket'
    if n <= 8 and not s.stairs_down:
        return 'pocket'
    return 'room'
```

### Pocket Handler — Early Escape

Fire pocket detection BEFORE stuck recovery in the handler chain:
```python
handlers = [
    ('town',        lambda: self._handle_town(s, pct)),
    ('eat',         lambda: self._handle_eat(s, pct)),
    ('pocket_room', lambda: self._handle_pocket_room(s, pct)),  # BEFORE stuck handlers
    ('reroll',      lambda: self._handle_tiny_room_reroll(s, pct)),
    # ...
]
```

Pocket handler fires at stuck >= 5 (faster than stuck recovery at stuck > 50):
```python
def _handle_pocket_room(self, s, pct):
    rt = self._room_type(s)
    if rt != 'pocket':
        return None
    if self.stuck < 5:
        step = self._bfs(s)
        if step: return step
        return self._search_wall(s)
    # Stuck 5+ in pocket — go up
    self.last_pocket_stairs = s.stairs_up
    return self._go_up_stairs(s) or 's'
```

### Pocket Loop Prevention

After going up from a pocket, the level regenerates. The agent might land in ANOTHER pocket. Track the last pocket's stairs position to detect loops:
```python
def _pocket_is_new(self, s):
    if s.stairs_up == self.last_pocket_stairs:
        return False  # same pocket
    return True
```

When in the same pocket again, walk a random direction first before going up again:
```python
if not self._pocket_is_new(s):
    if self.stuck < 5:
        return None  # let BFS try
    # Walk random direction to change position
    dirs = [(0,-1,'8'),(0,1,'2'),(-1,0,'4'),(1,0,'6')]
    random.shuffle(dirs)
    for dx, dy, ch in dirs:
        if (px+dx, py+dy) in s.floors:
            return ch
    self.last_pocket_stairs = s.stairs_up
    return self._go_up_stairs(s) or 's'
```

## Oscillation Detector — Tightened (April 18)

The old detector fired at 12 turns / 4 unique positions. Too slow — the agent wastes turns oscillating.

**Fix:** Fire at 8 turns / 3 unique:
```python
def _handle_oscillation(self, s):
    if len(self.recent_positions) < 8:
        return None
    if len(set(self.recent_positions)) > 3:
        return None
    # Break the loop...
```

## 1-Tile Room — Immediate Reroll (April 18)

A room with exactly 1 floor tile (the player's position) and no doors is an inescapable pocket. The agent should go up immediately, not wait for stuck > 50.

```python
# In tiny room check — add 1-tile detection:
if not self._is_town(s) and not s.stairs_down and len(s.floors) <= 2:
    if s.stairs_up:
        self.game.send(' ')  # clear pending messages
        time.sleep(0.1)
        if s.pos == s.stairs_up:
            return '<'
        return self._move(s.stairs_up[0] - px, s.stairs_up[1] - py, s)
```

## Visual Debug — Human Eyes in the Loop (April 18)

The user wants to SEE what the agent sees. JSONL logs aren't enough — the user needs visual feedback to trust the parser.

**Quick approach:** Write a map snapshot to a file every N turns:
```python
if t % 50 == 0:
    with open('/tmp/angband_map_debug.txt', 'w') as f:
        for i, line in enumerate(s.lines):
            if 0 <= i < 25:  # map region only
                f.write(line[:66] + '\n')
        f.write(f"\nPos: {s.pos} Floors: {len(s.floors)} Walls: {len(s.walls)} ")
        f.write(f"Monsters: {s.monsters} Stairs: up={s.stairs_up} down={s.stairs_down}\n")
```

User can `cat /tmp/angband_map_debug.txt` to see the agent's view.

## Message Parsing for AAR

Parse top 3 lines for kills, items, artifacts:
```python
# Kills: "You have slain the Kobold"
kills = re.findall(r'(?:slain|destroyed)\s+(?:the\s+)?([A-Z][a-z]+)', line)
# Items: "You have found a Potion of Cure Light Wounds"
items = re.findall(r'You have.*?(?:found|picked up)\s+(?:a|an|\d+)\s+(.+?)(?:\.|$)', line)
# Artifacts: shown in {brackets}
artifacts = re.findall(r'\{([^}]+)\}', line)
```

## Grok's Strategic Advice (Key Points)
- **Chunked diving:** Dive 5-15 levels, recall to town, resupply, redive
- **Town routine:** Sell junk → Buy recalls/healing → Stash in Home → Rest → Redive
- **Depth > everything:** Deeper kills give exponentially better XP/loot
- **Free Action by DL ~20, rPoison by DL ~30** — mandatory milestones
- **Borg vs Learner:** Borg optimizes for survival; our agent learns through exploration and failure

## File Locations
- Agent: `~/numogame/angband_agent.py` (~1100 lines)
- Display: `~/numogame/angband_display.py` (ANSI color capture)
- AAR: `~/numogame/angband_aar.py` (run analysis)
- Memory: `~/.angband_memory.json` (cross-run persistence)
- Runs: `~/.angband_runs.jsonl` + `~/.angband_runs_checkpoint.json`
- Turn log: `/tmp/angband_turns.jsonl` (freeze debugging)
- Saves: `~/.angband/Angband/save/` (one file per character name)
- Grok conversation: `~/.hermes/obsidian/hermetic/raw/Grok Angband conversation.md`

## Go-Up-Stairs Instead of Save-and-Quit (April 17)

When stuck in a tiny room or level fully explored, navigate to `<` stairs and go up instead of save-and-quit. This regenerates the level when you come back down. Save-and-quit only as a last resort when no up stairs are known.

```python
def _go_up_stairs(self, s):
    """Navigate to up stairs and go up — regenerates the level."""
    target = s.stairs_up or self.known_stairs_up
    if target:
        if s.pos == target:
            return '<'
        step = self._bfs_to(target, s)
        if step:
            return step
        return self._move(target[0] - px, target[1] - py, s)
    # No known up stairs — save and quit (rare)
    self.game.send('Q'); time.sleep(0.5)
    self.game.send('y'); time.sleep(0.5)
    self.game.send('@'); time.sleep(2)
    return None
```

Use this in all stuck/explored situations:
- Stuck 50+ in tiny room (≤25 floors) → `self._go_up_stairs(s)`
- Stuck 50+ in town with no path → `self._go_up_stairs(s)`
- All floors explored, no `>` stairs → `self._go_up_stairs(s)`
- Dead end with no doors, no treasure → `self._go_up_stairs(s)`

### Post-Stairs Wandering

After going up and coming back down, the agent lands at the `<` stairs again. If it descends immediately, it lands in the same tiny pocket. Walk away first:

```python
if s.pos == s.stairs_down and self.level_turns < 20:
    # Walk away from stairs before descending
    dirs = [(0,-1,'8'),(0,1,'2'),(-1,0,'4'),(1,0,'6'),
            (-1,-1,'7'),(1,-1,'9'),(-1,1,'1'),(1,1,'3')]
    random.shuffle(dirs)
    for dx, dy, ch in dirs:
        nx, ny = s.pos[0]+dx, s.pos[1]+dy
        if (nx, ny) in s.floors:
            return ch  # walk away first
return '>'  # descend after wandering
```

### All-Explored Detection

When BFS finds no unvisited floors and no `>` stairs, go up immediately. Don't wait for oscillation detection (which requires 8+ turns of bouncing).

```python
# In BFS explore section:
visible_unvisited = s.floors - self.visited
if not visible_unvisited and not s.stairs_down:
    return self._go_up_stairs(s) or step  # fallback to BFS step
```

## Search Key — `s` IS Search (April 17)

**CRITICAL CORRECTION:** In vanilla Angband 4.2's original keyset, `s` = Search (searches all 8 adjacent tiles for hidden doors/traps). No direction needed.

The agent previously thought `s` was "Aim a wand" and used `+` + direction (Alter/tunnel) instead. This was wrong:
- `s` = Search (no direction, searches all adjacent)
- `a` = Aim a wand (not `s`)
- `+` + direction = Alter (tunnels walls, disarms traps, bashes doors)
- `T` + direction = Tunnel

**Verification method:** Start Angband, look at status bar. "Searching 11%" confirms `s` is Search.

**Fix in `_search_wall`:**
```python
def _search_wall(self, s):
    """Search for hidden doors — vanilla Angband original keyset: 's' searches ALL adjacent tiles.
    No direction needed. '+' + direction is Alter (tunnel/trap/disarm) — NOT search."""
    return 's'
```

**Why this matters:** Without a pickaxe, tunneling `#` walls at DL1 takes hundreds of turns. The agent was wasting 500+ turns sending `+` + direction at granite walls, thinking it was searching. The `s` command searches all adjacent tiles instantly and reveals hidden doors.

## BFS `?` Expansion for Small Rooms (April 17)

When the agent is in a small room (< 25 floors), BFS should treat adjacent `?` (unknown/unseen) tiles as passable. Without this, BFS can only walk on known floors and gets trapped when all visible tiles are visited.

```python
def _bfs(self, s):
    px, py = s.pos
    all_pass = s.passable() | self.known_floors
    if self.known_stairs: all_pass.add(self.known_stairs)
    
    # In small rooms, expand passable to include adjacent ? tiles
    if len(s.floors) < 25:
        for y in range(len(s.lines)):
            for x, ch in enumerate(s.lines[y][:66]):
                if ch == '?' and (x, y) not in s.walls and (x, y) not in self.known_walls:
                    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        if (x+dx, y+dy) in all_pass:
                            all_pass.add((x, y))
                            break
    
    # Rest of BFS as normal...
```

**Results:** Before fix: agent stuck in 3-5 tile sealed boxes (max_stuck=500). After fix: agent explores 180+ floors per level, reached L2 multiple times (max_stuck=68).

**Risk:** BFS may try to walk into `?` tiles that are actually walls. This is acceptable — the agent bumps the wall, learns it's impassable, and `known_walls` prevents revisiting. The benefit of exploring through `?` corridors far outweighs occasional wall bumps.

## Angband Symbols Reference

Complete symbol reference created at `~/.hermes/obsidian/hermetic/wiki/angband-symbols.md`. Built from actual installed Angband gamedata (`/usr/share/angband/angband/gamedata/terrain.txt`, `monster_base.txt`, `object_base.txt`). Covers terrain features, objects, monsters, original keyset commands, and digging difficulty. Linked from wiki index.

## Food — Agent Doesn't Eat (Known Issue)

The agent has rations but no eating logic. In Angband, `E` opens the eat menu and auto-selects if only one food item exists. When the `Fed` percentage drops below 50%, the agent should eat:

```python
# Add to decision tree (before flee/fight):
fed = s.status.get('fed', 100)
if fed < 50 and pct > 0.3:
    return 'E'  # eat — Angband auto-selects food
```

Without this, the agent slowly starves. Damage from starvation looks identical to monster damage in the turn log (gradual HP loss). Check `Fed` percentage in status bar to distinguish.

## Monster Types in Pockets

The `k` (kobold) is a common early-game monster that wanders into tiny pockets and kills Level 1 characters over ~15 turns. The agent's HP drops 20→3 before the `go_up_stairs` timeout fires.

Not a worm mass — worm masses (`w` or `j`) multiply rapidly. A single `k` deals consistent 1-3 damage per turn, enough to kill a Level 1 character in a pocket they can't escape from.

## Fighting More Aggressively for XP (April 17)

The agent was too conservative with fight thresholds. At L1, weak monsters (lowercase: mice `r`, bats `b`, worms `w`) do ~0-2 damage — free XP.

### Thresholds
```python
# Hunt weak monsters at HP > 25% (was 35%)
# Fight strong monsters at HP > 60% (unchanged)
# Heal at HP < 25% (was 35%) — lower since we fight more
```

### Walk Toward Monsters (Not Just Bump)
Only fighting adjacent monsters wastes opportunities. Walk toward weak monsters within 5 tiles:

```python
if pct > 0.25 and weak_monsters and not self._is_town(s):
    for mpx, mpy, ch in weak_monsters:
        if s.adj(s.pos, (mpx, mpy)):
            return self._move(mpx - px, mpy - py, s)
    # Walk toward nearest weak monster within 5 tiles
    closest = None; closest_dist = 999
    for mpx, mpy, ch in weak_monsters:
        d = abs(mpx - px) + abs(mpy - py)
        if d < closest_dist and d <= 5:
            closest = (mpx, mpy); closest_dist = d
    if closest:
        return self._move(closest[0] - px, closest[1] - py, s)
```

Same pattern for strong monsters at 3 tiles when HP > 60%.

### BFS Interest for Monsters
Add weak monsters to interest scoring so agent gravitates toward them while exploring:

```python
is_weak_monster = any(mx == x and my == y and ch.islower()
                      for mx, my, ch in s.monsters)
if is_weak_monster and not self._is_town(s):
    sc += 6.0  # weak monsters = free XP
```

## Auto-Equip — On Pickup With Fallback (April 17)

Angband auto-picks items but never equips them. Equip on item pickup (not periodic). `w` handles ALL equipment — weapons, armor, cloaks, shields, boots, rings, amulets. `W` is NOT a valid command in original keyset.

```python
# On pickup — primary
self.game.send('w')  # wield/wear ANY equippable item
time.sleep(0.15)
raw2 = self.game.capture()
if 'nothing' in raw2.lower() or 'which' in raw2.lower():
    self.game.send('Escape')
else:
    time.sleep(0.15)
    self.game.send('Escape')

# Fallback every 100 turns — catches missed pickups
if t > 0 and t % 100 == 0 and not self._is_town(s) and depth != '?':
    self.game.send('w')
    ...
```

## Reroll Strategy (April 17)

When stuck in a tiny room with no doors and no `>` stairs, the agent wasted 500 turns oscillating. The fix: go up `<` immediately to regenerate the level.

### Immediate Reroll — Tiny Room Detection
```python
# Priority check in _decide, BEFORE fight/flee/BFS:
if not self._is_town(s) and not s.stairs_down and not s.doors and len(s.floors) < 30:
    if s.stairs_up and s.pos == s.stairs_up and self.level_turns > 5:
        return '<'  # go up, regen level
    elif s.stairs_up:
        return self._move(s.stairs_up[0] - px, s.stairs_up[1] - py, s)
```

This fires at the TOP of the decision tree — before BFS, before fight, before flee. The agent recognizes "I'm in a dead room" and exits immediately.

### Multi-Stage Stuck Recovery
```python
# Stuck 100+ in ANY room (not just tiny) — go up
if self.stuck > 100 and s.stairs_up and not self._is_town(s):
    return self._go_up_stairs(s) or 's'

# Stuck 50+ in tiny room (≤25 floors) — go up
if self.stuck > 50 and len(s.floors) <= 25 and not self._is_town(s):
    return self._go_up_stairs(s) or 's'
```

**Critical:** These checks must be OUTSIDE the `walkable_neighbors < 2` block. Otherwise rooms with 3+ walkable neighbors never trigger recovery.

### Never Dig Regular Walls
Remove `_can_dig` from escape targets — regular `#` walls are undiggable without a pickaxe. Only dig:
- `:` rubble (clears with alter key)
- `$` treasure veins (gems/ore in walls)

```python
# BEFORE (wastes 500 turns on undiggable walls):
elif (nx, ny) in s.walls and self._can_dig(s): targets.append(...)

# AFTER (only diggable targets):
if (nx, ny) in s.rubble: targets.append(...)
elif (nx, ny) in s.treasure_walls: targets.append(...)
```

## Search Before Descending (April 17)

When near `>` stairs in a small room, search for hidden doors before committing to descend:

```python
elif s.adj(s.pos, s.stairs_down) and self.level_turns > 20:
    if self.level_turns % 40 == 0 and len(s.floors) < 30:
        return 's'  # search hidden doors before leaving
    self.committed_target = s.stairs_down
    return self._move(...)
```

Also reduce the descend threshold from 30 turns to 20 — the agent should dive faster once it has a feel for the room.

## Ladder Analysis — Human Play Patterns (April 17)

Scraped 6,735 dumps from angband.live/ladder. Key findings for agent behavior:

### Equipment by Level Tier
| Tier | Avg Items | Top Slots |
|---|---|---|
| L1-3 deaths | 3 | Torch (100%), Weapon (67%), Body (67%) |
| L4-8 deaths | 6 | Torch (100%), Body (100%), Cloak (50%), Ring (50%) |
| L9-15 deaths | 7.1 | Body (86%), Shield (71%), Boots (71%), Cloak (57%), Helm (57%) |
| Winners L40+ | 12 | All slots filled, Ring (187%), Ranged (100%), Cloak (100%) |

### What Agent Should Prioritize
1. **Weapon** — wield immediately on pickup
2. **Body armor** — wear first armor found
3. **Cloak** — 57% by L9-15, free AC. Agent currently doesn't track this specifically but `w` command handles it.
4. **Shield** — 71% by L9-15
5. **Boots** — 71% by L9-15
6. **Gauntlets** — 57% by L9-15

### The `w` Command
Angband's `w` command handles ALL equippable items — weapons, armor, cloaks, shields, boots, rings, amulets. Don't send `W` (not a valid command in original keyset). Just `w` + Escape.

### Death Causes (Early Game)
- Town: dogs, drunks, Grip, Fang — lethal L1-2
- L1-5: poison, trap doors, soldiers
- L5-15: Kobold archers, orcs (Grishnákh), mages, starvation
- **Starvation is a real killer** — agent needs `E` command

### Diving vs Grinding (Ladder Data)
From 487 ladder entries analyzed:
- **21% cautious** (ratio 3-10 turns per foot) — Fing won in 14,713 turns
- **79% grind heavily** (ratio >10) — median winner takes 85k turns
- Most aggressive winners: 14-30k turns (Hobbit Mage, Gnome Paladin, Half-Troll Warrior)
- **Survivorship bias**: ladder dominated by winners who ground. Fastest wins are rogues/warriors who dove hard.

**Agent implication**: "Dive hard, fight weak monsters, reroll bad floors" is closer to the aggressive-diver winning pattern. Don't add grinding logic.

### Rogues Win More
Rogues dominate the ladder (25/50 top entries). Stealth + disarming is the winning strategy for humans. Warriors are simpler for automated play.

### Fed Parsing for Eating
Angband sidebar shows `Fed XX%`. Parse and eat:
```python
# In status parsing:
m = re.search(r'Fed\s+(\d+)', line)
if m: self.status['fed'] = int(m.group(1))

# In _decide (before stairs/fight/flee):
fed = s.status.get('fed', 100)
if fed < 50 and pct > 0.25 and not self._is_town(s):
    return 'E'  # Angband auto-selects food
```
**Note**: GCU sidebar may not show Fed% until hungry. Show in status line for debugging: `Fed:{s.status.get("fed","?")}`.

Full analysis: `~/.hermes/obsidian/hermetic/wiki/angband-ladder-analysis.md`

## Angband Live Ladder — Studying Human Games (April 17)

Angband has no demo recording (unlike Doom). Study human play via the **Angband Live ladder** at `angband.live/ladder/`. Scraped 6,735 dumps. Full analysis: `~/.hermes/obsidian/hermetic/wiki/angband-ladder-analysis.md`

### Key Ladder Findings
- **Equipment by tier:** L1-3 (3 items: torch, weapon, body). L4-8 (6 items: +cloak, ring). L9-15 (7.1 items: +shield 71%, boots 71%, gauntlets 57%)
- **The `w` command handles ALL equipment** — weapons, armor, cloaks, shields, boots, rings, amulets. `W` is dead.
- **Top winners:** High-Elf Rogue (25/50), Human Warrior (20/50). Rogues win more but Warriors are simpler for bots.
- **Diving vs grinding:** 79% grind (ratio >10 turns/foot). Most aggressive winners: 14-30k turns. Median winner: 85k turns.

### Ladder Scraper
Script: `~/numogame/scrape_angband_ladder.py`. URL pattern: `ladder-browse.php?v=Angband&o={offset}&s=4` (50 per page). Individual dumps: `ladder-show.php?id={id}`, parse `<pre>` block.

## Food & Eating (April 17)

Angband sidebar shows "Fed XX%". Parse: `re.search(r'Fed\s+(\d+)', line)`. Drain: ~1% per 150 turns. Eat when Fed < 50%. Fallback: eat every 2000 turns regardless (Fed parsing may not work in all modes).

```python
fed = s.status.get('fed', 100)
if fed < 50 and pct > 0.25 and not self._is_town(s):
    return 'E'  # Angband auto-selects food
if not self._is_town(s) and self.turn > 0 and self.turn % 2000 == 0:
    return 'E'
```

## BFS Tie-Breaking — Kill Oscillation (April 17)

BFS was deterministic — always picked first tile with highest score. Multiple unvisited tiles had identical score 8.0. Agent oscillated 2-3 positions for 500+ turns.

Fix: 30% chance to replace equal-score tiles during BFS traversal:
```python
if sc > best_s or (sc == best_s and random.random() < 0.3):
    best = (cx, cy); best_s = sc
```

## Interest Decay — Strong Novelty Penalty (April 17)

Visited tiles lose interest fast. Final formula: `-2.0 - (v-1) * 2.0`. First revisit: -4. Second: -6. Stairs stay hot (+20). Items stay warm (+5). Everything else becomes invisible.

## Level Regeneration — Reset Exploration (April 17)

When level regenerates (go up + come back down), reset ALL exploration state or old layout penalizes new layout:
```python
if depth != self.last_depth:
    self.visited = {s.pos}
    self.vcount = {}
    self.recent_positions = deque(maxlen=20)
```

## Perimeter Search (April 17)

When all visible floors explored and no `>` found, walk along walls searching for hidden doors. Find wall-adjacent floor tiles, BFS to nearest unvisited one, send `s` when close. Only search, never dig regular walls.

## CANT BFS to Stairs — Walk Toward (April 17)

When BFS can't find path to visible stairs, walk directionally instead of save-and-quit:
```python
return self._move(target[0] - px, target[1] - py, s)
```

## Reroll With Search (April 17)

Before rerolling tiny room, search 15 turns and dig adjacent rubble:
- Walk to stairs, search every 3rd turn
- At stairs after 15 turns: dig rubble/treasure if adjacent (up to turn 25)
- Then reroll with `<`

## Secret Door — False Item (Parser Fix)

"You have found a secret door" matches item pickup regex. Filter: `if 'secret door' not in item.lower()`.

## Character Creation Flow (Critical Fix, April 17)

With `-n` flag, Angband shows "use as is / redo" → send 'y'. But AFTER 'y', Angband shows a **stat modification screen** (up/down to modify stats, left/right to change values). This screen has "STR:", "INT:", etc. but NO '@' character.

The agent was stuck on this screen for 60 iterations, never entering the game.

**Fix:** Send Enter immediately after 'y':
```python
elif 'use as is' in raw or 'redo' in raw:
    self.game.send('y')  # Accept character
    time.sleep(0.5)
    self.game.send('Enter')  # Confirm past stat screen
```

**Also:** Changed default dialog dismissal from 'Enter' to 'space' — more universally accepted in Angband.

### Character Summary vs Game Detection
- Character summary has "STR:", "INT:", etc. but NO '@' → send space
- Game has '@' on map AND sidebar stats → game ready
- Don't check for "STR:" alone — sidebar always shows stats during gameplay

### Character Creation Screen Flow
1. "use as is / redo" → send 'y'
2. Stat modification screen → send 'Enter' 
3. Character summary (name, race, class, stats) → send 'space' (multiple times)
4. Game ready when '@' appears with 'floor', 'town', or 'Open floor' in raw

## Uppercase Sidebar Characters as False Monsters (April 17)

Even after sidebar fix (`x >= 13, 1 <= y < 22`), uppercase characters from the game sidebar can be detected as "strong" monsters. The sidebar shows "STR: 17", "DEX: 16", etc. — the letters 'S', 'D', etc. at columns >= 13 are caught by `ch.isupper()`.

**Symptom:** MONSTERS: 1 total, 0 weak, 1 strong (always exactly 1 "strong" monster = sidebar letter)

**Mitigation:** C command backstop validates every 5 turns when count > 3. Also: the M:1 "strong" is harmless — fight logic only engages strong at HP > 60%, and the position is usually wrong (not adjacent).

**Future fix:** Could exclude known sidebar text patterns ("STR", "INT", "WIS", "DEX", "CON", "CHR", "AC", "HP", "Gold", "Level", "Title", "Race", "Class") from monster detection. Or rely entirely on C command.

## Monster Parser — Floor Adjacency Filter (Critical Fix, April 17)

Even after zone-aware parsing (x >= 13, y < 25), sidebar text still contaminates monster detection. Uppercase letters like "M" from "Melee", "S" from "Searching", "T" from "To-hit" pass all zone checks because they're at valid map coordinates.

**The fix: real Angband monsters are always adjacent to floor tiles ('.').** Sidebar text is surrounded by spaces, digits, and punctuation — never `.`.

```python
def _adj_floor(self, y, x):
    """Check if position is adjacent to a floor tile (.). Real monsters live next to floors."""
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dy == 0 and dx == 0: continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < len(self.lines) and 0 <= nx < len(self.lines[ny]):
                if self.lines[ny][nx] == '.':
                    return True
    return False
```

Applied to both lowercase AND uppercase monster branches:
```python
elif (ch.islower() or ch.isupper()) and x >= 13 and 1 <= y < 25:
    if dist <= 15 and self._adj_floor(y, x):
        self.monsters.append((x, y, ch))
```

**Before:** M:1-2 (sidebar "strong" monsters from stat display)
**After:** M:0 (only real floor-adjacent monsters)

**Key insight:** The `_adj_floor` check is the FINAL filter. Column/row restrictions eliminate most sidebar text, but the adjacency-to-floor check is what truly separates map entities from UI text. This pattern applies to any terminal roguelike where entities must be on walkable terrain.

## Character Creation Flow — 'y' Then Enter (April 17)

With `-n` flag, Angband auto-creates character, then shows:
1. "New character based on previous one" → send 'y'
2. **Stat modification screen** → send 'Enter' to confirm
3. Character summary → send 'space' to dismiss

The stat modification screen was missed — agent sat on it for 60 iterations. Detection: has "STR:", "INT:", etc. but no '@'. Sending space doesn't dismiss it — needs Enter.

**Fix:**
```python
if 'use as is' in raw or 'redo' in raw:
    self.game.send('y')
    time.sleep(0.5)
    self.game.send('Enter')  # Confirm past stat screen
```

Changed default dialog dismiss key from 'Enter' to 'space' (more universally accepted in Angband).

## _decide() Dispatcher Pattern (April 17 Refactor)

Extracted 17 named handler methods from monolithic 380-line `_decide()`. Each returns action string or None. Clean dispatcher with priority-ordered handler table:

```python
handlers = [
    ('town',        lambda: self._handle_town(s, pct)),
    ('eat',         lambda: self._handle_eat(s, pct)),
    # ... 15 more
]
for name, handler in handlers:
    action = handler()
    if action: return action
return ','
```

Benefits: each handler independently testable, priority explicit, adding new behaviors = one method + one line in table.

## Search Patience Tuning (April 17)

Warriors have ~11% search skill. Hidden doors need ~7 searches on average to reveal (1-(1-0.11)^7 = 55% chance). Agent was rerolling after 15 turns with search every 3rd turn = only 5 searches.

**Fix:** Search every other turn, reroll after 30 turns = ~15 searches per room. Also increased rubble digging window from 25 to 40 turns.

```python
if self.level_turns % 2 == 0:
    return 's'  # search every other turn
# ... reroll after 30 turns (was 15)
```

## BFS ? Expansion Column Fix (April 17)

The `?` expansion in `_bfs()` used `s.lines[y][:66]` (old column restriction). After sidebar fix, should skip cols 0-12:

```python
for x, ch in enumerate(s.lines[y]):
    if x < 13: continue  # skip sidebar
```

When the agent freezes for 500+ turns, standard output isn't enough. Log every turn to `/tmp/angband_turns.jsonl` with screen state:

```python
class TurnLogger:
    def __init__(self, path='/tmp/angband_turns.jsonl'):
        self.f = open(path, 'w')
    def log(self, **kwargs):
        self.f.write(json.dumps(kwargs) + '\n')
        self.f.flush()
    def close(self):
        self.f.close()
```

In the run loop, log after each decision:
```python
self.turn_log.log(
    turn=self.turn,
    screen_lines=self._get_nearby_screen(s),  # 11-line capture around player
    pos=s.pos, hp=s.status.get('hp', 0),
    depth=s.status.get('depth_label', '?'),
    stuck=self.stuck, floors=s.floors,
    doors=s.doors, decision=act
)
```

`_get_nearby_screen()` captures a 17×11 window around the player:
```python
def _get_nearby_screen(self, s):
    px, py = s.pos
    lines = []
    for dy in range(-5, 6):
        row = ''
        for dx in range(-8, 9):
            nx, ny = px + dx, py + dy
            if 0 <= ny < len(s.lines) and 0 <= nx < len(s.lines[ny]):
                row += s.lines[ny][nx]
            else:
                row += ' '
        lines.append(row)
    return lines
```

Analyze the log to find freeze patterns:
```python
# Position changes show where the agent moved
# Stuck counter shows oscillation
# Screen state at each turn shows what the agent saw
# HP drops reveal monster attacks
```
