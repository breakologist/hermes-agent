---
name: numogram-audio/mod-writer
category: creative
description: Minimal .mod (Protracker) module writer with numogram-native extensions
triggers:
  - word: "tracker"
  - word: "mod writer"
  - word: "module generator"
  - phrase: "generate mod"
version: 0.2.0
author: Hermes Agent
last_updated: 2026-04-28
---

## Purpose

Write valid Protracker `.mod` files from Python, with optional numogram-driven
composition layers. Primary goal: produce small, editable chiptune modules that
play in MilkyTracker / Furnace. Secondary goal: extend tracker semantics with
numogram topology (syzygy harmony, gate effects, current morphing).

## Why a custom writer?

- No existing Python library writes `.mod` files reliably (pymod/modfile are dead/readonly)
- GUI trackers (Furnace, MilkyTracker) have no CLI for generation
- Full control over binary format → no format ambiguities
- Can embed numogram concepts directly in the generator

## Phase 1 — Core writer (baseline)

## Phase 2 — Numogram mapping (complete)

- Zone (1–9) → pentatonic degree (via `note_and_octave_from_zone`)
- Gate (0–36) → effect family encoded as Protracker command/param (`mod_effect_from_gate`)
- Current (A/B/C) → instrument (sample index 1/2/3)
- Metadata layer: song title and sample names embed ZzGggC tags
- Skill registration: `/mod-writer` slash command + `numogram_mod_writer` tool available


Valid .mod with:
- 4 channels, up to 64 patterns, up to 31 instruments
- Single built-in instrument (8-bit square wave sample, generated in memory)
- Period-based notes (standard Protracker periods)
- No effects

Output plays identically in MilkyTracker and Furnace.

## Phase 2 — Numogram mapping

- Zone (1–9) → pentatonic scale degree
- Gate (0–36) → effect family (arpeggio, slide, volume)
- Current (A/B/C) → instrument selection (square/triangle/noise)

## Phase 3+ — Hypersigil extensions

- Syzygy harmony (auto-generated chords from partner zones)
- Entropy injection (hardware RNG note variation)
- Syzygy-time phasing (pattern lengths = triangular sums)
- AQ seed embedding (subtle constraints hidden in pattern data)

## Usage

```bash
# Minimal valid module
python -m numogram_audio.mod_writer --title "Test Song" --pattern-count 1 --output test.mod

# Numogram-driven composition
python -m numogram_audio.mod_writer \
  --seed "AQ-CHAOS-3-6" \
  --zone 3 --gate 12 --current A \
  --syzygy-harmony --output chaos.mod
```

## Files

```
mod-writer/
  __init__.py         # ModWriter class, note/period tables
  writer.py           # Binary packing (header, patterns, samples)
  samples.py          # Built-in waveform generators (square, triangle, noise)
  mapping.py          # Numogram → music mapping dicts
  cli.py              # argparse entry point
  references/
    modformat.md      # .mod spec summary (extracted from modarchive.org)
  scripts/
    play.sh           # milkytracker / furnace playback helper
```

## Dependencies

Python stdlib only: `struct`, `argparse`, `random` (or `os.urandom` for entropy).

No external libs required.

## Verification

```bash
# Play in MilkyTracker (installed)
milkytracker test.mod

# Or Furnace
furnace test.mod
```

## Status

Phase 1 implementation ready to scaffold.
