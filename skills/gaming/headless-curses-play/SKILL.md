---
name: headless-curses-play
description: "Three approaches to curses games - headless stdin, tmux+Hyprland, background PTY. Covers state dump API, diagonal fixes, gate alerts, Angband Borg pattern."
version: 1.0.0
author: Etym
---

# Playing Curses Games via Background PTY

Use when: you need to interact with a curses-based terminal game that requires keyboard input and screen rendering. The game cannot be run non-interactively (curses needs a real terminal).

## Approach

1. Start the game as a background PTY process
2. Send keystrokes via `process(action='write')` 
3. Read output via `process(action='poll')`
4. Manage sessions via `process(action='list')`

## Steps

### 1. Launch
```
terminal(command="cd /game/dir && python3 game.py", background=true, pty=true)
```
Returns a `session_id`. The game runs in a pseudo-terminal.

### 2. Send Input
```
process(action='write', session_id=session_id, data='w')  # single key
process(action='write', session_id=session_id, data='ddddssss')  # batch
```
Curses processes keys one at a time. Batch sends work but timing matters — if the game has animations or delays, keys may queue.

### 3. Read Output
```
process(action='poll', session_id=session_id)
```
Returns `output_preview` — a fragment of the curses screen. Output is garbled because curses uses terminal control codes (cursor positioning, color codes). You need to parse fragments rather than clean lines.

### 4. Check State
Press info keys (like 'i' for info screens) to get cleaner text output. Curses info screens often use `print()` or `addstr()` that survives piped output better than the map rendering.

### 5. Quit
Send 'q' or the quit key. Check `cult.json` or save files for persisted state after exit.

## Gotchas

- **`TERM` must be set for PTY mode too.** Launching with `pty=true` without a TERM env var fails with `setupterm: could not find terminal` (NOT `cbreak() returned ERR` — that's the tmux/sandbox variant). Fix: `TERM=xterm-256color python3 game.py`. The tmux section covers TERM for tmux, but bare PTY launches need it too.
- **Curses output is garbled.** You'll see ANSI codes, cursor positioning (`\x1b[30;72H`), and fragmented text. Parse what you can.
- **The player can get stuck.** If all movements hit walls, the player is in a dead end. Try diagonal keys (y/u/b/n) or different directions.
- **Terminal size matters.** Curses games render for a specific terminal size. If the PTY is too small, the game may crash or render incorrectly.
- **Keys may queue.** If you send 30 'w' keys at once, they all process sequentially. The player moves 30 steps. There's no way to interrupt mid-batch.
- **Info screens block.** Pressing 'i' (or similar) often opens a modal that requires another keypress to dismiss. Send a space or enter after reading the info.
- **Multiple instances share state.** If the game has persistent files (like `cult.json`), multiple running instances can interfere with each other. Check for conflicts.

## Example: Numogram Roguelike

The Abyssal Crawler (`numogram_roguelike.py`) uses curses. Playing it via PTY:

1. Launch: `cd /home/etym/numogame && python3 numogram_roguelike.py`
2. Controls: WASD movement, f/space attack, i info, v AQ check, q quit
3. Info screen at turn 62 shows zone, hyperstition, demons slain
4. AQ check shows AQ value and zone reduction of current zone name and "ABYSSAL CRAWLER"
5. After quit, check `cult.json` for run summary

## Limitations

- Cannot take screenshots of curses output
- Cannot read the full map state programmatically
- Navigation is trial-and-error (send movement, check if position changed)
- Combat requires adjacent positioning (send 'f' only when next to demon)

## Better: Interactive tmux + Hyprland (User Watches)

The headless PTY approach works but the user can't see what's happening. A better method uses **tmux** to let the user watch in a real terminal while the agent sends commands.

### Setup (Hyprland)

```bash
# 1. Start game in detached tmux session
tmux new-session -d -s numogame \
    "TERM=xterm-256color NUMOGRAM_PLAYER=hermes python3 game.py 2>/tmp/ngame_err.log"

# 2. CRITICAL: Prevent session death when viewer window closes
tmux set-option -t numogame destroy-unattached off

# 3. Open viewer window for user
hyprctl dispatch exec -- kitty --title "numogame-watch" tmux attach -t numogame
```

### Sending Commands

```bash
# Send single key
tmux send-keys -t numogame "d"

# Send batch (keys process sequentially)
tmux send-keys -t numogame "ddddssss"

# For name entry (interactive input)
tmux send-keys -t numogame "n" && sleep 0.5
echo -n "playername" | tmux load-buffer -t numogame -
tmux paste-buffer -t numogame && sleep 0.2
tmux send-keys -t numogame "Enter"
```

### Reading Output

```bash
# Capture current screen (text, not visual)
tmux capture-pane -t numogame -p | grep -E "^(Z|>|HP)" | head -5

# Capture full screen history
tmux capture-pane -t numogame -p -S -30

# For screenshots (Hyprland with grim/slurp)
grim -g "$(slurp)" - | vision_analyze  # if vision tool available
```

### Key Differences from Headless PTY

| | Headless PTY | tmux + Hyprland |
|---|---|---|
| User visibility | None | Full — watches in kitty window |
| Output quality | Garbled ANSI fragments | Clean curses rendering (text capture) |
| Session management | Process tool (poll/write) | tmux send-keys / capture-pane |
| Multiple runs | Each launch is fresh | tmux session persists |
| Name entry | Crash risk (scope bugs) | Works via tmux load-buffer |

### Pitfalls (Learned April 15, 2026)

- **`destroy-unattached off` MUST be set BEFORE opening the viewer.** Without it, closing the kitty window kills the tmux session and the game crashes.
- **`TERM=xterm-256color`** must be set for curses to initialize in tmux. Without it: `cbreak() returned ERR`.
- **Environment variables** (like `NUMOGRAM_PLAYER`) must be set in the tmux command, not exported before, because tmux creates a new shell.
- **Game crashes propagate.** If the game crashes (e.g., NameError in key handler), the tmux session dies. Check `/tmp/ngame_err.log` for traceback.
- **kitty title** helps identify the window: `--title "numogame-watch"`.
- **`destroy-unattached off`** + viewer closing gracefully: the session persists and the agent can keep playing.

### Known Bugs (Abyssal Crawler)

- **'n' key handler**: Uses `max_y` variable not in scope. Fix: `my, mx = stdscr.getmaxyx()` before `addstr()`.
- **Diagonal attack**: Attack check used Manhattan distance (cardinal only). Fix: `max(abs(d.x - player.x), abs(d.y - player.y)) == 1` (Chebyshev). Also fix demon chase AI with same change.
- **Zone 0 density**: Very low (0.3, rooms 2-4). Getting stuck is common. Need forward-escape strategy.

### Game-Specific Notes (Abyssal Crawler)

- Controls: WASD/HJKL cardinal, YUBN/7913 diagonal, f/space attack, g grasp, n name, i info, v AQ, q quit
- cult.json persists across runs — multiple instances interfere. Only one game at a time.
- Hyperstition ratchet: +0.3/step, +3 zone crossing, +5 gate, +5 demon kill, +20 Cryptolith
- Pacifist path exists: 10 zones (+30) + gates (+50) + Cryptolith (+20) = 100%, no kills needed
- Gates are the critical missing piece — stepping on gate tiles (+5 hyp each) is how you reach 100%

### Headless Auto-Recording (Added April 15, 2026 — Evening)

Headless mode now auto-records demos. The demo starts at game init and stops at all exit points (quit, death, EOF, interrupt). Events (zone_change, demon_kill, death) record automatically via shared Player methods. Key recording requires `demo.record_key(player.turn, key)` in the headless loop. Call `demo.stop()` at ALL four exit points — missing any one means the demo file lacks its closing marker.

### Headless Mode — The Game's Own API (Added April 15, 2026)

The breakthrough: add `--headless` flag to the game. No curses. No terminal. The game
reads moves from stdin, writes state to `/tmp/numogame_state.txt`, prints status to
stderr. The agent drives the game through a clean pipe interface.

### Implementation

```python
if __name__ == "__main__":
    import sys
    if "--headless" in sys.argv:
        main_headless()
    else:
        curses.wrapper(main)
```

The `main_headless()` function:
- Initializes game (same as curses main)
- Reads moves from stdin (one char per line or batch: `ddddssss`)
- Processes each char: w/a/s/d=movement, f=attack, p=state dump, v=AQ, q=quit
- Calls `_tick_headless()` after each move (spawn demons, move enemies, check death)
- Writes state file after each move
- Prints one-line status per turn: `[T:42] Z3:Release HP:73 Hyp:35% Slain:2 Gates:0`
- Saves to cult.json on EOF, death, or quit

### Usage

```bash
# Pipe moves directly — instant, no terminal
echo "ddddssssllllnnnnpp" | NUMOGRAM_PLAYER=hermes python3 game.py --headless

# Interactive — type moves, press enter
NUMOGRAM_PLAYER=hermes python3 game.py --headless
> ddddssss
> p
> q

# Automated sweep — generate moves programmatically
python3 -c "
moves = ''
for _ in range(30): moves += 'dn'
for _ in range(30): moves += 'sa'
moves += 'pq'
print(moves)
" | NUMOGRAM_PLAYER=sweeper python3 game.py --headless
```

### The Game Loop for Agents

1. Pipe moves in → game processes them instantly (<1ms per move)
2. Read `/tmp/numogame_state.txt` → see the map, gates, demons
3. Decide next moves based on state
4. Pipe them in
5. Repeat until dead or goal reached

### Why This Beats tmux

| | tmux send-keys | headless mode |
|---|---|---|
| Latency | 0.5-2s per move | <1ms per move |
| Capture | Sometimes empty (race) | Always fresh (file I/O) |
| Session | Can die on window close | No session, just a process |
| Complexity | tmux + kitty + capture-pane | stdin + stdout + file |
| Watch mode | Built-in (kitty window) | Separate (tail state file) |

### Pitfalls Learned

- **EOF doesn't raise exception in for loop.** `for line in sys.stdin:` just exits on EOF,
  it doesn't throw `EOFError`. Save cult data AFTER the loop, not in an except block.
- **sorted() on mixed-type tuples fails.** `sorted(nearby_demons)` where the tuple is
  `(int, str, Demon)` fails because `Demon` isn't comparable. Fix: `key=lambda x: (x[0], x[1])`.
- **Demon ticks must happen on every turn-consuming action.** Not just movement — also
  attack, state dump, AQ check. Otherwise demons freeze while the player dumps state.
- **sorted() on mixed-type tuples fails.** `sorted(nearby_demons)` where the tuple is
  `(int, str, Demon)` fails because `Demon` isn't comparable. Fix: `key=lambda x: (x[0], x[1])`.
- **Demon ticks must happen on every turn-consuming action.** Not just movement — also
  attack, state dump, AQ check. Otherwise demons freeze while the player dumps state.

## Demo Recording — Doom-Style Input Logging (Added April 15, 2026)

Record human play for agent analysis. The demo file is text — parseable by any tool.

### Implementation

```python
DEMO_DIR = "/home/etym/numogame/demos"

class DemoRecorder:
    def __init__(self):
        self.active = False
        self.file = None
    
    def start(self, player_name="unknown"):
        import datetime, os
        os.makedirs(DEMO_DIR, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(DEMO_DIR, f"{ts}_{player_name}.demo")
        self.file = open(self.filename, "w")
        self.active = True
        self.file.write(f"# NUMOGRAM DEMO\n# Player: {player_name}\n# Started: {datetime.datetime.now().isoformat()}\n\n")
    
    def stop(self):
        if self.file:
            self.file.write(f"\n# Ended: {datetime.datetime.now().isoformat()}\n")
            self.file.close()
            self.file = None
        self.active = False
    
    def record_key(self, turn, key_char):
        if self.active and self.file:
            self.file.write(f"T:{turn} K:{key_char}\n")
            self.file.flush()
    
    def record_event(self, turn, event_type, **kwargs):
        if self.active and self.file:
            params = " ".join(f"{k}={v}" for k, v in kwargs.items())
            self.file.write(f"T:{turn} E:{event_type} {params}\n")
            self.file.flush()

demo = DemoRecorder()  # Global instance
```

### Key Handler (in main loop)

```python
# Toggle recording with 'D' key
if key == ord('D'):
    if not demo.active:
        demo.start(getattr(player, 'player_name', 'crawler'))
    else:
        demo.stop()
    continue

# Record every keypress — use readable names for curses special keys
demo.record_key(player.turn, _demo_key_name(key))
```

### Key Name Mapping (Fix for Hex Dump Bug)

Curses arrow keys (KEY_UP=259, KEY_DOWN=258, KEY_LEFT=260, KEY_RIGHT=261) get recorded as raw integers. Without a lookup, demos show `0x104` instead of `LEFT`. Fix:

```python
_CURSES_KEY_NAMES = {
    258: "DOWN", 259: "UP", 260: "LEFT", 261: "RIGHT",
    262: "HOME", 338: "PgDn", 339: "PgUp",
    330: "DC", 331: "IC", 263: "BACKSPACE",
    9: "TAB", 10: "ENTER", 13: "ENTER", 27: "ESC",
    353: "BTAB", 343: "ENTER",
}

def _demo_key_name(key):
    if key in _CURSES_KEY_NAMES:
        return _CURSES_KEY_NAMES[key]
    if 32 <= key < 127:
        return chr(key)
    return f"0x{key:x}"  # fallback for truly unknown keys
```

# Stop on quit
if key == ord('q'):
    demo.stop()
    break
```

### Event Recording Hooks

Record at zone changes, demon kills, death — inside Player methods:

```python
# In move() — zone change
demo.record_event(self.turn, "zone_change", zone=zone, name=data.get('name','?'))

# In attack() — demon kill  
demo.record_event(self.turn, "demon_kill", name=demon.name, mesh=demon.mesh, type=demon.dtype)

# In move() — death
demo.record_event(self.turn, "death", msg=self.death_msg, hyp=f"{self.hyperstition:.0f}", zone=self.zone)
```

### Headless Mode Demo Recording

Headless mode should auto-record demos so agents can self-analyze their play. Wire the demo recorder into `main_headless()`:

```python
def main_headless():
    # ... init ...
    
    # Start demo recording automatically
    demo.start(player_name)
    print(f"[DEMO] Recording to {demo.filename}", file=sys.stderr)
    
    for line in sys.stdin:
        for ch in line:
            key = ch.lower()
            demo.record_key(player.turn, key)  # headless keys are already chars
            
            # ... process key ...
            
            if key == 'q':
                demo.stop()
                save_cult(...)
                return
        
        # Check death
        if player.dead:
            demo.stop()
            save_cult(...)
            return
    
    # EOF exit
    demo.stop()
    save_cult(...)
```

Critical: call `demo.stop()` at ALL exit points — quit, death, EOF, and KeyboardInterrupt. Missing any one means the demo file lacks its closing timestamp and end-of-file marker.

Event recording (zone_change, demon_kill, death) works automatically in headless mode because those hooks are inside Player methods (`move()`, `attack()`), which are shared between curses and headless paths. No additional wiring needed for events — only for key recording and start/stop lifecycle.

### Demo File Format

```
# NUMOGRAM DEMO
# Player: hermes
# Started: 2026-04-15T16:45:56

T:3 K:6          # Turn 3, pressed key '6' (diagonal)
T:16 E:zone_change zone=1 name=Stability
T:27 E:zone_change zone=4 name=Catastrophe
T:109 E:zone_change zone=8 name=Multiplicity
T:178 E:demon_kill name=Tchakki mesh=19 type=amphidemon
T:216 K:4

# Ended: 2026-04-15T16:52:31
```

### Agent Analysis

Parse the demo file to build:
- **Movement heatmap**: Where the player spent the most turns
- **Zone transition timeline**: Order of zone visits, time in each
- **Combat log**: Which demons were killed, when
- **Key distribution**: What keys were pressed most (movement vs combat vs utility)
- **Death cause analysis**: What happened in the turns before death

## State Dump — Full Floor Map (78x22 ASCII)

The state dump includes both a local 21x21 view AND the full 78x22 floor map.

```python
# FULL FLOOR MAP section in _dump_state()
lines.append("## FULL MAP (78x22)")
lines.append("  @=you #=wall .=floor +=gate 0-9=zone boundary")
lines.append("  !" + "-" * 78 + "!")
for my in range(game_map.height):
    row = []
    for mx in range(game_map.width):
        if mx == player.x and my == player.y:
            row.append('@')
        elif (mx, my) in demon_positions:
            d = demon_positions[(mx, my)]
            if d.dtype == SYZYGISTIC: row.append('*')
            elif d.dtype == XENODEMON: row.append('?')
            elif d.dtype == CHRONODEMON: row.append('%')
            else: row.append('!')
        elif (mx, my) in game_map.gate_tiles:
            row.append('+')
        elif game_map.is_passable(mx, my):
            zone_here = game_map.get_zone_at(mx, my)
            if zone_here is not None and zone_here != player.zone:
                row.append(str(zone_here))
            else:
                row.append('.')
        else:
            row.append('#')
    lines.append("  !" + "".join(row) + "!")
lines.append("  !" + "-" * 78 + "!")
```

## Gate Visibility Bugs — Common Pitfalls (Abyssal Crawler)

### Bug 1: Pocket function overwrites gates

`_pocket()` randomly changes 30% of room tiles. If a gate ('+') is at the room center, it gets overwritten.

```python
# WRONG — overwrites gates
if self.rng.random() < 0.3:
    self.tiles[y][x] = ch

# RIGHT — skip gates
if self.tiles[y][x] != '+' and self.rng.random() < 0.3:
    self.tiles[y][x] = ch
```

Apply the same protection to `_reshape_rooms()`.

### Bug 2: Duplicate class definitions

If a game has two map classes (e.g., `DungeonMap` and `NumogramMap`), the second one may clear state that the first one set. Check with:

```python
import re
for m in re.finditer(r'^class \w+Map', source, re.MULTILINE):
    print(f'{m.group()} at char {m.start()}')
```

### Bug 3: _manifest_gates timing

If `_manifest_gates()` runs BEFORE `_reshape_rooms()` or `_warp_plex_pockets()`, the gates get overwritten. Check the generate() call order.

## Curses Input — Name Entry Fix

The game's `timeout(100)` interferes with `getstr()`. Fix by temporarily setting blocking input:

```python
# WRONG — timeout causes getstr to return early
stdscr.timeout(100)  # game's normal timeout
name = stdscr.getstr(my - 2, 6, 20)  # fails because timeout is active

# RIGHT — disable timeout during name entry
stdscr.timeout(-1)  # blocking mode
curses.echo()
name = stdscr.getstr(my - 2, 13, 20).decode('utf-8').strip()
curses.noecho()
stdscr.timeout(100)  # restore game timeout
```

## Class Method Scoping — `player` vs `self`

When adding demo recording or instrumentation inside Player/Demon methods, use `self` not `player`:

```python
# WRONG — 'player' not defined inside method
def attack(self, demon):
    demo.record_event(player.turn, "demon_kill", ...)

# RIGHT — use self
def attack(self, demon):
    demo.record_event(self.turn, "demon_kill", ...)
```

This is easy to miss when copy-pasting from the main loop where `player` IS a local variable.

## Map-Aware Pathfinding Script

For automated play, read the full map dump and navigate toward targets:

```python
def get_moves_toward_target(state_file="/tmp/numogame_state.txt"):
    # Parse full map
    # Find player position (@)
    # Find targets: zone boundaries (0-9), gates (+)
    # Compute direction to nearest target
    # Generate move string
    # Handle walls by checking passable tiles
    pass
```

Key insight: the full map shows corridors as '.' sequences. Follow them to reach new zones. Don't random-walk.

## Angband Borg — General Patterns

The Angband Borg reads `grid_data` from the game's internal state, not from the terminal. Our state dump does the same thing. General principle for AI-playable roguelikes:

1. **State reading over screen reading.** Give the agent structured game state.
2. **Decision loop.** Read state → evaluate threats → choose action → execute → repeat.
3. **Threat assessment.** Calculate danger from monster stats.
4. **Goal prioritisation.** Survive > explore > collect > kill.
5. **Memory across turns.** Remember explored areas, known threats.

See: `vagrant-borg` on GitHub, Angband manual at `angband.readthedocs.io/en/latest/hacking/borg.html`

## Watch Mode — tmux + Hyprland

For human watching while agent plays:

```bash
tmux kill-session -t numogame 2>/dev/null
tmux new-session -d -s numogame "TERM=xterm-256color NUMOGRAM_PLAYER=hermes python3 game.py 2>/tmp/ngame_err.log"
tmux set-option -t numogame destroy-unattached off
hyprctl dispatch exec -- kitty --title "numogame-watch" tmux attach -t numogame
```

Helper scripts at `~/numogame/numogame-watch.sh` and `~/numogame/ng` (send keys shortcut).
