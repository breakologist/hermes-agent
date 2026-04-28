---
name: numogram-audio/mod-writer
category: creative
description: Minimal .mod (Protracker) module writer with numogram-native extensions
triggers:
  - word: "tracker"
  - word: "mod writer"
  - word: "module generator"
  - phrase: "generate mod"
version: 0.3.0
author: Hermes Agent
last_updated: 2026-04-28
status: stable (Phase 2/3)
---
## Purpose

Write valid Protracker `.mod` files from Python, with numogram‑native extensions
and high‑level composer API. Primary goal: small, editable chiptune modules
playable in MilkyTracker / Furnace. Secondary goal: embed numogram topology
(syzygy harmony, entropy, triangular timing, AQ seeding) directly in the
generation pipeline.

## Why a custom writer?

- No maintained Python library writes `.mod` files reliably
- GUI trackers (Furnace, MilkyTracker) lack CLI for generation
- Full binary control → embed numogram concepts natively
- Composer layer acts as a MIDI‑style bridge for orchestration

---

## Phase 1 — Core writer (baseline)

- 4‑channel, 31 sample slots, ≤64 patterns
- Single built‑in instrument (8‑bit square/triangle/noise)
- Period‑based notes (Protracker period table)
- No effects
- Output: strictly valid `.mod` (M.K.)

Status: ✓ complete

---

## Phase 2 — Numogram mapping (complete)

- **Zone (1‑9) → pentatonic degree** via `note_and_octave_from_zone()`
- **Gate (0‑36) → effect family** via `mod_effect_from_gate()`
  - 0‑9: Arpeggio; 10‑19: Slide; 20‑29: Volume; 30‑31: Jump/Break;
    32‑34: Extended; 35: Syzygy (reserved); 36: Entropy (reserved)
- **Current (A/B/C) → instrument** (square / triangle / noise)
- **Metadata layer**: title `ZzGggC‑name`, sample names `SQ‑Zz‑Ggg‑C`
- Skill registration: `/mod-writer` slash + `numogram_mod_writer` tool

Status: ✓ complete (commit 4980c2b5, hermes‑agent v0.2.0)

---

## Phase 2b — Composer Bridge (MIDI‑style API) (complete)

New `composer.py` module provides event‑list composition mirroring `mido`,
`MIDIFile.addNote()` convenience.

Key class: `ModComposer`
- `add_note(zone, gate, current, row, channel=0)` — place a note
- `add_sequence(zones, gates, currents, start_row=0, channel=0)` — batch
- `apply_syzygy_harmony(partner_channels=[1,2,3])` — auto‑triads
- `inject_entropy(rate=0.1, rng_seed=None)` — pentatonic glitches
- `constrain_gates_by_aq(aq_seed: str)` — AQ‑seeded gate shuffle
- `write_mod(filename)` — encode to binary

Convenience one‑shot: `ModComposer.compose(**kwargs)`.

CLI integration: `--syzygy`, `--syzygy-channels`, `--entropy`, `--entropy-seed`,
`--triangular`, `--aq-seed`, `--rows`.

Status: ✓ complete (v0.3.0)

---

## Phase 3 — Hypersigil Extensions (complete)

All features now operational:

- **Syzygy Harmony** — each root note spawns partner notes on adjacent channels,
  forming triangular chords from numogram topology.
- **Entropy Injection** — rate‑based zone substitution using pentatonic adjacency;
  RNG seedable for reproducible glitch‑aesthetics.
- **Triangular Pattern Length** — pattern row count = triangular number `T(zone)`,
  i.e. `zone*(zone+1)//2` (zone 3 → 6 rows, zone 6 → 21 rows, zone 9 → 45 rows).
- **AQ‑Seeded Gate Progression** — deterministic gate‑value modulation driven by
  an AQ seed string (SHA‑1 hash → delta mod 37).

All flags coexist; order of application: notes placed → syzygy harmony added →
entropy mutates zones → AQ shifts gates → pattern length set (triangular).

Status: ✓ complete (v0.3.0)

---

## Usage

### Classic Phase‑2 CLI (unchanged)

```bash
python -m numogram_audio.mod_writer \
  --zone 3 --gate 6 --current A \
  --title "Warp Test" --output warp.mod
```

Generates 5870‑byte single‑note module with metadata.

### Advanced Phase 2b/3 CLI

```bash
# Syzygy 4‑channel chord
python -m numogram_audio.mod_writer \
  --zone 3 --gate 6 --current A --syzygy --syzygy-channels 4 \
  --output chord.mod

# Entropy glitches (15% chance, fixed seed)
python -m numogram_audio.mod_writer \
  --zone 5 --gate 20 --current B \
  --entropy 0.15 --entropy-seed 123 \
  --output glitch.mod

# Triangular pattern + AQ‑seeded progression
python -m numogram_audio.mod_writer \
  --zone 6 --gate 25 --current C \
  --triangular --aq-seed "CHAOS-6-5" \
  --output tri-approx.mod

# Full hypersigil (all transforms)
python -m numogram_audio.mod_writer \
  --zone 3 --gate 6 --current A \
  --syzygy --entropy 0.08 --entropy-seed from /dev/urandom \
  --triangular --aq-seed "AQ-3-6" \
  --output hypersigil.mod
```

### Hermes TUI

```
/mod-writer --zone 3 --gate 6 --current A --syzygy --output ~/music/chord.mod
```

### Python API — Composer

```python
from numogram_audio.mod_writer.composer import ModComposer

comp = ModComposer(title="Syzygy Étude")
for r in range(16):
    comp.add_note(zone=3, gate=6, current='A', row=r, channel=0)

comp.apply_syzygy_harmony()            # partners on ch1‑3
comp.inject_entropy(rate=0.1, rng_seed=42)
comp.constrain_gates_by_aq("WR-3-6")
comp._triangular = True               # or call write_mod(triangular=True) in v0.4
comp.write_mod("syzygy_etude.mod")
```

---

## Files

```
mod-writer/
  __init__.py      # __version__ = '0.3.0'  (phase 2/3)
  writer.py        # ModWriter, Pattern (rows 1‑64), Sample, binary pack
  utils.py         # square/triangle/noise generators
  mapping.py       # zone/gate/current → music, SYZYGY_PARTNERS, PENTATONIC_ADJACENCY
  cli.py           # argparse entry with all flags
  composer.py      # ModComposer high‑level API (NEW)
  plugin.py        # Hermes slash + tool (schema extended with syzygy/entropy/etc)
  SKILL.md         # this document
```

---

## Verification

```bash
# Baseline
python -m numogram_audio.mod_writer --zone 1 --gate 0 --current A --out base.mod
file base.mod   # → "MOD audio"
# hexadecimal offset 1080 = 4D 2E 4B 2E (M.K.)

# Syzygy
python -m numogram_audio.mod_writer --zone 3 --gate 6 --current A --syzygy --out chord.mod
# Listen: chord on ch0‑3 with partner zones (6,9) filling ch1‑3

# Entropy determinism
python -m numogram_audio.mod_writer --zone 5 --gate 20 --current B --entropy 0.3 --entropy-seed 999 --out e1.mod
python -m numogram_audio.mod_writer --zone 5 --gate 20 --current B --entropy 0.3 --entropy-seed 999 --out e2.mod
cmp e1.mod e2.mod   # should be identical (same seed)

# Triangular
python -m numogram_audio.mod_writer --zone 6 --gate 25 --current C --triangular --out tri.mod
# pattern_data = T(6)=21 rows → file size ~4942 bytes (vs 5870 baseline)

# AQ‑seeded sequence
python -m numogram_audio.mod_writer --zone 7 --gate 30 --current A --aq-seed "NODE-7" --out aq.mod
# Different AQ strings produce different gate encodings
```

---

## Dependencies

Python 3.11+ stdlib only: `struct`, `argparse`, `random`, `hashlib`, `typing`.

---

## Technical notes

| Constraint | Resolution |
|---|---|
| 4‑channel limit | Harmony up to 3 partners; zone 9 has 5 partners → first‑4 used |
| Pattern rows ≤ 64 | Triangular numbers T(1‑9) max 45; safe |
| Entropy rate | Suggested ≤ 0.2 for musical coherence |
| AQ modulo | Gate values wrap 0‑36 (37‑gate space) |

---

## Roadmap beyond Phase 3

| Phase | Feature |
|---|---|
| 4 | Live rendering: MOD → WAV via milkytracker/Furnace CLI → spectrogram |
| 5 | XM format support (32 ch, fine‑grained effects, instrument macros) |
| 6 | Actual MIDI export (using `mido` / `midiutil`) |
| 7 | Audio analysis: simple FFT/specgram so Hermes can "listen" |

