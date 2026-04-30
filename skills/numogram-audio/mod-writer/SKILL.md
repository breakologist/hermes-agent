---
name: numogram-audio/mod-writer
category: creative
description: Minimal .mod (Protracker) module writer with numogram-native extensions
triggers:
  - word: "tracker"
  - word: "mod writer"
  - word: "module generator"
  - phrase: "generate mod"
version: 0.6.0
author: Hermes Agent + CCRU lineage
last_updated: 2026-04-30
status: stable (Phase 5 full-track orchestration)
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
`--triangular`, `--aq-seed`, `--rows`, `--triad-motif`.

Status: ✓ complete (v0.3.0)

### Phase 2c — Triad‑Motif Harmony (complete)

- **Triad‑Motif policy** — given a motif name, select a triad (root, quality, octave)
  whose zone set aligns with the motif's target zones.
- Implemented via `ModComposer.apply_triad_motif(motif, rows, gate, current, channels)`.
  The function computes absolute semitone indices for root, third, and fifth, then
  derives **individual octaves** for each chord tone (third/fifth may cross octave
  boundaries). Initial version erroneously used the candidate octave for all three
  notes, breaking motifs whose fifth exceeds the root octave (e.g., Pythagorean G‑major).
  Fixed 2026‑04‑29: now zones match the pre‑computed triad‑zone tables for all candidates.
- CLI flags:
  - `--triad-motif NAME` — generate triad texture (overrides `--zone/--gate/--current`);
    accepts any key from `TRIAD_MOTIF_POLICY` (Numogram currents + Quadrivium systems).
  - `--validate-motif NAME` — **dry‑run validation**: builds the motif pattern in‑memory,
    extracts period values, maps them back to zones via `period_for_note`, and prints a
    JSON report containing expected vs observed zone sets plus a pass/fail flag. No `.mod`
    file is written. Useful for CI and quick sanity checks.
  - `--rows N` controls pattern length (default 16); `--triangular` forces triangular
    pattern length derived from the motif's zone.
- Overrides the default single‑channel seed pattern; generates a three‑voice chord
  texture on channels 0–2 using the highest‑ranked candidate from the policy.
- See `composer.py` for the full policy dictionary; zone‑triad tables are in
  `docs/wiki/assets/triad_zone_tables.json` and reference pages `tracker-motif-triads-reference`,
  `tracker-music-theory-mappings`.
- New wiki page `quadrivium-music-digest` explores the theoretical background.
- All five motifs (Sink, Monochord, Pythagorean, Ptolemaic, Harmonic) now validate
  in‑memory with correct zone sets.

**Quadrivium motif reference**

| Motif       | Triad (root, quality, octave) | Zone triple | Rationale |
|-------------|------------------------------|-------------|-----------|
| Monochord   | D minor 3                     | (1, 3, 6)   | Triangular syzygy cluster from monochord division points |
| Pythagorean | G major 3                     | (3, 6, 8)   | Perfect fifth (3:2) of C; embodies the 3‑limit tuning drive |
| Ptolemaic   | C major 3                     | (1, 5, 8)   | Just intonation major triad 4:5:6; pure major third (zone 5) |
| Harmonic    | C major 4                     | (2, 4, 8)   | Harmonic series partials 4,5,6 transposed to one octave |

Status: ✓ complete (v0.5.0, octave‑fix + `--validate-motif` added 2026‑04‑29)

---

#### Implementation methodology for new motif systems

When extending the mod-writer with a new motif or harmony system (e.g., just-intonation
mode, hexagram chords, or additional Quadrivium systems), follow this validated pipeline
to ensure mathematical soundness, documentation completeness, and CI‑ready verification:

1. **Derive zone mapping from canonical sources**  
   Start from the digital‑root formula `zone = digital_root(semitone_index + 1)`.
   Compute the expected zone triple for each candidate triad (root, quality, octave)
   using the exhaustive `triad_zone_tables.json` as ground truth. Select the
   candidate whose zone set best matches the motif's target zones.

2. **Implement with absolute‑octave handling**  
   In `apply_triad_motif` (or similar), compute absolute semitone indices for
   each chord tone (`root_semi`, `third_semi`, `fifth_semi`) and derive individual
   octaves via `// 12`. Never reuse the policy octave for all notes; intervals
   that cross octave boundaries (e.g., a perfect fifth above G3) must place the
   fifth in the next octave. This prevents the "Pythagorean bug" where the fifth
   rendered one octave too low.

3. **Add an in‑memory validation flag**  
   Implement `--validate-motif NAME` (or `--validate-<feature>`) that:
   - Builds the pattern in memory without writing a file
   - Extracts period values from the `Pattern` object
   - Maps periods back to zones via `period_for_note` reverse lookup
   - Compares observed zone set to expected and prints JSON + exit code (0 pass, 1 fail)
   This serves as a CI gate and rapid sanity check during development.

4. **Update documentation in layers**  
   - **SKILL.md**: Add the motif to `TRIAD_MOTIF_POLICY`, document the candidate
     selection rationale, update the Phase 2c subsection and version/status.
   - **Wiki (vault)**: Create or extend a reference page (`tracker-motif-…`) with
     a table of all candidates and their zone triples. For theoretically rich
     motifs, write a digest page linking the historical system to the numogram
     mapping (as with Quadrivium).
   - **Wiki (export)**: Mirror all vault changes via rsync; ensure `index.md`
     Recent Additions lists the new pages.
   - **Logs**: Append an after‑action report to both vault and export `log.md`
     summarising derivation, implementation decisions, validation results, and
     bugs fixed.

5. **Verify exhaustively before commit**  
   Run the validation flag for all candidates of the new motif. For triad systems,
   check all 12 roots × 2 qualities (or at least every zone appears correctly)
   to catch any octave‑boundary errors. Ensure the in‑memory zone fingerprint
   matches the pre‑computed table exactly.

6. **Git hygiene**  
   Stage only the affected skill directory and wiki pages; commit with a clear
   message prefix (`feat(numogram-audio): …` for code, `docs: …` for wiki).
   Push the export wiki to GitHub separately.

Following this pattern ensures every new motif system is **mathematically sound**,
**documented in depth**, and **verifiable** both in‑memory and (later) in rendered audio.

---

```bash
# Generate a 16‑row texture with the Sink triad motif
python3 cli.py \
  --triad-motif Sink \
  --rows 16 \
  --output sink_triad.mod \
  --title "SinkTriad"
```

The `--triad-motif` flag activates `apply_triad_motif()` which selects the
highest‑ranked candidate from `TRIAD_MOTIF_POLICY` (root, quality, octave)
and writes three‑voice root‑third‑fifth across channels 0‑2.



### Structural Improvements (v0.5.1 — 2026-04-30)

Resolved initial development frictions by adding transparent tooling,
canonical validation, documentation, and test coverage.

#### Added tooling
- `ModComposer.inspect_motif()` — returns full pattern metadata (per-row
  note/octave/zone/period/gate) and zone distribution; supports JSON/CSV/table
  output. Resolves "invisible patterns" friction.
- CLI: `--inspect-motif NAME [--format table|json|csv]`
- CLI: `--validate-all` — exhaustively validates all 24 canonical triad vectors
  against expected zone triples; exits non‑zero on any failure.

#### Canonical test vectors
- `data/canonical_vectors.json` generated by enumerating all 24 triads
  (12 roots × major/minor) at reference octave 3 using `NOTE_OFFSET` mapping.
- Each entry includes zones, note names, per‑tone octaves.
- `--validate-all` loads this file and reports pass/fail per triad.
- Result: **24/24 vectors pass** — triad→zone mapping confirmed.

#### Period table clarity
- `writer.py`: added `PERIOD_TABLE_LENGTH = 87` constant.
- Documented Amiga period arithmetic: valid index range 0–86 (C-0 to D7),
  semitone formula, and clamping behavior (out‑of‑range → period 0).
- Added docstring to `period_for_note()` explaining parameters, return, and edge cases.

#### Triangular semantics formalization
- Expanded `build_patterns_from_grid()` docstring with full description of:
  - Normal vs triangular length calculation.
  - Triangular number formula `T(n)=n*(n+1)//2` derived from `max_zone`.
  - 64‑row cap and its justification (Protracker pattern limit).
  - Syzygy topology link: pattern length mirrors spatial zone triple geometry.
- Added `tests/test_triangular_semantics.py`:
  - length calculation tests (including cap at 64)
  - syzygy correspondence check (21 rows for max_zone=6)
  - zone‑exhaustiveness per motif (Sink, Monochord, Pythagorean, Ptolemaic, Harmonic)
  - zone‑value validity guard (no zone ≥10)
  - period table clamping verification

All tests pass (5/5).

#### Packaging & licensing
- Package restructured as `mod_writer/` (underscore import name).
- `pyproject.toml` added: `pip install .` supported, entry point `mod-writer`.
- Dual license: **MIT (code)** + **CC0 1.0 (data/generated content)**.
- `CREDITS.md` acknowledges Hermes Agent / Etym CCRU provenance.

Status: ✓ complete (v0.5.1)



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


## Phase 5 — Full-Track Orchestration (complete)

Composition no longer stops at a single pattern. The `SongBuilder` orchestrates
multiple sections, each with its own `ModComposer` instance, then merges samples
and chains patterns into a complete module.

**New CLI flags:**
- `--song FILE.json` — load arrangement from JSON (sections, patterns, motifs)
- `--song-manifest` — write a companion `song.manifest.json` alongside the `.mod`
  containing section metadata, pattern counts, sample map, and BPM
- `--bpm N` — global tempo (affects playback speed)

**Python API:**
```python
from mod_writer.song import SongBuilder
SongBuilder(title="My Track", bpm=120)\
    .add_section(motif="Warp", rows=32, triangular=True)\
    .add_section(zone=5, rows=16, gate=0, current="B")\
    .write("track.mod")
```

**Features:**
- Multi‑section arrangements with independent `ModComposer` instances
- Automatic sample renaming to avoid slot collisions between sections
- Pattern caching by parameter hash (re‑use identical sections)
- Integration with Phase 4: `--render`, `--spectrogram`, `--analyze`,
  `--manifest`, `--describe` operate on the final merged module

Status: ✓ complete (v0.6.0)

---

---

## Phase 6 — MIR Audio Profiling (in progress)

*Optional, modular music information retrieval integration.*

### Phase 6a — Optional Dependency Stack (complete)

- `librosa` & `madmom` as optional extras (`pip install mod-writer[mir]`)
- Graceful degradation: missing deps → fallback to baseline analysis
- Core API unchanged; all new features behind availability flags

Status: ✓ scaffolding complete (v0.6.1-plan)

### Phase 6b — Unified MIR Feature Schema (pending)

Define a single JSON feature envelope that normalises outputs from:
- Librosa (chroma, beat, chord, structural segmentation)
- Madmom (DBN beat & downbeat tracking with confidence)
- Essentia (2000+ low/mid/high-level descriptors)
- musicnn / openl3 (deep tags & embeddings)

Schema fields:
```json
{
  "lowlevel": { "mfcc": [...], "spectral_contrast": [...], ... },
  "midlevel": { "bpm": 120.5, "key": "C", "chords": [...], "beats": [...] },
  "highlevel": { "genre": {"electronic": 0.87}, "instruments": {...}, "mood": {...} },
  "metadata": { "duration": 49.2, "sample_rate": 44100, "channels": 2 }
}
```

### Phase 6c — CLI & API Surface (pending)

- `--profile-audio FILE` → print JSON feature report
- `--mir-seed FILE` → compute features → hash → AQ seed → generate
- `SongBuilder.load_audio_profile(FILE)` → constrain sections by audio structure
- Python API: `MIRFeatureExtractor.extract(path) -> FeatureSet`

### Phase 6d — Essentia Premium Path (pending)

- Wire `essentia.standard.MusicExtractor` as a high‑accuracy branch
- Map Essentia's descriptor space into unified schema
- Document install: `apt-get install libessentia-dev` or use `pip` wheel (Python 3.11+)

### Phase 6e — Deep Tagging (pending)

- `musicnn` inference → instrument/genre/mood tags
- `openl3` embedding → for future k‑NN classification
- Cache predictions to avoid recomputation

### Phase 6f — Audio → AQ Mapping Model (pending)

- Build corpus: MIR features on all existing `.mod` examples + their AQ seeds
- Train lightweight regressor (random forest / MLP) to predict zone/gate/current
- Save model `models/mir2aq.pkl`; load automatically when `--mir-seed` used
- Invert: feed any audio → predicted AQ → mod that *translates* that audio's structure

Status: ⬜ planned (v0.6.1/v0.7.0)

---

## Phase 7 — Reverse Transcription & Accompaniment (planned)

### Phase 7a — `--from-audio` pattern synthesis (pending)

- Map RMS onset peaks → pattern rows
- Map dominant spectral band per peak → channel assignment (0–5)
- Map band energy → note velocity; band centre frequency → period
- Output: 32‑row, 6‑channel transcription of the input's transient structure

### Phase 7b — Accompaniment / Counterpoint (pending)

- `--accompaniment FILE` → generate a second module that *fills* spectral gaps
- Use the input's FFT profile to mask frequency bands; write complementary material

Status: ⬜ planned

## Phase 6 — Just Intonation Mode (complete)

When generating triad motifs, the default tuning uses equal temperament (each
semitone = 2^(1/12) ratio). With `--just-intonation`, the third and fifth
are tuned to pure small-integer ratios:

| Chord tone | Major ratio | Minor ratio |
|------------|------------|------------|
| Root       | 1/1        | 1/1        |
| Third      | 5/4        | 6/5        |
| Fifth      | 3/2        | 3/2        |

Implementation: `ModComposer` computes per‑tone periods as
`period = round(root_period / ratio)`, clamped to ≥ 1. Root note retains
equal‑tempered period. The override is stored in `zone_grid` entries and
propagates through `SongBuilder` as well.

**Usage example:**
```bash
# Single triad motif with just-intonation
mod-writer --triad-motif Ptolemaic --just-intonation --rows 64 --output ptolemaic-just.mod

# Full song orchestration
mod-writer --song symphony.json --just-intonation --song-manifest --output symphony-just.mod
```

All existing functionality remains backward compatible — the flag is opt‑in.

Status: ✓ complete (v0.6.0)

---

---

## Phase 3.3 — Real Audio Validation (complete)

Real-audio prediction pipeline implemented and tested on 10 tracks from music
collection (Kimberly Steele, Gregorian Chant, Current 93, Nurse With Wound,
Death's Dynamic Shroud, etc.).

- Script: `eval_real_audio.py` — transcodes via ffmpeg, profiles, predicts AQ
- Results: 9/10 tracks → Zone 6 (Venus), 1 track → Zone 4 (Mercury)
- Artifact: `real_audio_predictions.csv`
- Observation: Predictions cluster near synthetic training mean (~50–58 AQ);
  model lacks discriminative power due to uniform synthetic timbre

Next: expand synthetic dataset to multiple zones, switch to delta prediction
(0-36 gate shift), or curate real-labeled training set.


### 3.4 CLI integration (complete)

The `--classify` and `--classify-dir` flags expose the AQ classifier directly from the
command line, bypassing MOD generation:

- `--classify AUDIO_FILE` — single-track prediction
- `--classify-dir DIRECTORY` — batch walk (respects `--classify-limit`)
- `--classify-format {table,json,csv}` — output representation

The output fields align with the synthetic validation schema: `file`, `predicted_aq`,
`zone`, `duration_s`, `bpm`, `key`, `scale`. Both JSON and CSV formats write to stdout;
the table format is intended for interactive use.

Real-audio validation on a 10-track curated set showed a Zone 6 bias (9/10 tracks),
indicating that the model has not yet learned discriminative features beyond the
uniform zone‑1 synthetic distribution. Future work will diversify training across zones
or switch to predicting a zone-delta (0–36) rather than absolute AQ.

## Phase 4 — Audio Rendering & Spectral Analysis (complete)

The `audio-renderer` skill provides the perception layer: convert binary `.mod`
into linear PCM audio and extract visual/analytic artefacts.

### 4.1 Rendering pipeline

`render_mod_to_wav(mod_path)` → WAV (16‑bit mono, 44.1 kHz)
- Primary backend: `ffmpeg` with `libopenmpt` decoder (confirmed present)
- Fallback: pure‑Python soft synth (`SoftSynth` from `synth.py`) if ffmpeg fails

### 4.2 Spectrogram generation

`generate_spectrogram(wav_path, colormap='viridis', size='800x400')` → PNG
- Filter: `showspectrumpic=scale=log:color=<colormap>:size=<WxH>`
- Validated colormaps on current build: `viridis`, `magma`, `plasma`, `cool`
- Output: `<wav>_spec.png` (single‑frame spectral snapshot)

### 4.3 Live playback

`play_audio(wav_path, player='ffplay')` — system audio sink
Options: `ffplay`, `aplay`, `pw-play`, `mpg123`.

### 4.4 Basic feature extraction

`analyze_wav(wav_path)` → JSON‑serialisable dict:
```json
{
  "duration": 7.78,
  "sample_rate": 48000,
  "n_frames": 373440,
  "rms": 0.0,
  "peak": 0,
  "zero_crossing_rate": 0.0000,
  "path": "/tmp/file.wav"
}
```
Stdlib‑only (`wave`, `array`, `math`); no heavy deps yet.

### 4.5 Manifest aggregation

`--manifest` flag writes `_manifest.json` bundling:
- Track metadata (zone/gate/current, hypersigil flags)
- File paths (`.mod`, `.wav`, `_spec.png`)
- Optional analysis block
- ISO timestamp

### CLI flags

| Flag | Meaning |
|---|---|
| `--render` | Convert generated `.mod` to WAV |
| `--spectrogram` | Also generate PNG spectrogram |
| `--colormap viridis\|magma\|plasma\|cool` | FFmpeg spectrogram palette (default `viridis`) |
| `--spec-size WxH` | Image dimensions, default `800x400` |
| `--play` | Play WAV via system player (implies `--render`) |
| `--player ffplay\|aplay\|pw-play\|mpg123` | Audio backend |
| `--analyze` | Extract basic audio features to `_analysis.json` |
| `--manifest` | Write full `_manifest.json` metadata bundle |

All Phase 4 flags can be combined freely with Phase 2b/3 hypersigil flags.

Examples:
```bash
# Full hypersigil + render + spec + analysis
python -m numogram_audio.mod_writer \
  --zone 3 --gate 6 --current A \
  --syzygy --entropy 0.08 --triangular --aq-seed "WR-3-6" \
  --render --spectrogram --colormap magma --spec-size 960x540 \
  --analyze --manifest \
  --output hypersigil.mod
```

Status: ✓ complete (v0.4.0)

### 4.5 Auditory analysis, verification, and description

`analyze_wav()` now delegates to `audio-renderer/analyzer.py`, a comprehensive
ffmpeg/ffprobe-based analysis pipeline that extracts:

| Metric | Source |
|---|---|
| Duration, sample_rate, bit_depth | `ffprobe` JSON |
| RMS, peak, true‑peak, crest factor | `ffmpeg astats` |
| Integrated loudness (LUFS) | `ffmpeg ebur128` |
| DC offset | `astats.mean` |
| Spectral centroid / roll‑off | `astats` frequency statistics |
| Onset density | `silencedetect` + segment counting |
| Quality flag | clipping detection (`peak_count > 0`), DC offset warning |

The analysis dict is flat, JSON‑serialisable, and embedded in:

* `--analyze` → writes `<wav>_analysis.json`
* `--manifest` → includes `"analysis": {...}` in `_manifest.json`
* `--json` → merges `"analysis": {...}` into the compact TD status file
* `--verify` → exits non‑zero if `quality != "pass"` (clipping/DC offset)
* `--describe` → prints a one‑sentence oracle portrait using zone/gate/current context

Example description:
```
Zone 3::6 (A) renders a loud, saturated harmonic current (frantic staccato; high-frequency dominant). Peak=0.98, LUFS=-8.4, CR=1.42. [quality: WARNING]
```

All flags are compositional and can be combined:
```
--render --spectrogram --analyze --describe --verify --json
```

---

|
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

# Analysis + description + verification + TD ready
python -m numogram_audio.mod_writer \
  --zone 3 --gate 6 --current A \
  --syzygy --entropy 0.08 --triangular \
  --render --spectrogram --colormap plasma \
  --analyze --describe --verify --json \
  --output audit.mod

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


## TouchDesigner integration

### td-watcher.py
A lightweight polling watcher lives in `audio-renderer/td-watcher.py`:

```bash
python3 ~/.hermes/skills/numogram-audio/audio-renderer/td-watcher.py --dir ~/numogram/outputs
```

It scans the directory for the newest `.wav` and `_spectrogram.png`, merges
metadata from the sibling `.json` status file, and writes `td_state.json`.
TouchDesigner can monitor this file with a **File In DAT** (configured to
poll the file, or use a *File Watch* CHOP) and drive:

- **Movie File In TOP** ← `spectrogram` key (PNG path)
- **Audio File In CHOP** ← `wav` key
- **Text TOP** ← `zone`, `gate`, `current` keys

Colors come from `palettes.py::ZONE_COLOR[zone]`.

### Compact JSON output (`--json`)
The `--json` flag emits a small status file next to the `.mod`:

```json
{
  "zone": 3,
  "gate": 6,
  "current": "A",
  "title": "Warp Tune",
  "wav": "/abs/path/output.wav",
  "spectrogram": "/abs/path/output_spec.png",
  "palette": "plasma",
  "timestamp": "2026-04-29T14:32:00"
}
```

This is the source for `td_state.json` when used together with `--json`.

---


## Files

```
mod-writer/
  __init__.py      # __version__ = '0.4.0'
  writer.py        # ModWriter, Pattern (rows 1-64), Sample, binary pack
  utils.py         # square/triangle/noise generators
  mapping.py       # zone/gate/current → music, SYZYGY_PARTNERS, PENTATONIC_ADJACENCY
  cli.py           # argparse entry with all flags (Phase 2/3/4)
  composer.py      # ModComposer high-level API
  plugin.py        # Hermes slash + tool (extended schema)
  SKILL.md         # this document

audio-renderer/  (sibling skill, imported by mod-writer Phase 4)
  __init__.py      # exports render_mod_to_wav, generate_spectrogram, analyze_wav, describe_audio, palettes
  renderer.py      # ffmpeg wrapper + delegates to analyzer for quality metrics
  analyzer.py      # ffmpeg/ffprobe-based analysis pipeline (quality, spectral, onsets)
  synth.py         # Pure‑Python 4‑voice resampling mixer (fallback)
  palettes.py      # Zone colors (CCRU), ANSI FG, TD constants, ZONE_PROMPTS
  SKILL.md         # audio-renderer documentation
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

## Phase 2c — Structural Improvements (v0.5.1)

This phase consolidates the Mod-Writer codebase into a proper Python package, adds packaging metadata, licensing, tests, and comprehensive documentation. Functional core (Phases 1‑4) remains unchanged; this is a hygiene and distribution pass.

### Package restructure
- All modules (`cli.py`, `composer.py`, `writer.py`, `utils.py`, `mapping.py`, `plugin.py`) moved into the `mod_writer/` package directory.
- `git mv` preserved full commit history for each file.
- Root `__init__.py` (old constants) removed; new empty `mod_writer/__init__.py` marks the package namespace.
- Created `tests/` and `data/` directories; `examples/` exists for future `.mod` artifacts.

### Import system and path handling
- Updated intra‑package imports:
  - `cli.py` now uses absolute `mod_writer.*` imports (`mod_writer.writer`, `mod_writer.composer`, etc.).
  - `composer.py` uses relative imports (`.writer`, `.utils`, `.mapping`) for robustness.
- Refactored `sys.path` insertion in `cli.py` to add the **parent** directory of the package, enabling both direct script execution and module invocation.
- Fixed audio‑renderer integration path to correctly locate the sibling `audio-renderer` skill from the nested package (`.., .., audio-renderer`).

### Build system and licensing
- `pyproject.toml` (setuptools backend) declares distribution name `mod-writer`, import name `mod_writer`, and entry point `mod-writer = mod_writer.cli:main`.
- Dual licensing: **MIT** (code), **CC0 1.0 Universal** (data assets in `data/`).
- Added `CREDITS.md` acknowledging lineage (Hermes Agent, Nous Research, CCRU, Protracker community).

### Test suite
- Added `tests/test_triangular_semantics.py` with five unit tests covering triangular pattern length, the 64‑row cap, zero‑padding of unused channels, and overflow handling. All tests import from `mod_writer.composer` and pass under `pytest`.

### Repository layout
```
mod-writer/
├── pyproject.toml
├── .gitignore
├── LICENSE
├── CREDITS.md
├── SKILL.md
├── mod_writer/
│   ├── __init__.py
│   ├── cli.py
│   ├── composer.py
│   ├── writer.py
│   ├── utils.py
│   ├── mapping.py
│   └── plugin.py
├── tests/
│   ├── __init__.py
│   └── test_triangular_semantics.py
├── data/
│   └── canonical_vectors.json
└── examples/
```

### Wiki documentation
Comprehensive wiki created under `docs/wiki/numogram-audio/mod-writer/`:
- **Index** – overview, provenance, navigation
- **Usage** – installation (`pip install -e .`), CLI basics, Python API examples
- **Motif Reference** – table of all `TRIAD_MOTIF_POLICY` entries (root, quality, octave, zone triple, syzygy description)
- **Triangular Semantics** – length formula `T(zone)`, 64‑row cap, syzygy topology link
- **Validation** – `--inspect-motif`, `--validate-motif`, `--validate-all` usage with examples; link to `canonical_vectors.json`
- **Audio Renderer** – Phase 4 integration, rendering pipeline, spectrogram, analysis, manifest, outstanding TODOs
- **Development** – packaging, running tests, contributing guidelines, license details

### Version
Bumped to **0.5.1** (continuing from 0.5.0–triads, pre‑Phase 4 stable).
