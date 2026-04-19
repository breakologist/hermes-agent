## Fighting More Aggressively — Walk Toward (April 17)

The agent only fought adjacent monsters. Adding walk-toward logic (within 5 tiles for weak, 3 for strong) plus BFS interest scoring (+6.0 for weak monsters) doubled engagement rate.

### BFS Monster Interest
```python
is_weak_monster = any(mx == x and my == y and ch.islower()
                      for mx, my, ch in s.monsters)
if is_weak_monster and not self._is_town(s):
    sc += 6.0  # weak monsters = free XP — worth pursuing
```

## Stuck Recovery — Must Be TOP of Decision Tree (April 17)

The stuck recovery checks (`stuck > 100`, `stuck > 50 in tiny room`) must be at the TOP of `_decide()`, BEFORE fight/flee/BFS/escape checks. If nested inside a conditional block (like `walkable_neighbors < 2`), they only fire in tiny pockets — rooms with 3+ walkable neighbors never trigger recovery.

**Lesson:** The agent got stuck for 500 turns in a 37-floor room with 6 doors because stuck recovery was inside the `walkable_neighbors < 2` block. Moving recovery to the top fixed it.

```python
def _decide(self, s):
    # 0. STUCK RECOVERY — FIRST, before everything else
    if self.stuck > 100 and s.stairs_up and not self._is_town(s):
        return self._go_up_stairs(s) or 's'
    if self.stuck > 50 and len(s.floors) <= 25 and not self._is_town(s):
        return self._go_up_stairs(s) or 's'
    # ...rest of decision tree
```

## Equipment Memory — On-Pickup Only (April 17)

Periodic equip (every 25 turns) fires 20+ times per run even when nothing new is in inventory. The fix: equip only when items are picked up, plus a 100-turn fallback for missed pickups.

On-pickup: send `w` immediately after `items_found` message detected. Dismiss with Escape if "nothing to..." or "which...". 100-turn fallback catches missed pickups.

**Critical: `w` command handles ALL equipment** — weapons, armor, cloaks, shields, boots, rings, amulets. `W` is NOT a valid command. Previous code was sending both `w` AND `W` — wasted a cycle.

## Angband Live Ladder — Studying Human Games (April 17)

Angband has no demo recording (unlike Doom). Study human play via the **Angband Live ladder** at `angband.live/ladder/`.

Scrape: `https://angband.live/ladder/ladder-browse.php?v=Angband&o={offset}&s=4` (50 per page, 6700+ total). Individual dumps: `ladder-show.php?id={id}`. Parse `<pre>` block for equipment, death causes, stats.

Equipment patterns: L6-15 (9 items avg: Leather Armour, Gauntlets, Torch, Cloak). L16-30 (12 items: Ring of Damage, Cloak of Aman, Crossbow). L31+ (12 items: Ring of Speed, Shield of Thorin — mostly winners). Weapon is #1 priority. Top winners: High-Elf Rogue (25/50), Human Warrior (20/50).

Script: `~/numogame/scrape_angband_ladder.py`. Output: `~/.hermes/angband_ladder_data.json`.

## Food & Eating (April 17)

Parse Fed from sidebar: `re.search(r'Fed\s+(\d+)', line)`. Eat when Fed < 50%. Fallback eat every 2000 turns. Drain rate: ~1% per 150 turns. Starting at 89%, starvation around turn 12,000.

## BFS Tie-Breaking — Kill Oscillation (April 17)

BFS was deterministic — always picked first tile with highest score. Agent oscillated 2-3 positions for 500+ turns. Fix: 30% chance to replace equal-score tiles during BFS traversal.

```python
if sc > best_s or (sc == best_s and random.random() < 0.3):
    best = (cx, cy); best_s = sc
```

## Interest Decay — Strong Novelty Penalty (April 17)

Multiple iterations. First attempt (-0.5 per visit) too weak. Final: -2.0 per revisit. Visited tiles become invisible fast. Stairs stay hot (+20). Items stay warm (+5).

```python
sc = -2.0 - (v - 1) * 2.0
if is_down: sc += 20.0
if is_item: sc += 5.0
```

## Level Regeneration — Reset Exploration State (April 17)

When level regenerates, visited/vcount/recent_positions from OLD layout penalize NEW layout exploration. Reset all three on depth change.

## Perimeter Search (April 17)

When all floors explored, walk along walls searching for hidden doors. Find wall-adjacent floor tiles, BFS to nearest unsearched one, send `s` when close.

## Secret Door — False Item (Parser Fix)

"You have found a secret door" matches item pickup regex. Filter: `if 'secret door' not in item.lower()`.
