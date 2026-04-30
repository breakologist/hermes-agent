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
  - Global just-intonation flag (`--just-intonation`) propagates to all sections
  - Automatic manifest generation (`--song-manifest`)
- Audio pipeline (`--render`, `--spectrogram`, `--analyze`, `--manifest`, `--json`)
- Canonical vectors (24 exhaustive triads) in data/

## Just Intonation

Use `--just-intonation` to tune triad motifs to pure just intervals:

- Major triad: root (1/1), major third (5/4), perfect fifth (3/2)
- Minor triad: root (1/1), minor third (6/5), perfect fifth (3/2)

The root note remains in equal temperament; only the third and fifth are period‑adjusted to the simple ratios.

Example:

```bash
mod-writer --triad-motif Ptolemaic --just-intonation --rows 64 --output ptolemaic-just.mod
```


## Architecture

writer.py  – Pattern, Sample, ModWriter (binary packing)
composer.py – ModComposer (grid builder, triad logic, transforms)
song.py    – SongBuilder (multi-section orchestration)
mapping.py – zone/note/gate mappings
utils.py   – waveform generators

## License

MIT code, CC0 data/outputs. See LICENSE and CREDITS.md.


## Optional Dependencies (Enhanced Audio Analysis)

The base `mod-writer` installation includes basic audio analysis via `numpy` and
`scipy`. For *deeper ears* — instrument recognition, genre tagging, beat tracking,
chord estimation — install optional extras:

```bash
# Basic MIR stack (recommended)
pip install mod-writer[mir]

# Premium stack (all features: Essentia, musicnn, madmom)
pip install mod-writer[all]
```

| Extra | Provides | Size |
|-------|----------|------|
| `mir` | `librosa`, `madmom` (beat tracking, chroma, onset profiling) | ~50 MB |
| `essentia` | `essentia` (2000+ features, instrument/genre extraction) | ~120 MB |
| `highlevel` | `musicnn`, `openl3` (deep tagging & embeddings) | ~300 MB |
| `all` | Everything above | ~500 MB |

> **Note:** Optional dependencies are *gracefully degraded* — if a library is not
> installed, `mod-writer` falls back to simpler algorithms or skips that analysis
> category. No crashes, no mandatory heavy installs.

Once installed, use `--profile-audio FILE` or `--mir-seed FILE` to unlock
MIR-powered generation.

