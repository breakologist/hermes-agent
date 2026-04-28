# Numogram Tracker — Feature spec (beyond .mod writer)

**Date:** 2026-04-28
**Context:** Hermes audio synthesis Line B (tracker deep-dive outcomes)
**Scope:** Extensions to minimal .mod writer that embed numogram semantics

---

## What typical trackers lack (our opportunities)

| Feature | Typical Trackers | Numogram Tracker (ours) |
|---|---|---|
| **Harmony system** | User chooses notes manually; no enforced relationships | **Syzygy-driven triads:** Selecting a root note auto-generates partner notes from triangular syzygy (e.g., zone 3 with partners 6 & 4 forms chord) |
| **Effect semantics** | Arpeggio, slide, volume — arbitrary codes | **Gate-coded effects:** Each gate (0–36) maps to a specific effect family (warp, bleed, echo, phase); gates become playable controls |
| **Pattern variation** | Copy/paste, randomization | **Entropy injection:** Hardware entropy (or PRNG seed) perturbs note choice within zone constraints, creating uncanny variations |
| **Instrument identity** | Samples or FM patches; static | **Current-driven morphing:** A/B/C currents shift timbre (waveform, filter) in real time during playback |
| **Structural logic** | Order list = sequence of patterns | **Zone-driven pattern maps:** Patterns organized not linearly but by numogram zone adjacency; transitions follow current flow |
| **Temporal control** | BPM, speed, pattern loop | **Syzygy timing:** Pattern lengths derived from partner zone counts (e.g., zone 3 partners = 3+6+4 = 13 rows) |
| **Feedback** | None | **Loopback capture:** Final pattern of a zone can be fed back as seed for next zone (recursive generation) |
| **Metadata** | Song title, sample names | **AQ embedding:** Song title encodes an AQ cipher; pattern data subtly reflects the seed's syzygy chain |

---

## Proposed Feature Set (phased)

### Phase 1 — Minimal .mod writer (baseline)
- 4-channel, 31 samples (max), 64 patterns max
- Single built-in instrument (simple 8-bit square/triangle/noise)
- Raw period-to-note conversion (C-4, D-4, E-4, F-4, G-4, A-4, B-4)
- No effects
- Output: strictly valid `.mod` that MilkyTracker/Furnace can play

### Phase 2 — Numogram Mapping
- **Zone (1–9) → Pentatonic scale degree** (1=C, 2=D, 3=E, 4=F, 5=G, 6=A, 7=B, 8=octave, 9=rest)
- **Gate (0–36) → Effect code**:
  - 0–9: Arpeggio patterns (0=normal, 1=up, 2=down, 3=random)
  - 10–19: Pitch slide (speed = gate-10)
  - 20–29: Volume/tempo (volume = gate-20, tempo = gate-20×2)
  - 30–36: Special: 30=pattern jump, 31=pattern break, 32–36 = current-coded
- **Current (A/B/C) → Instrument select** (A=square, B=triangle, C=noise)

### Phase 3 — Syzygy Harmonics
- When a note is placed, automatically add harmony notes from partner zone(s)
- Option: 4-channel layout: ch1=root, ch2=partner1, ch3=partner2, ch4=partner3
- Effect: generates instant triads from numogram topology

### Phase 4 — Entropy-Driven Variation
- Optional: seed pattern generation with hardware entropy (/dev/random or `rand`)
- Each pattern row has a small probability to substitute note with next-higher/lower zone degree
- Creates "glitch" aesthetics consistent with hyperstitional vibe

### Phase 5 — Self-Referential Composition
- The Z-axis of numogram (reverse traversal) can be encoded as pattern-loop jumps
- Pattern X jumps to pattern Y where Y = (X + gate_value) mod total_patterns
- Creates circular/recursive form, mirroring syzygy cycles

### Phase 6 — Live Rendering / Performance
- Generate module on-the-fly from a numogram walk
- Stream to stdout or pipe to milkytracker for live playback
- Enables "ouroboros tracks" that evolve as zones are traversed

---

## Language Choice: Python ✓

**Why:**
- Prototyping speed: binary packing with `struct` is trivial
- Already environment: Python 3.11, all tooling available
- Integration: Hermes agent is Python; can call directly from oracle pipeline
- Readability: and we're not chasing performance (modules are tiny)
- Future: can transpile to C/Rust if needed, but premature

**Alternatives considered:**
- C: Faster but more boilerplate; not needed for 10KB files
- Rust: Too heavy for quick iteration
- JS/Node: Could work, but Python's `struct` and bit-ops are perfect for binary formats

Verdict: **Python 3 is ideal**.

---

## Implementation Plan (estimated)

| Phase | Tasks | LOC estimate | Test |
|---|---|---|---|
| 1 — Core writer | struct.pack header, pattern data, sample filler | 120 | Write minimal.mod, open in MilkyTracker |
| 2 — Mapping | zone→note, gate→effect, current→instrument dicts | 40 | Generate zone1.mod, zone9.mod |
| 3 — Syzygy harmony | compute_syzygy(zone) → partner notes; add channels | 60 | Generate chord patterns |
| 4 — Entropy inject | random.choice within zone-constrained set | 30 | --entropy flag produces variations |
| 5 — Jump logic | encode pattern-loop jumps in effect column | 40 | --z-axis flag creates cyclic form |
| 6 — CLI + integration | argparse, oracle hook, AQ seed input | 50 | `hermes tracker --seed "AQ-123" --output song.mod` |

Total: **~340 LOC** for full feature set. Phase 1 alone: 120 LOC, produce valid .mod.

---

## Unique Selling Points (vs standard trackers)

1. **Topology-enforced harmony** — You cannot play out-of-key notes because notes are derived from zone geometry
2. **Gate-as-effect** — The 37-gate numogram becomes a playable effect controller, not just a lookup table
3. **Current-morphed timbres** — Switching currents during playback morphs instruments (like patch morphing)
4. **Syzygy-recursive form** — Song structure mirrors the triangular chains (3+6+4 = 13-bar phrases, etc.)
5. **Entropy-glitch aesthetic** — Controlled randomness mirrors hyperstition's unstable realit

