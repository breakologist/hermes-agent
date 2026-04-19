---
name: tsubuyaki
description: "Write tsubuyaki (tweet-length) p5.js sketches — generative art in 280 characters or less. Domain-specific constraint art with iterative refinement."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [tsubuyaki, p5js, creative-coding, constraint-art, generative]
    category: creative
---

# Tsubuyaki — Tweet-Length Generative Art

Write generative art sketches in 280 characters or less. One tweet, one universe.

## When This Skill Activates

Use this skill when:
- Writing tsubuyaki / tweet-length generative art
- Creating constrained creative coding (character budgets)
- Iterating on a series of related sketches with varied complexity
- Building domain-themed p5.js sketch collections

## The Constraint

280 characters. No imports. No boilerplate. No comments. Every character earns its place.

Standard opener (15 chars): `f=0;draw=_=>{f++||createCanvas(W=500,W);`

Remaining budget: ~265 chars for the art.

## Compression Techniques

| Technique | Example | Saves |
|-----------|---------|-------|
| `1e3` | Instead of `1000` | 2 chars |
| `~~(x)` | Instead of `floor(x)` | 7 chars |
| `TAU` | Instead of `PI*2` | 2 chars |
| `W=500,W` | Variable capture | Avoids repeating 500 |
| `background(0,N)` | Low-alpha clear | Creates trails |
| `n/99` | Instead of `n/100` | 1 char, shifts noise period |
| `cos(a)*.6` | Ellipse via squash | No separate ellipse logic |
| `noise(n+99,...)` | Independent noise channel | Different noise from same fn |
| `fill(R,G,B,A)` | Raw RGBA | No `color()` call |
| `f/2e3` | Instead of `f/2000` | 1 char |
| `F*F/100` | Quadratic expansion | Non-linear ring growth |

## Background Alpha Values and Their Effects

| Alpha | Clear % | Effect |
|-------|---------|--------|
| `background(0)` | 100% | No trails. Clean slate each frame. |
| `background(0,4)` | 1.6% | Extreme persistence. Blood pooling, nebula accumulation. |
| `background(0,6)` | 2.4% | Long trails. Ghost echoes, wake patterns. |
| `background(0,8)` | 3.1% | Moderate trails. Standard for most sketches. |
| `background(0,12)` | 4.7% | Short trails. Magenta sun, overlapping glow. |
| `background(0,15)` | 5.9% | Brief trails. Dual vortex interaction visible. |

## Iteration Method: v1 → v2 with Complexity Variation

When building a series (e.g., 10 sketches for 10 zones), iterate deliberately:

**v1 (first pass):** Write each sketch in its simplest viable form. Establish the core technique for each piece. Keep character counts conservative (170-210).

**v2 (second pass):** Revisit each sketch with a deliberate decision — MORE complex or LESS simple:
- Some go simpler (Void: 50 particles → 10, slower orbit)
- Some gain new elements (Stability: add connecting lines between grid nodes)
- Some change technique entirely (Catastrophe: displaced grid → expanding ripple rings)
- Some go significantly more complex (Multiplicity: 80 particles/1 mode → 120 particles/4 modes)

The variation across the series matters more than any individual sketch. A series of 10 sketches all at 180 chars feels monotonous. A series ranging from 161 to 275 chars feels alive.

### Complexity Decision Framework

For each sketch in v2, ask:
1. What does this concept *want* to be? (Simple concepts want simple sketches)
2. Where is there headroom? (180/280 leaves 100 chars of possibility)
3. What technique from the reference collection would elevate this? (Dual vortices, concentric rings, line connections, multi-mode particles)
4. What did I *not* try in v1 that the concept demands?

## Gallery Pattern

Build a single self-contained HTML gallery with instance-mode p5.js:

```javascript
// Each sketch as a function taking the p5 instance
const ZONES = [{
  id: 0, name: "Void", hex: "#444444",
  code: `f=0;draw=_=>{...}`, // The tsubuyaki string (for display)
  note: "Description...",
  draw(p) { /* Expanded implementation */ }
}, ...];

// Gallery: card per sketch with canvas, code, char count
// Each card gets its own p5 instance
new p5((p) => {
  p.setup = () => { p.createCanvas(500, 500); p.pixelDensity(1); p.noiseSeed(z.id * 137 + 666); };
  p.draw = () => { z.draw(p); };
}, container);
```

Key: display the compressed code (for reading), run the expanded code (for reliability). The tsubuyaki string is the artifact. The expanded function is the renderer.

## Character Count Verification

Always verify after writing:

```python
codes = [
    ('Zone Name', 'f=0;draw=_=>{...}'),
    # ...
]
for name, code in codes:
    chars = len(code)
    status = "OK" if chars <= 280 else "OVER"
    print(f"  {name:14s} {chars:3d} chars  {status}")
```

## Domain Integration

Tsubuyaki works best with domain-specific content. Each sketch encodes a concept from a system (numogram zones, I Ching hexagrams, musical modes, etc.). The constraint forces you to find the *essential visual motion* of each concept — the one thing that makes Zone 3 different from Zone 6.

When pairing with a domain:
- Assign one sketch per element (zone, hexagram, mode, etc.)
- Use the domain's color palette
- Let the domain's dynamics inform the motion (centripetal for Sink, orbital for Hold, etc.)
- The constraint reveals what's essential about each element

## Source Material

- [@Hau_kun](https://x.com/Hau_kun/) — coined #つぶやきProcessing, May 2019
- [@SnowEsamosc](https://x.com/SnowEsamosc) — collected p5.js tsubuyaki with video outputs
- [@yuruyurau](https://x.com/yuruyurau) — dense trig-based character forms
