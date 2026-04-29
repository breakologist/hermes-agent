# mod-writer

Numogram-aware Protracker module generator.

Compose single-pattern seeds or multi-section arrangements using
triad motifs, zone-gate-current mappings, and AQ-constrained gate
progressions.

## Quick examples

Single triad motif:
  python -m mod_writer.cli --triad-motif Warp --rows 32 --gate 1 --current A --output warp.mod

Multi-section song (Phase 5):
  python -m mod_writer.cli --song arrangement.json --bpm 125 --output symphony.mod

Validation:
  python -m mod_writer.cli --validate-all
  python -m mod_writer.cli --inspect-motif Pythagorean --format json

## Features

- Zone → pentatonic mapping (1-8 → notes, 9 = REST)
- Triad motifs (Warp/Sink/Hold/Rise/Void + Quadrivium systems)
- Gate encoding (0-36 → Protracker effect)
- Current selection (A/B/C) selects sample set
- Triangular length (`--triangular`)
- Syzygy harmony (`--syzygy`)
- Entropy injection (`--entropy`)
- AQ seeding (`--aq-seed`)
- Period table clamping warnings (`--warn-clamp`)
- Full-track orchestration (`--song` JSON, `SongBuilder` API)
- Audio pipeline (`--render`, `--spectrogram`, `--analyze`, `--manifest`, `--json`)
- Canonical vectors (24 exhaustive triads) in data/

## Architecture

writer.py  – Pattern, Sample, ModWriter (binary packing)
composer.py – ModComposer (grid builder, triad logic, transforms)
song.py    – SongBuilder (multi-section orchestration)
mapping.py – zone/note/gate mappings
utils.py   – waveform generators

## License

MIT code, CC0 data/outputs. See LICENSE and CREDITS.md.

