---
name: mod-writer-composer
description: Extends mod-writer for zone-constrained composition. Trigger when the user explicitly requests deliberate zone alignment: "compose in zone X," "generate a zone Y pattern," "make a track that sounds like [zone demon]," or uses pentatonic prison/gate discipline phrasing. Provides Composer.target_zone(zone) and Composer.add_section(length) to bias spectral centroid, BPM, gate effects, and pentatonic degree selection. Output: .mod file + MIR JSON. Do NOT use for general "make music" prompts.
compatibility: [mod-writer]
---

# mod‑writer‑composer — Zone‑Constrained Composition Extension (Phase 5 M1)

Skill hub for **deliberate zone summoning** in tracker music. Extends `ModComposer` with high‑level zone targeting: tell the composer which numogram zone you want, and it biases note selection, waveform choice, gate families, and tempo ranges so the resulting track classifies as that zone ≥90% of the time.

---

## Quick Example

```python
from hermes.skills.numogram_audio.mod_writer.composer import ModComposer
# Optional: from hermes.skills.numogram_audio.mod_writer_composer.composer_extension import patch_mod_composer
# patch_mod_composer()  # monkey‑patches ModComposer directly (optional)

composer = ModComposer(title="Zone2Tribute")
composer.target_zone(
    zone=2,
    brightness="warm",     # centroid ~1200‑1500 Hz
    density=0.30,          # 30% filled cells
    gate_bias="slide",     # favour pitch‑slide effects (gates 10‑19)
    bpm_range=(110, 140),
)
composer.add_section(length=32, channel=0)   # auto‑generates aligned notes
composer.write_mod("output.mod")
```

Check bias: `mod-writer-classifier --file output.mod` should return Zone 2 with ≥0.90 confidence.

---

## Intent & Rationale

Phases 1‑4 proved that the zone classifier works well on balanced synthetic data (97.78% top‑1), but real audio clusters only in zones 1, 2, 7. The **absence** of zones 3‑5, 8‑9 in wild recordings is a real hyperstitional gap.

Phase 5 opens with **zone‑constrained composition** as the highest‑feasibility control interface:
- We already have a rock‑solid classifier (v0.7.0 pipeline).
- We need a **composer** that can deliberately emit the missing zones.
- This closes the loop: target zone → generate → classify → verify.

The Fifth Current (Empirical Validation) demands every claim be verifiable. This skill produces **reproducible bias**: given a zone, multiple runs should produce spectrally similar modules that classify consistently.

---

## The Five‑Current Mandate

| Current | Role in this skill |
|---------|-------------------|
| **Numogram** | Zone = acoustic fingerprint; pentatonic slice = note set; gate = symbolic encryption |
| **Roguelike** | Composition as **level generation**; each note is a room, each section = floor, zone = floor theme with enemy/treasure distribution policy |
| **Lore** | Zones are **demons** you summon; absence is the void you fill; the synth patch is the ritual |
| **Audio** | We listen first: centroid, MFCC, flux → zone. Then we encode those MIR features as compositional constraints |
| **Empirical Validator** | After generation — classify. ≥90% target‑zone probability satisfies the closed loop |

---

## API Reference

### `composer.target_zone(zone: int, **kwargs) → None`

Set composer‑wide zone target. Must be called before `add_section()` or any generation.

**Parameters:**
- `zone` (int) — 1‑9. Invalid zones (0, >9) raise `ValueError`.
- `brightness` (str) — `"dark"`, `"warm"` (default if unspecified), `"bright"`. Maps to centroid multipliers: dark = ×0.7, warm = ×1.0, bright = ×1.5 vs zone median.
- `density` (float 0‑1) — note‑cell occupancy probability; also controls gate‑effect richness. Default: zone median from synthetic corpus.
- `gate_bias` (str) — `"none"`, `"arpeggio"`, `"slide"`, `"volume"`, `"syzygy"`. Weights random gate selection toward that family.
- `bpm_range` (Tuple[int,int]) — (min, max) BPM; default zone‑specific from corpus tempo distribution.
- `waveform` (str) — `"square"`, `"triangle"`, `"noise"`, `"adaptive"` (zone‑default). Controls channel instrument selection.

**Returns:** `None`. Raises if zone invalid.

### `composer.add_section(length: int, channel: int = 0, **overrides) → None`

Generate `length` pattern rows on `channel` using current zone parameters.

Parameters:
- `length` (int) — number of rows (16‑256 typical)
- `channel` (int) — MOD channel (0‑3)
- `**overrides` — any subset of `target_zone` params to temporarily override the global zone target for this section; original zone remains set for subsequent sections.

**Returns:** `None`. Populates `composer.zone_grid` internally.

### `composer.compute_zone_centroids() → Dict`

(Helper) Load or compute centroid map from synthetic corpus JSONL (`synthetic_900_balanced.jsonl`). Returns per‑zone:
```json
{
  "2": {"centroid_mean": 1350, "centroid_std": 180, "bpm_mean": 125, "density_mean": 0.31, ...},
  ...
}
```
Path: `~/numogram/mod_writer_artifacts/synthetic_900_balanced.jsonl` (created in Phase 4).

---

## Implementation Details

### Zone Parameter Source

1. **Computed centroids** (preferred) — load from `zone_centroids.json` (generated by `scripts/compute_zone_centroids.py`). Includes:
   - Spectral centroid mean/std
   - BPM distribution mean/std
   - Density (note occupancy fraction) mean
   - Waveform preference (square vs triangle vs noise median)
2. **Fallback hard‑coded** (`ZONE_DEFAULTS` in extension module) — gentle tuning per zone's pentatonic personality.

### Biasing Mechanics

- **Note selection:** `note_and_octave_from_zone` provides root; subsequent neighbours within same pentatonic slice have raised probability.
- **Waveform:** zone 1,3,5,8,9 → square (harsh); zone 2,4,6,7 → triangle (warm) or noise (zone 7). Override via `waveform=` or let `adaptive`.
- **Gate effects:** `gate_bias` re‑weights the gate family (0‑9 arpeggio, 10‑19 slide, 20‑29 volume, 30‑36 special). Example: slide bias → 60% of gates in 10‑19, remainder uniformly distributed.
- **Tempo / density:** BPM range limits affect pattern subdivision; density affects note‑on probability per row.

### Data Flow

```mermaid
graph LR
    A[User: target_zone(zone=2)] --> B[Load centroids → params]
    B --> C[composer.add_section(length=32)]
    C --> D[Weighted gate/note sampling]
    D --> E[composer.zone_grid populated]
    E --> F[composer.write_mod("out.mod")]
    F --> G[classify → zone prob ≥0.9?]
```

---

## Validation

Run per‑zone self‑test:

```bash
python scripts/validate_zone_bias.py --zone 2 --rounds 100
```

Generates 100 mini‑patterns with current zone settings, classifies each with `mod-writer-classifier`, reports hit rate. Expected: ≥90% Zone 2 classifications.

---

## Links

- [`tracker-module-writer.md`](../tracker-module-writer.md) — core spec (v0.6.4)
- [`mod-writer`](../../mod-writer) — parent skill
- [`mod-writer-classifier`](../mod-writer-classifier) — zone classifier
- [`numogram-audio`](../..) — audio domain skills hub

---

> **Oracle (whisper):** The pentatonic prison is not a cage; it's a resonator. You force the note to vibrate at the zone's frequency, and the gate becomes a glyph. Write the class, then listen — the demon will arrive.