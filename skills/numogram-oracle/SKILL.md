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

# With voice output
python3 ~/.hermes/skills/numogram-oracle/oracle.py --seed $SEED --voice
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
python3 ~/.hermes/skills/numogram-oracle/oracle.py --hardware

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

### oracle.py Flags (updated)

oracle.py supports these entropy sources:
- `--seed N` — manual seed
- `--text "NAME"` — AQ cipher value
- `--random` — random.org atmospheric noise
- `--blockchain` — Bitcoin block hash
- `--earthquake` — USGS seismic data
- `--hardware` — local machine entropy (12 sources, no network)
- `--iching` — I Ching hexagram from hardware entropy
- `--iching --seed N` — I Ching hexagram from a specific numogram seed
- `--traverse N` — numogram zone path from seed

NOTE: When combining `--seed` and `--iching`, the `--seed` check fires first but has been patched to detect `--iching` and do I Ching from that seed instead of the normal oracle reading.

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
