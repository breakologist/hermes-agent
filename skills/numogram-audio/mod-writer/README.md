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


## Classifier — MIR to AQ Prediction (Phase 3)

> **Status:** Experimental. Requires `pip install -e .[classifier]`.

The classifier module (`mod_writer.classifier`) learns to predict a track's AQ value from MIR features. It's a proof-of-concept "ears that hear the numogram": audio in, zone/gate candidates out.

### Usage

```bash
# Profile an audio file and predict its AQ
mod-writer --classify /path/to/audio.wav

# Batch classify a directory
mod-writer --classify-dir /path/to/music_collection/

# After training, generate synthetic MODs for a target AQ and verify
mod-writer --aq-seed 42 --render --analyze
```

### How it works

1. **Synthetic dataset** — 100 MOD files (AQ 0-99, zone=1) rendered to WAV, profiled via `mir_profiler` → feature vectors
2. **Training** — `MLPRegressor(hidden=(128,64))` learns mapping `(29 MIR features) → AQ`
3. **Evaluation** — held-out test accuracy ~10% within ±5 AQ, zone accuracy ~10% (baseline)
4. **Artifacts** — `mod_writer/classifier/artifacts/{scaler.joblib,model.joblib}`

### Current limitations

- Synthetic training data uses only square/triangle/noise waveforms — extremely limited timbre
- MIR features capture spectral/rhythmic content, not symbolic structure
- Model accuracy near chance on synthetic data; generalization to real audio unproven
- Zone prediction from AQ is indirect (regression → rounding)

Next steps (Phase 3.3): evaluate on real audio collection, explore better models (RandomForest, gradient boosting), enrich features (musicnn embeddings). See `run_phase3.py` for full pipeline.

## Phase 3.3 — Real Audio Validation

A proof-of-concept end-to-end pipeline has been run on 10 tracks from the
personal music collection. Results cached at
`mod_writer/classifier/artifacts/real_audio_predictions.csv`.

### Running it yourself

```bash
# Ensure classifier deps installed
pip install -e .[classifier]

# Evaluate a directory of audio files (any format)
python eval_real_audio.py   # uses curated list from MUSIC_ROOT
```

The script:
1. Walks a curated list of esoteric/ambient/experimental artists
2. Transcodes MP3/FLAC → WAV via `ffmpeg`
3. Extracts MIR features (`mir_profiler`, Essentia low/mid level)
4. Predicts AQ via trained `MLPRegressor`
5. Writes CSV: `file, predicted_aq, zone, duration_s, bpm, key, scale`

**Observations from the first run (10 tracks):**
- 9/10 tracks predicted **Zone 6 (Venus)**; 1 track (Gregorian Chant Rosary) → **Zone 4 (Mercury)**
- All AQ values clustered ~50–58 (near training set mean ~49.5)
- BPM and key often unavailable for esoteric/ambient drone works
- The model has not learned meaningful discrimination yet — expected given synthetic-only training

**Next:** add more diverse synthetic data (multiple zones), switch to predicting delta (0-36), or train on real-labeled data via filename heuristic.


## Phase 3.4 — CLI integration

The `--classify` and `--classify-dir` flags provide direct CLI access to the AQ classifier
without requiring intermediate MOD generation:

```bash
# Single-file classification (table output)
mod-writer --classify track.mp3

# Batch classification with limit and CSV output
mod-writer --classify-dir /path/to/music/ --classify-limit 20 --classify-format csv
```

Output formats:

- `table` (default) — aligned human-readable columns
- `json` — structured single-track object
- `csv` — header + rows for batch runs

All formats include: `file`, `predicted_aq`, `zone`, `duration_s`, `bpm`, `key`, `scale`.
The CLI uses the same feature extraction pipeline as `--profile-audio` and weights the
32-dimensional MIR descriptor set with the saved `scaler.joblib` and `model.joblib`.

Validation on the 10-track development set showed a strong Zone 6 (Venus) bias — expected
given the uniform zone-1 synthetic training distribution. Future work will diversify the
training dataset across multiple zones to improve classifier generalisation.

---

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

