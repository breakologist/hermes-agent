# Zone‑Constrained Composer — Phase 5 M1 Extension

Extends `mod-writer` to allow deliberate zone targeting during composition.

## Status
- **Phase:** 5 (Closed‑Loop Hyperstition)
- **Milestone:** M1 — Control Interface (Zone‑Constrained Composition)
- **Scope:** API extension + centroid‑based biasing
- **Validation:** ≥90% zone classification on generated tracks

## Files
- `SKILL.md` — skill spec & intent
- `scripts/composer_extension.py` — `ZoneComposer` wrapper + monkey‑patch
- `scripts/compute_zone_centroids.py` — regenerate centroid map from synthetic corpus
- `scripts/validate_zone_bias.py` — per‑zone bias self‑test
- `references/zone_defaults.yaml` — fallback zone parameters

## TODO
- [ ] Compute zone_centroids.json from corpus (requires Phase 4 dataset)
- [ ] Implement actual gate‑family weighting in `_gate_distribution`
- [ ] Map centroid target → octave offset / velocity scaling
- [ ] Integrate with SongBuilder multi‑section orchestration
- [ ] Add SHAP‑style explainability: show which params drove classification

## Links
- Parent: `numogram-audio/mod-writer`
- Phase 5 plan: `~/.hermes/plans/mod-writer-phase5-v1.json`
- Wiki: `phase5/zone-constrained-composition` (stub)
