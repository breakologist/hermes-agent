---
name: roguelike-ability-corruption
version: 1.0.0
description: Ability system with combo activation, corruption costs, and Stabilizer/Hoarder/Oscillator playstyles for roguelike design.
author: Etym
---

# Ability System & Corruption Costs for Roguelikes

Use when: adding resource-based abilities to a roguelike where accumulating a meter has escalating costs, creating a build-and-spend tension that enables multiple playstyles.

## The Core Loop

```
EXPLORE → accumulate resource → corruption rises → SPEND on abilities → corruption drops → explore again
```

The player negotiates constantly: stabilize now or hoard for transformation later?

## Ability System (Combo Activation)

### The Pattern
One activation key ('x') opens a menu. Number keys (1-5) select abilities. In headless mode: `x1`-`x5` in move strings.

### ABILITIES Dict
```python
ABILITIES = {
    "glimpse": {"name": "Glimpse", "tier": 1, "cost": 5, "desc": "Reveal 5-tile radius"},
    "nudge":   {"name": "Nudge",   "tier": 1, "cost": 8, "desc": "Push adjacent enemies"},
    "trace":   {"name": "Trace",   "tier": 1, "cost": 10,"desc": "Direction to nearest gate"},
    "anchor":  {"name": "Anchor",  "tier": 1, "cost": 12,"desc": "Mark position, return once"},
    "quench":  {"name": "Quench",  "tier": 1, "cost": 15,"desc": "Heal 20 HP"},
}
```

### Cost Scaling at High Corruption
```python
def use_ability(player, ability_key, game_map, demons):
    base_cost = ability["cost"]
    if player.hyperstition >= 85:
        cost = int(base_cost * 1.5)  # 1.5x at high corruption
    else:
        cost = base_cost
    if player.hyperstition < cost:
        player.log.append(f"Need {cost}% hyp. Have {player.hyperstition:.0f}%.")
        return False
    player.hyperstition = max(0, player.hyperstition - cost)
```

### Curses Mode (Blocking Input)
```python
if key == ord('x'):
    available = get_available_abilities(player)
    player.log.append("[ABILITIES] (press 1-5)")
    for i, (k, v) in enumerate(available):
        player.log.append(f"  {i+1}. {v['name']} ({v['cost']}%)")
    stdscr.timeout(-1)  # blocking
    choice_key = stdscr.getch()
    stdscr.timeout(100)
    if ord('1') <= choice_key <= ord('5'):
        idx = choice_key - ord('1')
        if 0 <= idx < len(available):
            use_ability(player, available[idx][0], game_map, demons)
```

### Headless Mode (Skip-Next Pattern)
```python
skip_next = False
for ci, ch in enumerate(line):
    if skip_next:
        skip_next = False
        continue
    elif ch == 'x':
        remaining = line[ci + 1:]
        for rch in remaining:
            if rch.isdigit() and 1 <= int(rch) <= 5:
                choice = int(rch)
                break
        if choice:
            use_ability(player, available[choice-1][0], ...)
            skip_next = True  # consume the digit
```

## Corruption Spectrum (Escalating Costs)

The resource meter is NOT just a display. It has escalating gameplay costs:

| Range | Cost | Effect |
|-------|------|--------|
| 0-30% | None | Safe. Abilities cheap. |
| 30-50% | None yet | Accumulating. Consider spending. |
| 50-70% | 1 HP / 20 turns | Passive drain. Factor into survival. |
| 70-85% | Demons +1 move | Threats faster. Be cautious. |
| 85-95% | Abilities 1.5x | Resource management critical. |
| 95%+ | Phase change | Different rules. |

### Implementation
```python
# In movement processing (curses and headless):
hyp = player.hyperstition

# 50%+: passive drain
if hyp >= 50 and player.turn % 20 == 0:
    player.hp -= 1
    if player.turn % 40 == 0:
        player.log.append("The structure corrodes.")

# 70%+: demon aggression
demon_extra_move = hyp >= 70
for d in demons:
    d.try_move(player, game_map)
    if demon_extra_move and d.alive:
        d.try_move(player, game_map)  # extra move

# 85%+: ability cost scaling (in use_ability function)
```

### LOS Corruption (Walls Become Translucent)
```python
walls_translucent = hyperstition >= 55
# Bresenham LOS: if tile == '#' and not walls_translucent → block
#                if tile == '#' and walls_translucent → continue (see through)
```

## Three Playstyles (Emergent from Loop)

### Stabilizer — One-Shot Mastery
- Uses active abilities constantly
- Stays at low corruption (spending hyp prevents accumulation)
- Never reaches schizo-lucid state
- Completes game through skill and resource management

### Hoarder — Corruption as Power
- Saves hyperstition, rides high corruption
- Accepts alienation as power (translucent walls = see-through structure)
- Pushes for schizo-lucid transformation
- Game gets harder around them but they get stronger within it

### Oscillator — The Rhythm
- Alternates building and spending
- Adapts to what the floor offers
- Most flexible but least specialized
- Reads the situation and switches modes

## Sil Principle (Awareness Reward)

When entering a NEW zone with a demon within 5 tiles: +8 hyperstition. Rewards awareness over violence.

```python
if is_new_zone and demons:
    for d in demons:
        if d.alive and max(abs(d.x-nx), abs(d.y-ny)) <= 5:
            self.hyperstition = min(100, self.hyperstition + 8)
            self.log.append(f"[SIL] You sense {d.name}. +8 hyp.")
            demo.record_event(self.turn, "sil_avoidance", demon=d.name, zone=zone)
            break
```

Makes pacifist conduct numerically competitive: +8 per new zone (up to 80) vs +5 per kill.

## Design Principles

1. **Resource meter must have escalating costs** — otherwise accumulation is trivial
2. **Spending must drop the meter** — otherwise the loop doesn't close
3. **Costs should affect different systems** (HP, threat speed, ability cost) — variety prevents monotony
4. **Playstyles should emerge from the loop** — don't force them, let the tension create them
5. **Corruption is reversible** — spending hyp drops the meter and stabilizes the world
6. **Abilities cost more at high corruption** — the Outside resists being channeled
7. **The Sil principle rewards non-combat engagement** — deeper than fighting

## Pitfalls

**Anchor ability handler ordering:** The anchor return handler was placed AFTER the ability menu handler. Since the ability menu fires on 'x' and `continue`s, the anchor return never executed. Fix: check anchor return BEFORE the ability menu handler.

```python
# WRONG — anchor return is dead code (ability handler fires first)
if key == ord('x'):
    show_ability_menu()
    continue
if player.anchor_pos and key == ord('x'):  # never reached
    snap_back()
    continue

# RIGHT — anchor return fires first, then falls through to ability menu
if player.anchor_pos and key == ord('x'):
    snap_back()
    continue
if key == ord('x'):
    show_ability_menu()
    continue
```

**Headless digit consumption:** In headless mode, `x1` sends two characters. If '1' isn't consumed, it processes as a separate move (diagonal). Fix: `skip_next = True` after successful ability use.

**Cost scaling display:** When abilities cost 1.5x at 85%+, the ability menu should show the scaled cost, not the base cost. Otherwise the player is surprised by the actual cost.

**Ability cancellation:** In curses mode, pressing any key other than 1-5 after 'x' should cancel the menu and NOT consume a turn. Currently any key press consumes a turn even if it cancels.
