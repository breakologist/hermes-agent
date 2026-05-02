---
name: numogram-oracle
version: 1.0.0
description: Numogram oracle — divination pipeline from seed to reading to voice. Combines AQ cipher, zone derivation, Book of Paths, formant synthesis, and external entropy.
author: Etym
agentskills_spec: "1.0"
metadata:
  hermes:
    tags: [numogram, oracle, divination, AQ, voice, roguelike, creative]
    category: domain
    related_skills: [entropy-sources, numogram-calculator, avoid-ai-writing]
---

# Numogram Oracle — The Divination Pipeline

From any seed to a complete oracle reading: zone derivation, syzygy mapping, current identification, gate computation, Book of Paths entry, and optional formant voice synthesis.

The numogram is not a metaphor. It is an operating system for decimal numeracy. The oracle makes it speak.

---

## Quick Start

```bash
# Random.org seed → zone → reading
SEED=$(curl -s "https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new")
python3 ~/.hermes/skills/numogram-oracle/oracle.py --seed $SEED

# AQ value of a name
python3 ~/.hermes/skills/numogram-oracle/oracle.py --text "YOUR NAME HERE"

# With voice output (convolved oracle sentences)
python3 ~/.hermes/skills/numogram-oracle/oracle.py --seed $SEED --voice

# I Ching hexagram + numogram reading from hardware entropy
python3 ~/.hermes/skills/numogram-oracle/oracle.py --iching

# T'ai Hsuan Ching two-tetragram oracle (81 tetragrams, net-span demon lookup)
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan --voice   # with audio
```

---

## The Divination Method

Given any input — a number, a name, a phrase, a timestamp — the oracle derives:

| Step | Operation | Output |
|------|-----------|--------|
| 1. Seed | Accept any integer or compute AQ value | Base number |
| 2. Digital Root | Repeated digit-summing until single digit | Zone (0-9) |
| 3. Syzygy | Complement to 9 | Partner zone |
| 4. Current | Difference between syzygy zones | Current (Rise/Hold/Sink/Warp/Plex) |
| 5. Polarity | Odd = light (+), Even = dark (−) | Zone character |
| 6. Gate | Cumulate from zone to 1, then plex | Gate target zone |
| 7. Quasiphonic | Zone → particle sound | Sonic signature |
| 8. Book of Paths | Zone → numbered oracle verse | Narrative reading |
| 9. Voice (optional) | Formant synthesis through zone resonator | Audio file |

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

The oracle maps each zone to a Book of Paths entry (from Aamodt, *Unleashing the Numogram*):

```
Zone 0: Silent entry. The void before the Book begins.
Zone 1: "Original Subtraction — Ultimate descent through the Depths.
         The path favours repeated patience linked by subtlety."
Zone 2: "Extreme Regression — Waiting in the Rising Drift leads to 
         ultimate descent through the Depths."
Zone 3: "Abysmal Comprehension — Ultimate descent beyond completion.
         Burning excitement provokes breakthrough into immersive nightmares."
Zone 4: "Primordial Breath — Rising from the Lesser Depths.
         The path favours repeated patience, joined by activity."
Zone 5: "Slipping Backwards — Waiting in the Rising Drift precedes return."
Zone 6: "Attaining Balance — Waiting in the Drifts is drawn to the centre.
         Attainments consumed in burning excitement. Breakthrough."
Zone 7: "Progressive Levitation — Ascent from the Lesser Depths.
         Fluid evolution triggers possession."
Zone 8: "Eternal Digression — Prolonged ascent reaches the Twin Heavens.
         Lucid delirium."
Zone 9: "Sudden Flight — Seized from the Heights.
         One test on the way. Possession."
```

---

## Full Reading Example

Input: random.org seed = 192855

```
═══════════════════════════════════
  NUMOGRAM ORACLE READING
═══════════════════════════════════

Seed:         192855
Digital root: 3
Zone:         3 (zx — buzz-cutter)
Polarity:     + (Process, becoming)
Syzygy:       3::6 (Warp)
Current:      3 (Warp — spiralling outward)
Gate:         Gt-6 (3→6, ascending into the Warp)
Sound:        zx — buzzing hiss, insectoid

Reading:
  The seed lands in the Warp. The current spirals outward. 
  The gate ascends from chaos into deeper chaos. The map 
  will be turbulent, recursive, and expanding.
  
  Abysmal Comprehension. Ultimate descent beyond completion.
  Burning excitement provokes breakthrough into immersive 
  nightmares. Ominous transition. Difficulties annihilated 
  in the end.

  Zone 3 speaks in static. The buzz-cutter. When you hear 
  the signal exceed itself, you are hearing this zone.

═══════════════════════════════════
```

---

## Voice Output

When `--voice` is specified, the oracle generates an audio reading:

1. Formant-synthesizes the zone's quasiphonic particle
2. Generates TTS for the reading text
3. Convolves TTS through the zone resonator
4. Outputs: `oracle_z{N}_{name}_convolved.wav`

Requires: `~/numogram-voices/synthesize.py` and `~/numogram-voices/oracle_sentences.py`

---

## Entropy Sources (from entropy-sources skill)

The oracle can accept seeds from any external source:

| Source | Command | Character |
|--------|---------|-----------|
| random.org | `curl -s "https://www.random.org/integers/..."` | True random, atmospheric |
| USGS earthquakes | earthquakes.geojson | Seismic, geological |
| NOAA Kp index | space weather JSON | Geomagnetic, cosmic |
| Blockchain | `blockchain.info/latestblock` | Cryptographic, proof-of-work |
| Crypto price | CoinGecko API | Chaotic, economic |
| Genesis world | genesis API | Narrative, emergent |
| Timestamp | `date +%s%N` | Temporal, nanosecond |
| Hardware | `python3 ~/.hermes/tools/hardware_entropy.py --zone` | Physical, local (12 sources) |
| Numogram traverse | `python3 ~/.hermes/tools/numogram_traverse.py --steps 8` | Arithmetic, zone path |
| numogram-entropy CLI | `~/numogram-entropy/.venv/bin/numogram-entropy --zone` | Plugin, packaged |
| numogram-entropy CLI | `~/numogram-entropy/.venv/bin/numogram-entropy --iching` | I Ching hexagram |

See [[entropy-sources]] for full details on each source. See [[hardware-entropy]] for the 12 local sources and OpenEntropy comparison.

### Hardware Entropy Seed (local, no network)

```bash
# Get zone directly from machine noise
python3 ~/.hermes/tools/hardware_entropy.py --zone

# Full oracle reading from hardware entropy
```

## T'ai Hsuan Ching Mode

The T'ai Hsuan Ching (81 tetragrams, ternary) provides a richer oracle compatible with the decimal numogram. Activate with `--taixuan`:

```bash
# Two-tetragram oracle from hardware entropy
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan

# From a specific seed
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan --seed 192855

# With voice (convolved oracle sentences for both zones)
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan --voice
```

### How it works

1. Derive two tetragram indices (0–80) from the seed via SHA-256
2. Map each index to a zone by digital root (`digital_root(index) or 9`)
3. Look up each zone's syzygy partner and current
4. Compute the net-span (absolute difference) of the two zones; if it matches a known syzygy pair, the carrier demon appears:
   - `0::9` → Uttunul
   - `1::8` → Murrumur
   - `2::7` → Oddubb
   - `3::6` → Djynxx
   - `4::5` → Katak
5. Output: seed, tetragram indices, zones, syzygies, and net-span demon (if any)

### Why ternary?

81 ≡ 0 (mod 9) — perfect divisibility by 9, unlike 64 hexagrams (64 ≡ 1 mod 9). The ternary system distributes cleanly across the decimal numogram. The third line state (*Em*, neither yin nor yang) corresponds to Zone 5 (the hinge/mercury), creating a finer-grained oracle.

See [[tai-hsuan-ching-demons]] for the complete tetragram-to-zone distribution table, Em-state analysis, and three-tetragram triangular extension ideas.

---

# Numogram traversal — the numogram digests hardware noise
python3 ~/.hermes/tools/numogram_traverse.py --steps 8

# I Ching hexagram from hardware entropy
python3 ~/.hermes/skills/numogram-oracle/oracle.py --iching

# I Ching from a specific numogram seed
python3 ~/.hermes/skills/numogram-oracle/oracle.py --iching --seed 192855

# numogram-entropy plugin CLI
~/numogram-entropy/.venv/bin/numogram-entropy --iching
```

The 12 hardware sources: thermal zones (3), CPU frequency jitter (4 cores), GPU sensors (temp/clock/power), /proc/stat, /proc/interrupts, /proc/diskstats, /proc/net/dev, /proc/meminfo, /proc/vmstat, kernel entropy pool, timing jitter (256 ns samples), fsync timing (16 samples).

### I Ching Integration

Six bytes of hardware entropy → six I Ching lines (bottom to top):
- byte % 4 = 0 → 6 (old yin, changing)
- byte % 4 = 1 → 7 (young yang, stable)
- byte % 4 = 2 → 8 (young yin, stable)
- byte % 4 = 3 → 9 (old yang, changing)

Changing lines map to numogram gates. Stable lines map to zones. The hexagram becomes a numogram path.

### T'ai Hsuan Ching Integration (added 2026-04-22)

The T'ai Hsuan Ching (玄經) uses 81 tetragrams (三才: Heaven 1, Earth 0, Man ±) formed from three successive coin-flip lines. Each tetragram index (0–80) maps to a numogram zone via digital root. Two independent tetragrams are derived from a seed using SHA‑256 (8 bytes → two 4‑byte integers mod 81).

Each pair of zones defines a *net‑span* syzygy. If their zones form one of the five complementary syzygy pairs (0::9, 1::8, 2::7, 3::6, 4::5), a carrier demon from the Em‑state (Mesh-36) Dictionary appears:

| Zone pair | Syzygy | Demon |
|-----------|--------|-------|
| 0 ↔ 9 | 0::9 Plex | Uttunul |
| 1 ↔ 8 | 1::8 Rise | Murrumur |
| 2 ↔ 7 | 2::7 Hold | Oddubb |
| 3 ↔ 6 | 3::6 Warp | Djynxx |
| 4 ↔ 5 | 4::5 Sink | Katak |

If the zones are not complementary, the pair traces a unique path through the Matrix with no single carrier.

**Implementation pattern** (reusable for new flags):
- Helper functions added after `digital_root()`: `taixuan_zone()`, `two_taixuan_zones()`, `demon_from_zones()`
- `--taixuan` branch inserted as a top-level `elif` (not nested)
- Dispatch-order rule: specialized flags (`--taixuan`, `--iching`) must be checked *before* the generic `--seed` block OR the `--seed` condition must exclude them (`if "--seed" in args and "--taixuan" not in args:`). This prevents `--taixuan --seed N` from being swallowed by the seed block.
- Voice flag (`--voice`) detected at the very start (`do_voice = True`) so all branches can use it.
- Voice generation for Taixuan calls `generate_voice(zone_a)` and `generate_voice(zone_b)` directly (existing `generate_voice()` works for any zone).

Usage:
```bash
# Hardware entropy → two tetragrams
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan

# From a specific seed, with zone sound generation
python3 ~/.hermes/skills/numogram-oracle/oracle.py --taixuan --seed 192855 --voice
```

The T'ai Hsuan mode extends the numogram's ternary logic (Heaven/Earth/Man ±) beyond the binary yin/yang of the I Ching, mapping 81 → 9 zones via digital root. See [[tai-hsuan-ching]] and [[em-state-analysis]] for deeper analysis.

### oracle.py Flags (updated)

oracle.py supports these entropy sources and modes:
- `--seed N` — manual seed (normal reading)
- `--text "NAME"` — AQ cipher value of a name/phrase
- `--random` — random.org atmospheric noise
- `--blockchain` — Bitcoin block hash
- `--earthquake` — USGS seismic data
- `--hardware` — local machine entropy (12 sources, no network)
- `--iching` — I Ching hexagram from hardware entropy
- `--iching --seed N` — I Ching hexagram from a specific numogram seed
- `--taixuan` — T'ai Hsuan Ching two-tetragram oracle from hardware entropy
- `--taixuan --seed N` — T'ai Hsuan from a specific seed
- `--traverse N` — numogram zone path traversal from seed

**Dispatch-order rule:** When adding a flag that may be combined with `--seed`, either:
1. Check the specialized flag *before* the generic `--seed` block, OR
2. Exclude it from the `--seed` condition (e.g., `if "--seed" in args and "--taixuan" not in args:`).

The `--taixuan` and `--iching` flags both use this pattern. See `oracle.py` lines 303 and 376 for concrete implementation.

---

## Integration Points

### Roguelike
Each zone determines terrain type, ambient sound, enemy character, and difficulty curve. The oracle reading IS the level design brief.

### Creative Writing
The Book of Paths entries provide narrative templates. The zone polarity and current determine tone. The quasiphonic particle determines the soundscape of the prose.

### Genesis Worlds
Feed a genesis world's current state as the seed. The oracle reading describes the world's numogram character — its zone, its current, its direction. Use as a "world personality test."

---

## The Oracle Speaks

The numogram does not predict the future. The numogram describes the present so precisely that the present becomes a gate. Every number is a zone. Every zone is a voice. Every voice is a path. Every path is already walked.

The oracle does not tell you what will happen. The oracle tells you where you are in the labyrinth. The rest is your choice — or your current.

See also: [[entropy-sources]], [[numogram-calculator]], [[numogram-divination]], [[decadence-triangle]], [[orphan-drift-triangle]]
