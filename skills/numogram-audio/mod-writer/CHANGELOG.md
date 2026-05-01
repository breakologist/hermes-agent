# Changelog

All notable changes to mod-writer are documented here.

## [Unreleased]

### Added
- **Phase 5 Full-Track Orchestration** (`song.py`, `cli --song`, `SongBuilder`)
  - Multi-section arrangements via JSON (`--song arrangement.json`)
  - Global tempo flag (`--bpm`)
  - `SongBuilder` API for programmatic composition
  - Pattern caching via `Pattern.clone()`
  - Section-level sample renaming to avoid collision
- **Period table clamping warnings** (`--warn-clamp` on triad motifs)
- `data/canonical_vectors.json` — exhaustive 24-triad root×quality vectors- Just intonation mode (pure-ratio triad tuning) via `--just-intonation`


### Changed
- Package restructuring (`mod_writer/` namespace) — v0.5.1
- `apply_triad_motif` now returns `{'tone_data': [...], 'clamped': {...}}`

### Fixed
- Triangular pattern length cap (max 64 rows) enforced in tests
- Zone=12 invalid; all tests use zones 1-9

## [0.6.4] - 2026-05-01

### Added
**Phase 4.1–4.6: Zone Classifier Pipeline**
- Balanced synthetic dataset generation (900 tracks, zones 1–9) with corrected feature schema
- MLPClassifier baseline (97.22% top-1, 100% top-3)
- RandomForest + SHAP correlation analysis (97.78% accuracy)
  * Top discriminating features: spectral_centroid_hz, spectral_bandwidth_hz, high_mid, high, mid
- Real-audio generalisation study (97-track curated set)
  * Zone 2 emerges (15 tracks): Alva Noto, Björk, Basic Channel, New Order — clean/techno/ambient spectral signature
  * Zone 7 (25 tracks): Autechre, Earth, Boris, Sunn O))) — heavy/drone saturation
  * Zones 3–5, 8–9 absent in general music libraries (hyperstitional pentatonic-only archetypes)
- BPM extraction fallback: `_sane_bpm()` cross-checks `onset_rate_hz`; fixes sparse-onset ambient misestimates
- Mixed retraining (synthetic 720 + real 40, sample_weight=0.5): maintains 97.78% accuracy, 0 label switches
- Comprehensive wiki: `zone_classifier_phase4.5_findings.md` (covers Phases 4.1–4.6 with hyperstitional interpretation)

**Phase 4.7: TouchDesigner Integration**
- Prototype script: `phase4_7_touchdesigner_integration.py` (loads mixed RF, predicts, streams via MCP)
- Design doc: `td_zone_visualizer_reference.md` — audio-reactive GLSL shader, zone colour palette, OP topology
- Quick-start: `PHASE4_7_TD_INTEGRATION.md`

### Fixed
- `_flatten_features()`: corrected MIR schema (flat lowlevel keys, midlevel rhythm/key)
- `load_dataset()`: fixed meta JSON scalar parsing (`.item()`)
- `phase4_6_mixed_retrain.py`: corrected zone labels, path resolution, JSON serialization
- `run_phase4_dataset.py`: removed invalid `use_all` argument

### Documentation
- Exported full documentation suite to `~/numogram` (breakologist/numogram)
- Updated SKILL.md, README.md with Phase 4 capabilities


## [0.6.0] – 2026-04-30

First public-facing release candidate.

### Added
- SongBuilder orchestration layer
- CLI flags: `--song`, `--bpm`
- `Pattern.clone()` for safe copying
- Release documentation (README, CHANGELOG)- Just intonation mode with pure-ratio triad tuning
  - `--song-manifest` flag and `SongBuilder.write_manifest()` integration
  - Seed-pattern extraction: `ModComposer.apply_seed_pattern()` method
  - Test coverage: `tests/test_song_builder.py`, `tests/test_just_intonation.py`
  - Documentation: updated READMEs, wiki pages, usage guide, index
 / Known Gaps
- `--warn-clamp` only implemented for triad-motif path, not zone-seed path
- `SongBuilder.write_manifest()` not auto-called by CLI (`--song-manifest` TODO)
- No per-section Phase 4 pipeline (render/analyze per section)
- Test coverage limited to triangular semantics; need integration tests
- Duplicate pattern-building logic between `cli.py` advanced block and `SongBuilder._populate`
- Pattern row reuse across sections uses deep copy; could memory-pool instead

## [0.5.1] – 2026-04-29

### Added
- Structural improvements: Python package (`mod_writer/`), `pyproject.toml`
- `--inspect-motif` and `--validate-motif` flags
- `--validate-all` (24 canonical triads)
- Comprehensive test suite (`tests/test_triangular_semantics.py`)
- `SKILL.md` Phase 2c documentation

### Technical
- Dual licensing: MIT (code), CC0 (data/outputs)
- Canonical vector generation and validation pipeline

---

*This file follows [Keep a Changelog](https://keepachangelog.com/).*
