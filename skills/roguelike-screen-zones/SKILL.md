---
name: roguelike-screen-zones
description: Screen zone recognition for terminal roguelike agents — separate map from UI panels
category: gaming
---

# Roguelike Screen Zone Recognition

## Problem
Terminal roguelikes render map + UI panels on the same screen. Parsing the raw screen catches sidebar text (stats, messages) as game entities (monsters, items).

## Solution: Zone-Aware Parsing
Define screen zones explicitly. Parse each zone independently.

## Angband Layout (LEFT sidebar)
```
Row 0:       Status line (HP, position, depth, etc.)
Rows 1-21:   Map area (scrolls with player position)
  Columns 0-12:  Sidebar (race, class, STR, INT, WIS, DEX, CON, CHR, AC, HP, Gold)
  Columns 13-79: Map tiles (walls, floors, monsters, items)
Rows 22-28:  Status area (Fed, Speed, Level, MaxDepth, Exp, AC, HP bar)
Rows 30-31:  Messages
```

### Monster Detection (Verified April 17)
```python
# Map area: rows 1-21, columns 13-79
# Sidebar at cols 0-12 always skip. Row 0 = status.
# Rows 22+ = status area (Fed, Speed, etc.)
elif (ch.islower() or ch.isupper()) and x >= 13 and 1 <= y < 22:
    self.monsters.append((x, y, ch))
```

### C Command Backstop
Screen parser can still inflate from status text at rows 21-22. Use Angband's `C` (nearby creatures) command to validate:
```python
if len(s.monsters) > 3 and t % 5 == 0:
    real = self._scan_nearby_monsters()  # sends 'C', parses result
    if len(real) < len(s.monsters):
        s.monsters = convert_to_positions(real)  # direction/distance → (x,y)
```

### Key Insight
The `x < 66` check on stores does NOT apply to monsters. Each entity type needs its own zone guard. The sidebar at cols 0-12 catches 't' from "STR", 'a' from "Warrior", 'e' from "Level", etc.

## Cross-Game Patterns

| Game | Sidebar | Map | Messages | Detection Heuristic |
|------|---------|-----|----------|-------------------|
| Angband | Left (cols 0-12) | cols 13-79 | bottom rows | Fixed left column block |
| DCSS | Right (cols 41-79) | cols 0-40 | bottom rows | Right-aligned panel |
| Brogue | Bottom (with ╔═══ border) | rows 0-21 | bottom area | Visual border separator |
| NetHack | Right panel | left | top rows | Top message + right sidebar |

## Universal Heuristic

1. Scan for visual separators (borders, blank lines, repetitive patterns)
2. Fixed-position text = sidebar (stats, status messages)
3. Scrolling text = map (varies by player position)
4. Detect sidebar boundary: find columns where text changes to fixed labels

## Floor Adjacency Filter (Critical — April 17)

Even after zone filtering, UI text can contaminate entity detection. The FINAL filter: **real game entities are adjacent to walkable terrain.**

```python
def _adj_floor(self, y, x):
    """Check if position is adjacent to a walkable tile. Real entities live next to terrain."""
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dy == 0 and dx == 0: continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < len(self.lines) and 0 <= nx < len(self.lines[ny]):
                if self.lines[ny][nx] in WALKABLE_TILES:  # '.', ',', etc.
                    return True
    return False
```

**Angband:** Walkable = `.` (floor), `'` (open door), `,` (rubble)
**DCSS:** Walkable = `.`, `,`, `'`
**Brogue:** Walkable = `.`, `,`, `:` (torch)
**NetHack:** Walkable = `.`, `#` (corridor), `'` (open door)

**Why it works:** UI text (stats, status) is surrounded by spaces, digits, punctuation — never walkable terrain. A monster `k` at (30, 15) next to `.` tiles is real. "Melee" at (29, 11) next to spaces is not.

**Apply to both lowercase AND uppercase branches.** In Angband, sidebar text includes uppercase ("STR:", "Melee", "Searching") that passes all column/row filters.

## Pitfalls
- Sidebar position varies by game — don't assume right or left
- Some games render sidebar at same rows as map (Angband)
- Status text below map can contain lowercase letters
- Uppercase map characters (stores, special terrain) overlap with monster chars
- Store numbers (0-9) at map edge need separate handling from sidebar numbers

## Debugging Methodology (How to Find the Issue)

When entity counts are inflated (monsters, items, etc.):

1. **Check the numbers.** If the screen parser reports 28-81 monsters on DL1, something is wrong. DL1 has 0-5 real monsters.

2. **Ask the human.** The user has PLAYED the game and knows what the screen looks like. They can tell you sidebar position, layout, and normal ranges. Don't guess — ask.

3. **Verify each entity type's column restriction separately.** The `x < 66` check on stores does NOT automatically apply to monsters. Each if/elif branch needs its own zone guard.

4. **Check if/elif order for character set collisions.** If `+` is in both ITEMS and DOORS, the parser's if/elif chain determines which wins. Items come first → doors are never detected.

5. **Test with simulated screens.** Build a fake screen with known sidebar text and known monsters. Run the parser and count before/after the fix.

6. **Use game commands as backstop.** If screen parsing can't be fixed perfectly, use the game's own commands (`C` for creatures, inventory commands) to validate/replace parsed data.

7. **Iterate on row boundaries.** Status text can render at different rows depending on map scroll position. Start with a conservative restriction, then widen if monsters disappear.

## Implementation
1. Define zone boundaries (cols, rows) per game
2. Add zone check to each entity parser (monsters, items, stairs)
3. Test: count entities BEFORE and AFTER zone fix
4. Verify: real monsters should be 0-5 on DL1, not 28-81
5. Add game-command backstop for unreliable parsers
