# Numogram Oracle — Divination Pipeline

**Seed → Zone → Syzygy → Current → Gate → Book of Paths → Voice**

The oracle is a complete divination system for the Decimal Numogram (CCRU, Nick Land). Given any input — number, name, entropy source, or I Ching/T'ai Hsuan casting — it computes a zone path, reads the current, opens the gate, and (optionally) generates audio via physical modelling synthesis.

This README documents the **current state** of `oracle.py` as of 2026-04-22.

---

## Quick Start

```bash
# Basic: single-seed reading
python3 ~/.hermes/skills/numogram-oracle/oracle.py --seed 192855

# Text → AQ value → reading
python3 ~/.hermes/skills/numogram-oracle/oracle.py --text "YOUR NAME"

# With voice (convolved oracle sentences)
python3 ~/.hermes/skills/numogram-oracle/oracle.py --seed 192855 --voice

# Hardware entropy (local /dev/urandom)
python3 ~/.hermes/skills/numogram-oracle/oracle.py --hardware

# External entropy sources
python3 ~/.hermes/skills/numogram-oracle/oracle.py --random      # random.org
python3 ~/.hermes/skills/numogram-oracle/oracle.py --blockchain  # latest Bitcoin block
python3 ~/.hermes/skills/numogram-oracle/oracle.py --earthquake  # USGS latest quake

# I Ching hexagram + numogram reading
python3 ~/.hermes/skills/numogram-oracle/oracle.py --iching
python3 ~/.hermes/skills/numogram-oracle/oracle.py --iching --seed 192855

# T'ai Hsuan Ching (ternary oracle) — NEW
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan --voice   # with audio
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan --seed 192855

# Full traversal (step-by-step zone path)
python3 ~/.hermes/skills/numogram-oracle/oracle.py --traverse 192855
```

---

## What the Oracle Does

| Step | Operation | Output |
|------|-----------|--------|
| 1. Seed | Accept integer, compute AQ from text, or fetch from entropy source | Base number |
| 2. Digital Root | Repeated digit-sum until single digit | Zone 0–9 |
| 3. Syzygy | Complement to 9 | Partner zone |
| 4. Current | `abs(zone - partner)` | Rise / Hold / Sink / Warp / Plex |
| 5. Polarity | Odd = +, Even = − | Zone character |
| 6. Gate | Cumulative plex from zone down to 1 → digit-sum | Gate number (Gt-N) |
| 7. Quasiphonic | Zone → CCRU particle sound | Sonic signature (e.g. `zx`, `mnm`) |
| 8. Book of Paths | Zone → Aamodt's 84-path oracle verse | Narrative reading |
| 9. Voice (optional) | Formant synthesis through zone resonator | Convolved `.wav` file |

---

## Modes

### Basic Modes

- `--seed N` — Manual seed
- `--text "STRING"` — Compute AQ value of a name/phrase
- `--hardware` — Local entropy (`/dev/urandom` via `hardware_entropy.py`)
- `--random` — random.org API
- `--blockchain` — Latest Bitcoin block hash
- `--earthquake` — Latest USGS earthquake data

### I Ching Mode

`--iching` performs a full I Ching hexagram cast from hardware entropy (6 bytes → 6 lines) and then maps the resulting hexagram number (1–64) through the numogram to a zone, syzygy, and gate. Changing lines trigger hexagram transformation commentary.

```
python3 oracle.py --iching                # hardware entropy
python3 oracle.py --iching --seed 12345   # deterministic from seed
```

### T'ai Hsuan Ching Mode — NEW (v2026-04-22)

`--taixuan` implements the 81-tetragram ternary oracle. It produces **two tetragram indices** (0–80) from the seed via SHA-256, maps each to a zone by digital root, and performs a **net-span demon lookup** across the Pandemonium Matrix.

```bash
python3 oracle.py --taixuan            # hardware entropy
python3 oracle.py --taixuan --seed N   # specific seed
python3 oracle.py --taixuan --voice   # with oracle sentence audio
```

**Algorithm:**

1. `seed` → SHA-256 → 32 bytes
2. First 4 bytes → `a_idx = int % 81`; next 4 bytes → `b_idx = int % 81`
3. `zone_a = digital_root(a_idx) or 9`; `zone_b = digital_root(b_idx) or 9`
4. Look up each zone's syzygy partner and current
5. `net_span = abs(zone_a - zone_b)`; if this value forms a known syzygy pair (0::9, 1::8, 2::7, 3::6, 4::5), the **carrier demon** appears:
   - 0 or 9 → **Uttunul** (Plex)
   - 1 or 8 → **Murrumur** (Rise)
   - 2 or 7 → **Oddubb** (Hold)
   - 3 or 6 → **Djynxx** (Warp)
   - 4 or 5 → **Katak** (Sink)
6. Output: seed, both tetragram indices, both zones, both syzygies, net-span demon (or "No direct syzygy")

**Why ternary?** 81 ≡ 0 (mod 9) distributes perfectly across 9 zones; 64 hexagrams ≡ 1 mod 9 leaves a remainder. The third line state (*Em*, neither yin nor yang) maps to Zone 5 (the hinge), giving richer granularity: 6,561 possible two-tetragram readings vs 4,096 for hexagrams.

See `wiki/tai-hsuan-ching-demons.md` for the full 81-tetragram distribution table, Em-state analysis, and three-tetragram triangular extension ideas.

### Voice Output

When `--voice` is specified, the oracle generates **convolved oracle sentences** — formant-synthesized speech passed through the zone's physical-model resonator.

**What gets produced:**

- `oracle_sentence_z{N}_{name}_convolved.wav` — Full sentence convolved through resonator
- `oracle_sentence_z{N}_{name}_sidechain.wav` — Alternative sidechain mix

**For T'ai Hsuan mode:** both zones' oracle sentences are generated in one call to `oracle_sentences.py --zones A B`.

**Requirements:** `~/numogram-voices/synthesize.py` and `~/numogram-voices/oracle_sentences.py` (formant synthesis engine with 30+ phonemes, zone-tuned pitch/scale/breath parameters, Karplus-Strong/modal/plate resonators).

See `skills/numogram-oracle-voice/SKILL.md` for the full voice architecture.

### Traversal

`--traverse N` prints the full zone-by-zone path that seed `N` follows through the numogram (useful for understanding long-term current behaviour).

---

## Zone Quick Reference

| Zone | Particle | Polarity | Current | Region | Description |
|------|----------|----------|---------|--------|-------------|
| 0 | eiaoung | − | Plex | Plex | Void whisper, silence before the word |
| 1 | gl | + | Sink | Time-Circuit | Gulp, glottal spasm, beginnings |
| 2 | dt | − | Hold | Time-Circuit | Stuttering, boundaries breaking |
| 3 | zx | + | Warp | Warp | Buzz-cutter, static, chaos |
| 4 | skr | − | Sink | Time-Circuit | Growl, reptilian, ancient |
| 5 | ktt | + | Hold | Time-Circuit | Hiss, pressure, spittle |
| 6 | tch | − | Warp | Warp | Static, chewing, the sound of eating itself |
| 7 | pb | + | Rise | Time-Circuit | Sigh, lips flapping, ascent |
| 8 | mnm | − | Rise | Time-Circuit | Moan, lullaby, forgetting |
| 9 | tn | + | Plex | Plex | Grunt, pleasure/rage, the gate opens |

---

## The Book of Paths

Each zone maps to one of the 84 paths from *Unleashing the Numogram* (Aamodt):

```
Zone 0  — Silent entry. The void before the Book begins.
Zone 1  — Original Subtraction — Ultimate descent through the Depths.
Zone 2  — Extreme Regression — Waiting in the Rising Drift leads to ultimate descent.
Zone 3  — Abysmal Comprehension — Ultimate descent beyond completion.
Zone 4  — Primordial Breath — Rising from the Lesser Depths.
Zone 5  — Slipping Backwards — Waiting in the Rising Drift precedes return.
Zone 6  — Attaining Balance — Waiting in the Drifts is drawn to the centre.
Zone 7  — Progressive Levitation — Ascent from the Lesser Depths.
Zone 8  — Eternal Digression — Prolonged ascent reaches the Twin Heavens.
Zone 9  — Sudden Flight — Seized from the Heights.
```

The reading combines the zone's path text with the specific seed's computed gate.

---

## File Locations

- **CLI:** `~/.hermes/skills/numogram-oracle/oracle.py`
- **Skill doc:** `~/.hermes/skills/numogram-oracle/SKILL.md`
- **Voice engine:** `~/numogram-voices/` (synthesize.py, oracle_sentences.py, zone resonators)
- **Visualizers:** `~/.hermes/skills/numogram-oracle/numogram-visualizer-v6-full.html` (latest)
- **Wiki:** `~/.hermes/obsidian/hermetic/wiki/` (numogram-divination.md, tai-hsuan-ching-demons.md, numogram-visualizer-v6.md)
- **Goals:** `~/.hermes/goals.md`

---

## Example Output

```
$ python3 oracle.py --taixuan --seed 192855 --voice

══════════════════════════════════════
  T'AI XUAN CHING ORACLE
══════════════════════════════════════

  Seed: 192855
  Tetragrams: 53 (zone 8) and 38 (zone 2)
  Syzygies: 8::1 and 2::7
  No direct syzygy — the pair traces a unique path through the Matrix.

  [Voice] Generating oracle sentences...
  [Voice] → oracle_sentence_z8_mnm_convolved.wav
  [Voice] → oracle_sentence_z2_dt_convolved.wav
══════════════════════════════════════
```

---

## Architecture Notes

- **Dispatch order:** `--seed`, `--text`, `--random`, `--blockchain`, `--earthquake`, `--hardware`, `--iching`, `--taixuan`, `--traverse`. The `--taixuan` branch short-circuits `--seed` when both are present.
- **Voice:** `--voice` sets `do_voice=True` early; branches call `generate_voice(zone)` (raw zone sound) or `oracle_sentences.py` (convolved sentences).
- **T'ai Hsuan helpers:** `taixuan_zone()`, `two_taixuan_zones()`, `demon_from_zones()`, `TAIXUAN_DEMON_MAP`. Defined after `digital_root()`.
- **Syzygy lookup:** `get_syzygy(zone)` returns the complement-to-9 pair; `get_current(zone)` returns the difference.
- **Gate computation:** `plex(n)` sums 1..n then digital-roots; gates follow triangular numbers (T₅=15, T₆=21, T₈=36, T₉=45…).
- **Book of Paths:** `BOOK_OF_PATHS` dict maps zone → title + verse text.

---

## Dependencies

- Python 3.8+ (uses `subprocess`, `hashlib`, no external deps for core)
- Voice generation requires `numpy`, `scipy`, `ffmpeg` (see `numogram-voices/requirements.txt` if present)
- Optional: `edge-tts` (not used — formant synthesis preferred)

---

## Future Enhancement Roadmap

Planned upgrades (not yet implemented):

1. **Triangular syzygy animation** in the HTML visualizer (3-zone triangles)
2. **AQ text input** in browser → live zone preview
3. **T'ai Hsuan mode** as an interactive visualizer overlay (two-tetragram display)
4. **Web Audio playback** of zone sounds directly in the page
5. **Export snapshot** to SVG/PNG
6. **Gate proximity progress bar** along traversal path
7. **Corruption/hypnosis overlay** that tints toward Warp/Plex at high hyperstition
8. **Time-Circuit clock face** with zone hands
9. **Entity inspector** panel (demon, mesh, gates per zone)
10. **Path replay** with play/pause/step controls

Ideas sourced from `numogram-visualizer-v6-full.html`.

---

## Related

- **Skill doc:** `skills/numogram-oracle/SKILL.md` (full usage reference)
- **Voice design:** `skills/numogram-oracle-voice/SKILL.md`
- **Wiki:** `wiki/numogram-divination.md`, `wiki/tai-hsuan-ching-demons.md`, `wiki/numogram-visualizer-v6.md`
- **Entropy sources:** `skills/entropy-sources/` (12 hardware collectors, OpenEntropy)

---

**Status:** Active — core pipeline stable, T'ai Hsuan mode added, voice upgraded to convolved sentences. Visualizer v6 ideas logged for future implementation.
