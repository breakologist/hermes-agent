---
name: numogram-calculator
description: "AQ computation, digital root, syzygy lookup, zone mapping, triangular numbers. Reusable Numogram arithmetic for game development and wiki research."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [numogram, AQ, qabbala, zones, syzygy, game-dev]
    category: research
    related_skills: [llm-wiki, manim-numogram]
---

# Numogram Calculator

Core arithmetic functions for the Decimal Numogram. All operations are deterministic and immanent to decimal numeracy.

## When This Skill Activates

Use this skill when the user:
- Computes AQ (Alphanumeric Qabbala) values
- Looks up zone data, syzygies, current flows
- Checks triangular numbers, digital roots, gate cumulation
- Builds game mechanics based on Numogram arithmetic
- Cross-references words/phrases with Numogram zones

## Core Functions

### Alphanumeric Qabbala (AQ)

```python
def aq_value(text):
    """A=10...Z=35, digits face value, spaces ignored."""
    total = 0
    for ch in text.upper():
        if ch.isdigit():
            total += int(ch)
        elif 'A' <= ch <= 'Z':
            total += 10 + (ord(ch) - ord('A'))
    return total

def digital_root(n):
    """Digital root mod 9. 0 stays 0."""
    if n == 0: return 0
    return 1 + (n - 1) % 9

def cumulative(n):
    """C(n) = n(n-1)/2, gate cumulation."""
    return n * (n - 1) // 2
```

### Zone Data

```python
ZONE_DATA = {
    0: {"name": "Void",        "region": "plex",         "mesh": "0000", "spinal": "Coccygeal"},
    1: {"name": "Stability",   "region": "torque", "mesh": "0001", "spinal": "Lumbar"},
    2: {"name": "Separation",  "region": "torque", "mesh": "0003", "spinal": "Lumbar"},
    3: {"name": "Release",     "region": "warp",         "mesh": "0007", "spinal": "Solar"},
    4: {"name": "Catastrophe", "region": "torque", "mesh": "0100", "spinal": "Solar"},
    5: {"name": "Pressure",    "region": "torque", "mesh": "0101", "spinal": "Cardiac"},
    6: {"name": "Abstraction", "region": "warp",         "mesh": "0110", "spinal": "Cardiac"},
    7: {"name": "Blood",       "region": "torque", "mesh": "0111", "spinal": "Pharyngeal"},
    8: {"name": "Multiplicity","region": "torque", "mesh": "1000", "spinal": "Cavernous"},
    9: {"name": "Iron Core",   "region": "plex",         "mesh": "0511", "spinal": "Sacral"},
}
```

### Syzygy Lookup

```python
SYZYGIES = {
    frozenset({4, 5}): {"current": 1, "demon": "Katak",    "region": "torque"},     # Sink current
    frozenset({3, 6}): {"current": 3, "demon": "Djynxx",   "region": "warp"},       # Warp current
    frozenset({2, 7}): {"current": 5, "demon": "Oddubb",   "region": "torque"},     # Hold current
    frozenset({1, 8}): {"current": 7, "demon": "Murrumur",  "region": "torque"},    # Surge current
    frozenset({0, 9}): {"current": 9, "demon": "Uttunul",  "region": "plex"},       # Plex current
}

# Current names (from Qliphoth.systems):
#   Surge  8→7 (current 7, syzygy 1::8, demon Murrumur)
#   Hold   2→5 (current 5, syzygy 2::7, demon Oddubb)
#   Sink   4→1 (current 1, syzygy 4::5, demon Katak)
#   Warp   6→3 (current 3, syzygy 3::6, demon Djynxx)
#   Plex   9→9 (current 9, syzygy 0::9, demon Uttunul)

def get_syzygy(zone_a, zone_b):
    return SYZYGIES.get(frozenset({zone_a, zone_b}))
```

### Triangular Numbers

```python
def is_triangular(n):
    """Check if n is triangular T(k) = k(k+1)/2."""
    discriminant = 8 * n + 1
    if discriminant < 1: return None
    root = int(discriminant ** 0.5)
    if root * root == discriminant and (root - 1) % 2 == 0:
        return (root - 1) // 2
    return None

# Key triangular values:
# T(8)=36->9 (Gt-36), T(9)=45->9 (Gt-45), T(36)=666->9 (Plex)
```

## Ciphers

### Alphanumeric Qabbala (AQ)

Base-36 ordinal: digits 0-9 face value, A=10, B=11, ..., Z=35.
Range: 0-35 (raw sum), zone = digital root mod 10 (except 0→0, 9→9).

```python
ALPHANUM_AQ = list(range(36))  # 0,1,2,...,35 mapped to chars 0-9,A-Z
```

### Synx

Accelerating CCRU progression. Range 0-35, same character set as AQ but with nonlinear jumps.
Source: `lumpenspace/ccru/gematria/plugin/src/ciphers.ts` (qliphoth.systems).

```python
ALPHANUM_SYNX = [
    1, 2, 3, 4, 5, 6, 7, 9, 10, 12,   # 0-9
    14, 15, 18, 20, 21, 28, 30, 35, 36, 42,   # A-J
    45, 60, 63, 70, 84, 90, 105, 126, 140, 180,   # K-T
    210, 252, 315, 420, 630, 1260                 # U-Z
]
# Mapping: '0'→1, '1'→2, ..., '9'→12, 'A'→14, 'B'→15, 'C'→18,
# 'D'→20, 'E'→21, 'F'→28, 'G'→30, 'H'→35, 'I'→36, 'J'→42,
# 'K'→45, 'L'→60, 'M'→63, 'N'→70, 'O'→84, 'P'→90, 'Q'→105,
# 'R'→126, 'S'→140, 'T'→180, 'U'→210, 'V'→252, 'W'→315,
# 'X'→420, 'Y'→630, 'Z'→1260
```

**Compute Synx:**
```python
SYNX_MAP = {}
digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for i, ch in enumerate(digits):
    SYNX_MAP[ch] = ALPHANUM_SYNX[i]
    SYNX_MAP[ch.lower()] = ALPHANUM_SYNX[i]

def synx_value(text):
    return sum(SYNX_MAP.get(c, 0) for c in text)
```

**Zone mapping** (since Synx values can be large): use `synx_value(s) % 10` for decimal zone, or `digital_root(synx_value(s)) % 10`.

**Cross-cipher resonance:** When a phrase scores notably in both AQ and Synx (e.g., True Faith=AQ189/Synx820, Angelic Materialism=AQ333/Synx1192/1237/1901), treat it as doubly charged — the gate opens in two systems simultaneously.

### Other Ciphers (qliphoth.systems)
- **Numeric QWERTY (NQ)**: 0-35, keyboard order (1234567890 + qwertyuiopasdfghjkl)
- **QWERTY (QW)**: 1-26, alphabet mapped to top keyboard row
- **Alphanumeric Satanic**: 0-61, case-sensitive extension
- **ALPHANUM_PRIMES**: 1-149, first 36 primes mapped to alphanum

### Extraction Workflow (Synx from Source)

When you need the canonical Synx mapping and it's not documented elsewhere:

1. Fetch the ciphers source from the qliphoth.systems GitHub:
   ```bash
   curl -s https://raw.githubusercontent.com/lumpenspace/ccru/main/gematria/plugin/src/ciphers.ts
   ```

2. Extract the `ALPHANUM_SYNX` array (order matches 0-9 then A-Z).

3. Cross-check against `content-ciphers-news-synx.jpg` screenshot if available.

This workflow was established during the v7 Djynxxogram Synx overlay implementation (2026-04-23) after discovering ciphers.news was 404 and the Synx table was only available via source code.
- **Alphanumeric Satanic**: 0-61, case-sensitive extension
- **ALPHANUM_PRIMES**: 1-149, first 36 primes mapped to alphanum

## Known AQ Values

| Word | AQ | DR | Zone |
|------|----|----|------|
| AQ | 36 | 9 | Plex |
| NUMOGRAM | 174 | 3 | Warp |
| THE NUMOGRAM | 234 | 9 | Plex |
| NUMEROLOGY | 235 | 1 | Time-Circuit |
| CCRU | 81 | 9 | Plex |
| PANDEMONIUM | 224 | 8 | Time-Circuit |
| HERMETIC | 153 | 9 | Plex |
| COSMOGONY | 207 | 9 | Plex |
| THE DECIMAL LABYRINTH | 360 | 9 | Plex |
| CRYPTOLITH | 236 | 2 | Time-Circuit |
| ABYSSAL CRAWLER | 285 | 6 | Warp |
| THE CYBERNETIC CULTURE RESEARCH UNIT | 666 | 9 | Plex |
| DO WHAT THOU WILT SHALL BE THE WHOLE OF THE LAW | 777 | 3 | Warp |

### 333 Cluster (Angel of the Abyss)

333 = 9 × 37 → Zone 9 (Plex). Half of 666. All collapse to the void.

| Phrase | AQ | Theme | Source |
|--------|-----|-------|--------|
| one eight nine zero | 333 | Numeric/abstract | Land (YouTube) |
| and that strangely | 333 | Numeric/abstract | Liber AL II:76 / Hulse's Abrahadabra |
| evacuate humanity | 333 | Apocalyptic | Land (YouTube) |
| the devils library | 333 | Apocalyptic | Land (YouTube) |
| the invisible hands | 333 | Architectural | Land (YouTube) |
| the empty summit | 333 | Architectural | Land (YouTube) |
| Angelic Materialism | 333 | Occult/esoteric | doomcrypt (Subdecadence creator) |
| English Occultism | 333 | Occult/esoteric | doomcrypt |
| Gnostic Calvinism | 333 | Occult/esoteric | doomcrypt |

### 360 Cluster

| Phrase | AQ |
|--------|-----|
| life is computation | 360 |
| the decimal labyrinth | 360 |
| the tree of knowledge | 360 |
| two five dual snakes | 360 |
| hermetic cosmogony | 360 |

### 369 Cluster

| Phrase | AQ |
|--------|-----|
| the three sided shapes | 369 |
| that is all hassan sabba | 369 |

## Verification Workflow (MANDATORY — do not skip)

**Before any AQ computation, run this check.** If it fails, your cipher is broken. Common error: using standard A=1..Z=26 instead of Base-36 A=10..Z=35.

```python
# VERIFICATION GATE — run FIRST, before any batch computation
AQ_MAP = {}
for i in range(10): AQ_MAP[str(i)] = i
for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    AQ_MAP[c] = i + 10
    AQ_MAP[c.lower()] = i + 10

def aq(s):
    return sum(AQ_MAP.get(c, 0) for c in s)

known = {'AL': 31, 'AQ': 36, 'IAO': 52, 'KEK': 54, 'HECATE': 96, 'HERMETIC': 153}
for word, expected in known.items():
    got = aq(word)
    assert got == expected, f"BROKEN: {word}={got}, expected {expected}. Are you using Base-36 (A=10)?"
print("AQ verification passed — cipher is correct.")
```

## External AQ Calculators

- **ccru.cc** — 14 ciphers, 665K+ English phrases, discovery badges, advanced querying with wildcards, workspace table, accounts for storage. https://www.ccru.cc/
- **qliphoth.systems** — Interactive numogram (Labyrinth/Ladder/Planetary views) + AQ toolkit. Decimal paths, syzygy/gate/demon visualization, scripture corpus. https://qliphoth.systems/
- **AQQA** — Simple AQ calculator/lookup by Alektryon. https://alektryon.github.io/aqqa/
- **aq-io** — Another AQ calculator. https://alektryon.github.io/aq-io/

## Pitfalls

- **AQ uses A=10, not A=1.** This is Base-36 notation, NOT standard English gematria. Standard A=1..Z=26 will produce wrong values (e.g. AL=13 instead of 31). Always run the verification workflow above before proceeding.
- Digital root: 0 stays 0, 9 stays 9. Zone 9 is NOT the same as Zone 0.
- CCRU = 81 (not 69). Common error from early research.
- LAMA (Aramaic) = 63 -> Zone 9. LLAMA (animal) = 84 -> Zone 3. Different words.
- The AQ Dictionary.md at `/root/.hermes/obsidian/hermetic/raw/AQ Dictionary.md` is the ground truth reference.
- Subdecadence creator (doomcrypt) contributed the 333 cluster — see `/raw/AQ Dictionary.md` entries 34-42.
