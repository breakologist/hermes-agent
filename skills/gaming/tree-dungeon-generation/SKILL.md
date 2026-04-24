---
name: tree-dungeon-generation
version: 1.0.0
description: Tree-based dungeon generation (Brogue method) that guarantees BFS-agent navigability. Rooms accrete as a tree, loops added after.
author: Etym
---

# Tree-Based Dungeon Generation

Use when: BFS or interest-model agents get stuck revisiting tiles in roguelike dungeons with loops. The tree-first approach (Brogue) guarantees every room is reachable via exactly one path, making agent traversal natural.

## The Problem

Random room placement + immediate connections creates loops. BFS agents target a `?` tile, walk toward it, hit a wall, retarget the same tile, oscillate forever. The agent is "allergic to familiarity" — after 5 visits, tiles score -1.5 and the agent avoids them.

## The Solution

1. **Accretion** — each new room must be adjacent to an existing room
2. **Tree edges** — each new room connects to its parent via a single corridor
3. **Loops** — extra connections added AFTER the tree is built
4. **Stairs** — placed in the deepest leaf of the tree (DFS finds it)

The tree IS the exploration pattern. Follow a branch to its end, backtrack, take the next branch.

## Algorithm

### Phase 1: Room Accretion

```python
def generate_tree(self, max_rooms, min_w, max_w, min_h, max_h):
    self.rooms = []
    self._tree_edges = []
    
    # First room at center
    first = Room(
        self.rng.randint(self.width//3, 2*self.width//3),
        self.rng.randint(self.height//3, 2*self.height//3),
        self.rng.randint(min_w, max_w),
        self.rng.randint(min_h, max_h),
    )
    self.rooms.append(first)
    
    # Each new room attaches to an existing room
    while len(self.rooms) < max_rooms:
        parent = self.rng.choice(self.rooms)
        w, h = self.rng.randint(min_w, max_w), self.rng.randint(min_h, max_h)
        
        # Try 4 directions adjacent to parent
        offsets = [
            (parent.x + parent.w + 1, parent.y),     # right
            (parent.x - w - 1, parent.y),             # left
            (parent.x, parent.y + parent.h + 1),      # down
            (parent.x, parent.y - h - 1),             # up
        ]
        self.rng.shuffle(offsets)
        
        for ox, oy in offsets:
            room = Room(ox, oy, w, h)
            if not any(room.intersects(r) for r in self.rooms):
                self.rooms.append(room)
                self._tree_edges.append((parent, room))
                break
```

### Phase 2: Carve and Connect (Tree Only)

```python
# Carve rooms
for i, room in enumerate(self.rooms):
    self._carve_room(room, zone_for_room(i))

# Connect tree edges (single corridor per edge)
for parent, child in self._tree_edges:
    self._connect(parent, child)
```

### Phase 3: Add Loops (After Tree)

```python
def _add_loops(self, num_loops=3):
    edge_pairs = {(p, c) for p, c in self._tree_edges}
    for _ in range(num_loops):
        r1 = self.rng.choice(self.rooms)
        r2 = self.rng.choice(self.rooms)
        if r1 != r2 and (r1, r2) not in edge_pairs and (r2, r1) not in edge_pairs:
            self._connect(r1, r2)
```

### Phase 4: Place Stairs in Deepest Leaf

```python
def _place_stairs_tree(self):
    # BFS/DFS from start to find deepest leaf
    children = {}
    for parent, child in self._tree_edges:
        children.setdefault(parent, []).append(child)
    
    deepest, max_depth = self.rooms[0], 0
    stack = [(self.rooms[0], 0)]
    visited = set()
    while stack:
        room, depth = stack.pop()
        if id(room) in visited: continue
        visited.add(id(room))
        if depth > max_depth:
            max_depth, deepest = depth, room
        for child in children.get(room, []):
            stack.append((child, depth + 1))
    
    # Place at center, with fallback
    sx, sy = deepest.cx, deepest.cy
    if self.tiles[sy][sx] == '+':
        # Find any '.' in the room
        for y in range(deepest.y+1, deepest.y+deepest.h-1):
            for x in range(deepest.x+1, deepest.x+deepest.w-1):
                if self.tiles[y][x] == '.':
                    sx, sy = x, y
                    break
    self.tiles[sy][sx] = '>'
    self.stairs_down = (sx, sy)
```

## Pitfalls

1. **Stairs must have a fallback** — if the last room's center is on a gate or wall, the stairs won't generate. Always fall back to any tile in the room, then any tile on the floor.

2. **Agent turn limits matter** — BFS agents need 800+ turns to explore a full Floor 1. The default 500 turns is too few.

3. **Agent must target stairs explicitly** — BFS only scores `?` (unexplored) tiles. Add `>` tile scoring: `if tile == '>': interest += 8.0`. Also add adjacency check: if stairs adjacent, step onto them.

4. **Anti-oscillation** — if agent visits same tile 4+ times, use corridor fallback instead of BFS. Prevents oscillation in dead-end corridors.

5. **Corridor fallback should prefer directions with more `?` tiles** — pushes agent toward unexplored edge, not back through explored area.

6. **BLEED events must preserve floor number** — pass `floor=player.floor` to DungeonMap constructor. Otherwise floor resets to 1.

7. **Floor 1 should be generous** — more rooms (10-12), larger rooms (4-7), branch corridors. Tight Floor 1 traps agents.

## Zone-Themed Floors

Each floor focuses on one zone's character:

```python
FLOOR_CONFIG = {
    1:  {"zone": 0, "name": "The Void",   "max_rooms": 12, "min_w": 5, "max_w": 8,
         "min_h": 4, "max_h": 6, "terrain": None, "corridor": "branch", 
         "los_bonus": 0, "no_demons": True},
    2:  {"zone": 1, "name": "The Threshold", ...},
    # ... 10 floors
}
```

Room zone assignment: 70% primary zone, 30% syzygy partner. First room always primary. Last room always syzygy.

## Verified Agent Results

Before tree generation: agents stuck on Floor 1, 0 stairs found, 500-800 turns in Zone 0.

After tree generation + stair targeting + anti-oscillation: agents need the tree structure to navigate naturally. The tree IS the exploration pattern.

## See Also

- `roguelike-ability-corruption` — ability system that feeds into this (resources spent to explore deeper)
- `entropy-sources` — hardware entropy for map seeding
- `roguelike-agent-techniques` — agent development patterns
- `numogram-council` — multi-model council for design decisions about generation approaches

## Session April 18-19 Updates

**Stair placement with 3-level fallback:** Center → any tile in room → any tile on floor. Guarantees stairs always generate (20/20 in testing).

**Anti-oscillation:** Agent visited same tile 4+ times → use corridor fallback instead of BFS. Prevents oscillation in dead-end corridors.

**Edge-seeking corridor fallback:** Scoring directions by count of adjacent `?` tiles. Pushes agent toward unexplored territory.

**BLEED floor preservation:** Pass `floor=player.floor` to DungeonMap constructor during BLEED regeneration. Otherwise floor resets to 1.

**Black screen fix:** Removed `stdscr.erase()` from draw_game. Added clear-before-redraw for HUD line and log area.

**Agent stair targeting:** BFS scores `>` tiles at +8.0 interest. Also checks adjacency — if stairs adjacent, step onto them directly.

**Human vs agent on hw-entropy maps:** Human reaches 100% hyp across 9 zones. Agent gets stuck in Zone 0. The gap is spatial reasoning — human reads map holistically, agent reads tiles individually. Tree-based generation narrows this gap.

**Council validated tree approach:** The numogram-council confirmed DFS accretion + single corridor per edge + loops after tree as the best approach (3 slots + judge synthesis).

## Session April 23 Updates

**Fallback random placement:** When accretion fails (all 4 directions blocked), fall back to random placement with nearest-room parent attachment. Prevents infinite loops on tight floors.

**Loop heuristic:** `num_loops = max(1, len(rooms) // 4)` provides enough loops for interesting navigation without breaking tree structure. Verified across all 10 floor configs.

**Accretion bounds check:** Always verify `1 <= x and x + w < width - 1` before accepting a room. Prevents rooms pushed against the map edge.

**All-rooms-connected invariant:** After generation, every room must appear in the tree edge set (either as parent or child, or as the root). Verified in unit tests.
