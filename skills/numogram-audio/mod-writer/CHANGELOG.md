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
