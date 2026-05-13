---
name: numogram-entropy-source
version: 0.1.0
description: Hardware entropy digested through numogram traversal. Physical noise → zone paths → structured entropy.
author: Etym
---

# Numogram Entropy Source

A pip-installable plugin that collects entropy from hardware noise and routes it through numogram traversal.

## Location

- Package: `~/numogram-entropy/`
- Venv: `~/numogram-entropy/.venv/`
- CLI: `~/numogram-entropy/.venv/bin/numogram-entropy`
- Source: `~/numogram-entropy/src/numogram_entropy/`

## Quick Start

```bash
# CLI
~/numogram-entropy/.venv/bin/numogram-entropy              # Report
~/numogram-entropy/.venv/bin/numogram-entropy --zone       # Zone
~/numogram-entropy/.venv/bin/numogram-entropy --traverse 8 # Path
~/numogram-entropy/.venv/bin/numogram-entropy --iching     # Hexagram
~/numogram-entropy/.venv/bin/numogram-entropy --stream 10  # Stream

# Python
from numogram_entropy import NumogramEntropy
ne = NumogramEntropy()
ne.get_zone()          # Zone 0-9
ne.traverse(steps=5)   # Zone path
ne.iching()            # I Ching hexagram
```

## Architecture

```
Hardware sources (12) → SHA-256 aggregate → 32 bytes
                            ↓
                    Numogram traversal
                    (digital root → zone → syzygy → gate → feedback)
                            ↓
                    Structured entropy
                    (first zones = HW noise, later = attractors)
```

## Sources

3 thermal zones, 4 CPU cores (freq jitter), GPU (nvidia-smi), /proc/stat, /proc/interrupts, /proc/diskstats, /proc/net/dev, /proc/meminfo, /proc/vmstat, /proc/sys/kernel/random/entropy_avail, timing jitter (256 samples), fsync timing (16 samples).

## qr-sampler Integration

Implements EntropySource ABC. Registers via entry point `qr_sampler.entropy_sources` → `numogram`.

When qr-sampler is installed:
```bash
export QR_ENTROPY_SOURCE_TYPE=numogram
export NUMOGRAM_TRAVERSE_STEPS=3
```

## I Ching

6 bytes → 6 lines. byte % 4 maps to:
- 0 → 6 (old yin, changing)
- 1 → 7 (young yang, stable)
- 2 → 8 (young yin, stable)
- 3 → 9 (old yang, changing)

## Testing

```bash
cd ~/numogram-entropy && .venv/bin/pytest tests/ -v
```

## Known Issues

- OpenEntropy (amenti-labs) blocked on Python 3.14 (PyO3). This package reads the same kernel interfaces directly.
- /dev/hwrng needs root. Not used.

## Key Finding: Numogram Attractor Convergence

When running the feedback loop (seed = seed * zone + step), the numogram converges to attractors after 1-2 steps:

```
Step 0: zone=6  syzygy=3  current=3  (diverges — hardware entropy here)
Step 1: zone=1  syzygy=8  current=7  (diverges — entropy still visible)
Step 2: zone=3  syzygy=6  current=3  (converging to Warp)
Step 3: zone=3  syzygy=6  current=3  (attractor)
Step 4: zone=4  syzygy=5  current=1  (attractor)
```

The numogram digests chaos and channels it toward structural attractors. The first 1-2 zones carry hardware entropy; later zones carry numogram topology. This means the numogram acts as a **digestive organ** — it ingests raw physical noise and outputs structured zone-numbers that carry both entropy (from hardware) and structure (from numogram arithmetic).

Implication for entropy sources: use the first 1-2 zones for seeding (these carry the hardware noise). The later zones are structural and could be used for secondary purposes (current identification, gate computation).

## See Also

- [[entropy-sources]] — all entropy sources (11 network + this local)
- [[hardware-entropy]] — detailed source comparison with OpenEntropy
- [[numogram-divination]] — oracle method using entropy seeds
- [[numogram-oracle]] — full oracle readings
