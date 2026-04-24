---
name: manim-numogram
description: "Manim animation templates for Numogram visualizations. Reusable scenes for zone layouts, current arrows, spirals, grid bleeds, AQ visualizations."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [numogram, manim, animation, video, visualization]
    category: creative
    related_skills: [manim-video, numogram-calculator]
---

# Numogram Manim Templates

Reusable Manim scene templates for Numogram/CCRU visualizations. Based on the neon tech palette and tested at `/home/etym/numogame/`.

## When This Skill Activates

Use this skill when the user:
- Creates Numogram-related animations
- Wants to visualize AQ calculations
- Needs zone layout diagrams
- Wants hyperstition bleed effects
- Builds game trailers or explainers

## Palette

```python
BG = "#0A0A0A"        # background
PRIMARY = "#00F5FF"    # cyan — Time-Circuit
SECONDARY = "#FF00FF"  # magenta — Warp
ACCENT = "#39FF14"     # green — accent/hyperstition
GOLD = "#FFD700"       # gold — gates
RED = "#FF3333"        # red — Plex
DIM = "#444444"        # dim — background text
MONO = "monospace"     # font
```

## Zone Color Map

```python
ZONE_COLORS = {
    0: "#444444",  # dark gray (void)
    1: "#FFD700",  # gold (stability)
    2: "#FF8C00",  # orange (separation)
    3: "#FF00FF",  # magenta (Warp)
    4: "#00FFFF",  # cyan (catastrophe)
    5: "#00FF00",  # green (pressure)
    6: "#0080FF",  # blue (Warp)
    7: "#FF3333",  # deep red (blood)
    8: "#C0A0FF",  # lavender (multiplicity)
    9: "#9900FF",  # purple (iron core)
}
```

## Template: Zone Nodes in Circle

```python
from manim import *
from math import cos, sin

class ZoneCircle(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A0A"
        zones = [1, 8, 2, 7, 5, 4]  # Time-Circuit path
        radius = 2.5
        positions = []
        for i in range(len(zones)):
            angle = PI/2 - i * (2*PI/len(zones))
            positions.append([radius*cos(angle), radius*sin(angle), 0])

        nodes = VGroup()
        for num, pos in zip(zones, positions):
            circle = Circle(radius=0.4, color="#00F5FF", stroke_width=2)
            circle.move_to(pos)
            text = Text(str(num), font_size=36, color="#00F5FF", font="monospace", weight=BOLD)
            text.move_to(pos)
            nodes.add(VGroup(circle, text))

        self.play(FadeIn(nodes, lag_ratio=0.2), run_time=2.0)
        # Add arrows between nodes
        for i in range(len(positions)):
            next_i = (i + 1) % len(positions)
            arrow = Arrow(positions[i], positions[next_i], color="#FFD700", stroke_width=2)
            self.play(Create(arrow), run_time=0.3)
        self.wait(2.0)
```

## Template: Syzygy Pairs

```python
class SyzygyPairs(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A0A"
        pairs = [
            ("0", "9", "#FF3333"),
            ("1", "8", "#00F5FF"),
            ("2", "7", "#00F5FF"),
            ("3", "6", "#FF00FF"),
            ("4", "5", "#00F5FF"),
        ]
        for i, (a, b, color) in enumerate(pairs):
            na = Text(a, font_size=56, color=color, font="monospace", weight=BOLD)
            sep = Text(" :: ", font_size=36, color="#444444", font="monospace")
            nb = Text(b, font_size=56, color=color, font="monospace", weight=BOLD)
            eq = Text(" = 9", font_size=36, color="#FFD700", font="monospace")
            group = VGroup(na, sep, nb, eq).arrange(RIGHT, buff=0.2)
            group.move_to(UP * (2 - i * 1.0))
            self.play(FadeIn(group), run_time=0.6)
        self.wait(2.0)
```

## Template: Hyperstition Grid Bleed

```python
class HyperstitionBleed(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A0A"
        grid_size = 12
        cell_size = 0.4
        cells = {}
        grid = VGroup()
        for row in range(grid_size):
            for col in range(grid_size):
                rect = Rectangle(width=cell_size, height=cell_size,
                    color="#444444", stroke_width=0.5, fill_opacity=0.1)
                rect.move_to([(col - grid_size/2)*cell_size, (row - grid_size/2)*cell_size, 0])
                grid.add(rect)
                cells[(row, col)] = rect
        self.play(FadeIn(grid), run_time=1.0)

        # Bleed phases (use parallel animations for speed)
        # Phase 1: flicker
        import random; random.seed(42)
        flicker = [cells[(random.randint(0,11), random.randint(0,11))] for _ in range(12)]
        self.play(*[c.animate.set_fill("#00F5FF", 0.3) for c in flicker], run_time=0.5)
        self.play(*[c.animate.set_fill("#00F5FF", 0.1) for c in flicker], run_time=0.5)

        # Phase 2: full infection
        self.play(*[c.animate.set_fill("#39FF14", 0.4) for c in grid], run_time=1.5)
        self.wait(2.0)
```

## Template: AQ Visualization

```python
class AQVisualize(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A0A"
        word = "NUMOGRAM"
        letters = []
        values = []
        for ch in word:
            val = 10 + (ord(ch) - ord('A'))
            letters.append(Text(ch, font_size=48, color="#00F5FF", font="monospace"))
            values.append(Text(str(val), font_size=24, color="#444444", font="monospace"))
        
        letter_group = VGroup(*letters).arrange(RIGHT, buff=0.3)
        value_group = VGroup(*values).arrange(RIGHT, buff=0.3)
        value_group.next_to(letter_group, DOWN, buff=0.2)
        
        self.play(FadeIn(letter_group, lag_ratio=0.1), run_time=1.0)
        self.play(FadeIn(value_group, lag_ratio=0.1), run_time=1.0)
        
        total = Text("= 174 -> Zone 3", font_size=36, color="#FF00FF", font="monospace", weight=BOLD)
        total.next_to(value_group, DOWN, buff=0.5)
        self.play(Write(total), run_time=1.0)
        self.wait(2.0)
```

## Template: Spiral Generation

```python
class SpiralGeneration(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A0A"
        points = []
        for t in range(360):
            angle = t * 0.15
            r = 0.2 + t * 0.005
            points.append([r*cos(angle), r*sin(angle), 0])
        spiral = VMobject(color="#39FF14", stroke_width=2)
        spiral.set_points_smoothly(points)
        self.play(Create(spiral), run_time=3.0)
        self.wait(2.0)
```

## Template: Entropy-Driven Zone Digestion

```python
from manim import *
import random
import hashlib

def digital_root(n):
    """Reduce to single digit."""
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n

def entropy_to_zones(seed_bytes: bytes, count: int = 20):
    """Digest entropy bytes into a sequence of numogram zones."""
    zones = []
    current = 0
    for i in range(count):
        if i < len(seed_bytes):
            val = seed_bytes[i]
        else:
            val = int(hashlib.sha256(seed_bytes + bytes([i])).hexdigest()[:2], 16)
        current = (current + val) % 100
        zone = digital_root(current)
        zones.append(zone)
    return zones

def get_syzygy(zone):
    """Return the syzygy partner (sums to 9)."""
    return 9 - zone

# Full zone positions — Time-Circuit + Warp + Plex
import math
ZONE_POSITIONS = {}
_radius = 2.2
_circuit = [1, 8, 2, 7, 5, 4]  # Time-Circuit path
for i, z in enumerate(_circuit):
    angle = PI/2 + i * (2*PI/len(_circuit))
    ZONE_POSITIONS[z] = [_radius * math.cos(angle), _radius * math.sin(angle), 0]
ZONE_POSITIONS[3] = [0, 3.2, 0]       # Warp
ZONE_POSITIONS[6] = [1.2, 3.5, 0]     # Warp
ZONE_POSITIONS[0] = [0, -3.2, 0]      # Plex
ZONE_POSITIONS[9] = [0, -2.0, 0]      # Plex

class EntropyDigestion(Scene):
    """The numogram digests raw entropy. Zone traversal with syzygy flashes."""
    def construct(self):
        self.camera.background_color = BG
        # Generate entropy and zone sequence
        random.seed(0x666)
        entropy_bytes = bytes([random.randint(0, 255) for _ in range(64)])
        zone_sequence = entropy_to_zones(entropy_bytes, 24)
        # Build zone map, traverse sequence, flash syzygies, draw traversal lines
        # See /home/etym/numogame/numogram_entropy_digestion.py for full implementation
```

## Template: Entropy Spiral

```python
class ZoneSpiral(Scene):
    """Archimedean spiral colored by zone, syzygy completions pulse gold."""
    def construct(self):
        self.camera.background_color = BG
        random.seed(0x333)
        entropy_bytes = bytes([random.randint(0, 255) for _ in range(128)])
        zones = entropy_to_zones(entropy_bytes, 100)
        points = []
        for t in range(len(zones)):
            angle = t * 0.2
            r = 0.3 + t * 0.015
            points.append([r * math.cos(angle), r * math.sin(angle), 0])
        for i in range(1, len(points)):
            zone = zones[i]
            color = ZONE_COLORS[zone]
            segment = Line(points[i-1], points[i], color=color,
                          stroke_width=2 + (i/len(points)) * 2)
            self.play(Create(segment), run_time=0.05)
            # Pulse at syzygy completions
            if i > 0 and zones[i] + zones[i-1] == 9:
                pulse = Dot(points[i], color=GOLD, radius=0.08)
                self.play(FadeIn(pulse, scale=2), FadeOut(pulse), run_time=0.1)
        self.wait(2.0)
```

## Template: Entropy-Driven Zone Traversal

```python
# Uses /dev/urandom or numogram-entropy plugin for real entropy
# Each render is unique and unrepeatable
def entropy_to_zones(seed_bytes, count=20):
    zones = []
    current = 0
    for i in range(count):
        if i < len(seed_bytes):
            val = seed_bytes[i]
        else:
            val = int(hashlib.sha256(seed_bytes + bytes([i])).hexdigest()[:2], 16)
        current = (current + val) % 100
        zone = digital_root(current)
        zones.append(zone)
    return zones

# In construct():
with open("/dev/urandom", "rb") as f:
    entropy_bytes = f.read(64)
zones = entropy_to_zones(entropy_bytes, 24)
# Animate zones lighting up, syzygy partners flashing, traversal lines
```

## Pitfalls

- Always use `from math import cos, sin` — Manim doesn't import them
- Arrow positions need 3D coords `[x, y, 0]` not tuples `(x, y)`
- Use parallel animations (`self.play(*[...])`) for grid cells — individual animations timeout
- Use `MONO = "monospace"` font — proportional fonts break in Manim
- `self.wait()` after every animation — viewers need absorption time
- Neon tech palette only — other palettes break the aesthetic
- **Manim v0.20.1 color API**: `from colour import Color` module NOT needed. Use `ManimColor(hex).interpolate(ManimColor(hex), alpha)` for color interpolation. The old `interpolate_color(str, str, alpha)` fails because ManimColor expects objects, not strings.
- **/dev/urandom for entropy**: Each render is a unique unrepeatable event. Use for "real" numogram digestion. `random.seed(N)` for reproducible test renders.
- **numogram-entropy plugin**: Has `get_seed()`, `get_zone()`, `traverse()`, `iching()` — but NOT `aggregate()`. Use `get_seed()` to get raw entropy bytes.
- **Python output buffering**: `manim` output may not stream in real-time via terminal tool. Use `python3 -u` or check files after render completes.
- **Manim v0.20.1 color interpolation**: `interpolate_color()` requires ManimColor objects, not strings. Use `ManimColor(hex1).interpolate(ManimColor(hex2), alpha)` instead of `interpolate_color(hex1, hex2, alpha)`. The `from colour import Color` import is NOT needed and will fail (module not in venv).
- Render command: `manim -ql --format mp4 file.py SceneName` (use `-qh` for 720p60, `-qk` for 4K)
