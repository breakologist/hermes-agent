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

### v3: Conceptual Rotation (Different Take on Each)

After v1 (basic) and v2 (refined), v3 changes the *conceptual angle* on each zone. Not just more/less complex — a fundamentally different metaphor:

| Zone | v1/v2 concept | v3 concept |
|------|--------------|------------|
| 0 Void | Many orbiting points | Single point that occasionally jumps to random pos then returns |
| 1 Stability | Grid breathing | Waves rippling outward from center across the lattice |
| 3 Triangle | Spiral vortex | Three rotating triangles (geometric, not particle) |
| 4 Catastrophe | Displaced grid | Four corners connected by pulsing lines (gate opens/closes) |
| 7 Blood | Organic pulse | Grid points bisected by sweeping diagonal (growing on one side) |

The v3 should feel like a *third voice* — not louder or quieter, but speaking about the same thing from a different angle entirely. Each sketch's concept should be something you couldn't reach by iterating on v2.

### v4: Paradigm Shift (Different Lens Entirely)

The fourth pass abandons the previous visual vocabulary entirely. Where v1-v3 share a particle/geometry language, v4 introduces a completely different representational system. Example: signal topology (modular synthesis waveforms as zone metaphors) replacing particle systems.

**Implementation pattern (learned from numogram-tsubuyaki v4 production):**
1. Extract zone metadata from prior passes (names, regions, hex colors) via regex on the HTML files — e.g. `const ZONES = \[{id:\s*0,\s*name:\s*"Void"` — instead of re‑typing by hand.
2. Choose a foreign ontology (e.g., synthesis signal processing) whose primitives (sine, square, wavefold, LFO) map homomorphically onto the domain's dynamics.
3. Build the mapping table explicitly (zone → waveform → numogram rationale) before writing any code.
4. Generate the HTML gallery, then validate bracket/paren balance programmatically (`Open/Close` count) before committing.
5. Render compressed code strings for display; use expanded `draw(p)` functions for execution.

| Zone | v3 concept | v4 concept (signal topology) |
|------|-----------|------------------------------|
| 0 Void | Jumping pixel | Noise floor — random voltage |
| 2 Separation | Dual orbits | Hard sync — two oscillators detuning |
| 4 Catastrophe | Pulsing gate | Wavefolding — sine peaks folding into harmonics |
| 7 Blood | Sweeping cut | Pulse wave — LFO-gated rhythmic threshold |
| 9 Iron Core | Converging spiral | Feedback resonance — self-oscillation building |

v4 is not "more complex" or "a different angle." It is a different *ontology*. The same ten zones, mapped through a foreign system. This is the deepest iteration because it reveals structural homologies: the numogram's Separation is isomorphic to oscillator hard-sync detune; its Pressure is isomorphic to audio compression limiting.

**Rule:** Before proposing v4, read v1-v3 carefully. The fourth voice must be genuinely foreign to the first three. If it could have emerged from iterating v2, it is v3, not v4.

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

### Gallery + Wiki Dual Publishing

Long tsubuyaki strings (200+ chars) clip in HTML card layouts due to `overflow: hidden` and unbreakable code. The HTML gallery is for live visual experience; the wiki is for canonical code reference.

**Workflow:**
1. Build the HTML gallery as the primary artifact (`~/projectname.html`)
2. Create/update a wiki page with all code blocks in markdown fenced code (` ``` `)
3. Cross-link: gallery points to wiki for "full code reference," wiki points to gallery for "live version"
4. For series (v1, v2, v3, v4), keep all versions in the wiki, only the latest in the active gallery unless the user requests otherwise

**Pitfall:** Do not rely on CSS `overflow-x: auto` on `<pre>` blocks inside card containers with `overflow: hidden`. The card boundary clips before the pre scroll activates. Either remove card `overflow: hidden` (breaks rounded corners) or accept that the wiki is the code reference.

**File naming convention:**
- `~/projectname.html` — v1
- `~/projectname-v2.html` — v2
- `~/projectname-v3.html` — v3
- `~/projectname-v4.html` — v4
- Wiki: `wiki/projectname-museum.md` — all versions with full code blocks

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
