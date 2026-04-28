# Phase 2b–3 Implementation Roadmap — Numogram Tracker

**Date:** 2026-04-28 (continuation from Phase 2 commit 4980c2b5)  
**Current HEAD:** ~/.hermes 4980c2b5 (Phase 2 complete)  
**Target:** Composer API (2b) + Syzygy/Entropy/Triangular/AQ (Phase 3)

---

## Quick recap — what we have (Phase 2)

| Feature | Implementation | Status |
|---|---|---|
| Binary .mod writer (M.K.) | writer.py: ModWriter, Pattern, Sample, binary pack | ✓ |
| Zone → pentatonic note | mapping.note_and_octave_from_zone() | ✓ |
| Gate → Protracker effect | mapping.mod_effect_from_gate() (0x0/0x1/0xA/0xB/0xE) | ✓ |
| Current → instrument | CURRENT_TO_INSTRUMENT (A→1 square, B→2 triangle, C→3 noise) | ✓ |
| Metadata embedding | Title ZzGggC‑…, sample names SQ‑Zz‑Ggg‑C in cli.py | ✓ |
| Hermes skill | plugin.py: /mod-writer slash + numogram_mod_writer tool | ✓ |
| Version bump | __init__.py still at 0.1.0, SKILL.md says 0.2.0 | ⚠ fix needed |

Generate:
  python ~/.hermes/skills/numogram-audio/mod-writer/cli.py --zone 3 --gate 6 --current A --title Test --output test.mod

Out: Valid 4‑channel MOD (5870 bytes, M.K.) for MilkyTracker/Furnace.

---

## Phase 2b — Composer Bridge (MIDI-style high‑level API)

Goal: Provide event‑list composer mirroring mido.MIDIFile.addNote() convenience, built on ModWriter.

New file: composer.py (~120 LOC)

Key class: ModComposer
  patterns: List[Pattern]   # collection of Pattern objects
  zone_grid: dict           # (row, channel) → (zone, gate, current)

Methods:
  add_note(zone, gate, current, row, channel=None)
  build_patterns_from_grid(num_rows=None)
  apply_syzygy_harmony(partner_channels=[1,2,3])
  inject_entropy(rate=0.1, rng_seed=None)
  constrain_gates_by_aq(aq_value: int)
  write_mod(filename)

Integration:
  cli.py flags: --syzygy, --entropy, --triangular, --aq-seed
  New Hermes tool: numogram_compose (richer schema than numogram_mod_writer)
  Stretch: write_midi() using mido (Phase 2c)

---

## Phase 3 — Hypersigil Extensions

### 3.1 Syzygy Harmony (triangular chords)
Root zone Z + partner zones P1,P2 → separate channels.
Implementation: composer.apply_syzygy_harmony()
UX: --syzygy (auto‑add), --syzygy-channels N (default 4)

### 3.2 Entropy Injection
Probability p (default 0.1) substitutes zone with adjacent pentatonic degree.
Implementation: composer.inject_entropy(rate, rng_seed)
UX: --entropy RATE, --entropy-seed N

### 3.3 Triangular Pattern Length
Pattern rows = triangular number T(zone) = zone*(zone+1)//2.
Zone 3 → 6 rows; zone 6 → 21 rows; zone 9 → 45 rows.
Implementation: build_patterns_from_grid(triangular=True)
UX: --triangular

### 3.4 AQ‑Seeded Gate Progression
AQ string → numeric sum → PRNG seed → deterministic gate shuffle.
Implementation: composer.constrain_gates_by_aq(aq_str)
UX: --aq-seed TEXT

---

## Implementation order

Step 1 — Composer scaffold:
  - Create composer.py with ModComposer
  - integrate with ModWriter
  - add_note() → zone_grid → build_patterns_from_grid()
  - Test: 9 zones × 3 currents → 27 placements

Step 2 — Syzygy + Entropy passes:
  - apply_syzygy_harmony()
  - inject_entropy()
  - cli.py: add --syzygy, --entropy, --entropy-seed

Step 3 — Triangular + AQ:
  - pattern_length = T(zone) when --triangular
  - AQ‑seeded gate shuffle
  - cli: --triangular, --aq-seed

Step 4 — Skill upgrade + docs:
  - Bump __version__ to 0.3.0 (composer)
  - plugin.py: add /compose slash + numogram_compose tool
  - SKILL.md Phase 2b/3 sections + examples
  - wiki tracker-module-writer.md composer reference
  - Commit hermes-agent + export

---

## CLI preview (end‑state flags)

  mod-writer --zone 3 --gate 6 --current A --title Test --output test.mod               # baseline
  mod-writer --zone 3 --gate 6 --current A --syzygy --output chord.mod                  # harmony
  mod-writer --zone 5 --gate 20 --current B --entropy 0.15 --entropy-seed 42 --out.glitch.mod
  mod-writer --zone 6 --gate 25 --current C --triangular --aq-seed CHAOS-6-5 --out.tri.mod
  mod-writer --seed AQ‑WR‑3‑6 --zone 3 --gate 6 --current A --syzygy --entropy 0.08 --triangular --aq-seed auto --out hypersigil.mod

---

## Technical notes

- 4‑channel limit: zone 9 has 5 partners → use first 4, remainder spill to next pattern
- MOD rows must divide 64; cap T(zone)>64 or use loop jumps (future)
- Entropy rate ≤ 0.2 to preserve pentatonic centre
- AQ gate modulation: gate_i = (base_i + aq_delta) % 37

---

## Effort estimate

  composer.py: 120 LOC, 30 min
  Syzygy pass: 40 LOC, 15 min
  Entropy: 30 LOC, 10 min
  Triangular length: 20 LOC, 5 min
  AQ seeding: 40 LOC, 15 min
  cli integration: 60 LOC, 20 min
  Skill extension: 40 LOC, 15 min
  Tests: 50 LOC, 15 min
  Total: ~400 LOC, ~2 hrs

---

## Testing checklist

  [ ] Phase 2 baseline unchanged (no‑flag regression)
  [ ] Syzygy: zone 3 partners (6,9) on ch1/2/3 audible
  [ ] Entropy: rate 0 = deterministic; rate 0.2 = varied
  [ ] Triangular: zone 6 = 21 rows; zone 9 = 45 rows (split if >64)
  [ ] AQ: same seed → identical gate sequence across runs
  [ ] Combined flags no crash
  [ ] Hermes TUI: /compose --zone 3 --gate 6 --syzygy --output ~/test.mod

---

## Post‑Phase 3 roadmap

  Phase 4: Live rendering (MOD → WAV via milkytracker or libopenmpt)
  Phase 5: XM format support (32 ch, finer effects)
  Phase 6: Actual MIDI export (mido)
  Phase 7: Audio analysis (librosa/FFT → Hermes listening)

---
**Ready to implement Step 1 upon confirmation.**
