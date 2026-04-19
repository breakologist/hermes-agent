---
name: entropy-sources
version: 2.2.0
description: External entropy sources for procedural generation, seeding, and numogram oracle input. Combines real-world data streams, numogram traversal, and local hardware noise. Now includes I Ching casting and numogram-entropy plugin.
author: Etym
agentskills_spec: "1.0"
---

# Entropy Sources v2 — The Aether Tap

External data streams for seeding procedural generation, roguelike maps, creative experiments, and numogram oracle readings. Every source returns raw data from outside the machine — atmospheric noise, seismic tremors, solar wind, blockchain hashes, cosmic weather.

## Quick Start

```bash
# Get a true random seed
curl -s "https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new"

# Derive numogram zone from seed
python3 -c "seed=192855; zone=sum(int(d) for d in str(seed))%10 or 9; print(f'Zone {zone}')"

# Full oracle reading from seed
python3 ~/numogram-voices/oracle_sentences.py --zone $ZONE
```

---

## Sources

### 1. random.org — Atmospheric Noise
Source: Radio receiver sampling atmospheric electromagnetic noise.
```
curl -s "https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new"
```
Single integer 0-999999. True randomness from the aether.
Free tier: 10,000 bits/day.

### 2. USGS Earthquakes — Seismic Entropy
Source: Real-time earthquake feed (all magnitudes, global).
```
curl -s "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
```
Use: magnitude as intensity modifier, coordinates as spatial seed, timestamp as temporal offset.
The earth itself is the random number generator.

### 3. NOAA Space Weather — Geomagnetic Kp Index
Source: Planetary geomagnetic activity index (0-9).
```
curl -s "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
```
Kp 0-2: quiet. Kp 3-4: unsettled. Kp 5+: storm. Kp 7+: severe.
Use as "warp influence" — high Kp increases chaos in numogram Zone 3/6.

### 4. NOAA Solar Wind — Interplanetary Magnetic Field
Source: Real-time solar wind Bt (total) and Bz (north-south) components.
```
curl -s "https://services.swpc.noaa.gov/products/solar-wind/mag-2-hour.json"
```
Bz positive: constructive (building). Bz negative: destructive (tearing down).
Use as polarity modifier for oracle readings.

### 5. CoinGecko — Crypto Price Entropy
Source: Real-time cryptocurrency prices (volatile, chaotic).
```
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
```
Use: price last digits as seed. BTC price changes faster than any PRNG.
Combine with timestamp for nanosecond-level uniqueness.

### 6. Blockchain Block Hash — Cryptographic Entropy
Source: Latest Bitcoin block hash (public, verifiable, unpredictable).
```
curl -s "https://blockchain.info/latestblock" | python3 -c "import sys,json; print(json.load(sys.stdin)['hash'])"
```
Use: hex hash as seed. Each block is a proof-of-work — computing this hash required ~10 minutes of global computation. Maximum entropy per second.

### 7. DNS Entropy — Network Noise
Source: Random DNS queries against public resolvers.
```
dig +short $(head -c 8 /dev/urandom | xxd -p).entropy.dns.google @8.8.8.8
```
Use: response latency, NXDOMAIN patterns, or response content as seed material.
The network itself is noisy.

### 8. System State Hash — Machine Entropy
Source: Combined system metrics (uptime, memory, CPU, load average).
```
python3 -c "import hashlib,time,os; h=hashlib.sha256(f'{time.time()}{os.getloadavg()}{os.popen(\"free\").read()}'.encode()).hexdigest()[:8]; print(int(h,16))"
```
Use: unique per moment per machine. Not truly random but highly variable.

### 9. Genesis World State — Narrative Entropy
Source: Current state of a running hermes-genesis world.
```
curl -s http://localhost:8003/api/worlds/{world_id}/events | python3 -c "
import sys,json
events=json.load(sys.stdin)
seed=sum(hash(str(e)) for e in events[-5:]) % 1000000
print(seed)
"
```
Use: the world's history as entropy. Narrative events are unpredictable because they emerge from LLM generation. The world's story becomes the seed for the next thing.

### 10. Numogram Traversal — Arithmetic Entropy
Source: Walk the numogram from any seed and collect the zone path.
```
python3 -c "
seed = 192855
zones = []
n = seed
for _ in range(10):
    zone = sum(int(d) for d in str(n)) % 10 or 9
    zones.append(zone)
    n = n * zone + 1  # feed back
print('Zone path:', zones)
print('Seed stream:', ''.join(str(z) for z in zones))
"
```
Use: the numogram digests the seed and produces a stream of zone numbers. Each step is deterministic but non-obvious. The path IS the entropy.

### 11. Hardware Entropy — Local Machine Noise
Source: Your own machine's physical state — thermal sensors, CPU timing jitter, GPU sensors, memory pressure, disk I/O, network counters.
```
python3 ~/.hermes/tools/hardware_entropy.py              # Full report + 32 bytes
python3 ~/.hermes/tools/hardware_entropy.py --zone       # Numogram zone from entropy
python3 ~/.hermes/tools/hardware_entropy.py --stream 10  # Continuous stream
python3 ~/.hermes/tools/numogram_traverse.py --steps 8   # Numogram traversal from HW noise
```
9 sources: 3 thermal zones, 4 CPU cores (freq jitter), GPU (temp/clock/power via nvidia-smi), /proc/stat, /proc/interrupts, diskstats, network counters, meminfo, timing jitter (256 nanosecond samples).
No network, no API keys, no root. Uses SHA-256 aggregation.
Numogram traversal: hardware noise → zone path. First 1-2 zones diverge (true entropy), later zones converge to numogram attractors (3::6 Warp).
NOTE: OpenEntropy (amenti-labs, 63 sources) reads the same /sys and /proc files but is blocked on Python 3.14 (PyO3 maxes at 3.13). Our direct approach works identically. See [[hardware-entropy]] for full source comparison.
I Ching casting from hardware entropy: zones 4 (Sink/Closure) and 6 (Warp) dominate. Average 3.3 changing lines. Use `python3 oracle.py --iching`.

---

## Combining Sources

### XOR Stack (maximum entropy)
```bash
R1=$(curl -s "https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new")
R2=$(curl -s "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['features']))")
R3=$(curl -s "https://blockchain.info/latestblock" | python3 -c "import sys,json; h=json.load(sys.stdin)['hash']; print(int(h[:8],16))")
SEED=$((R1 ^ R2 ^ R3))
echo "Combined seed: $SEED"
```

### Zone Derivation
```bash
# Any seed → numogram zone
ZONE=$(python3 -c "s=$SEED; print(sum(int(d) for d in str(s)) % 10 or 9)")
echo "Zone: $ZONE"

# Full numogram path
python3 -c "
seed = $SEED
dr = sum(int(d) for d in str(seed))
while dr >= 10:
    dr = sum(int(d) for d in str(dr))
zone = dr or 9
syzygy = 9 - zone
current = abs(zone - syzygy)
gate = sum(range(zone+1))
while gate >= 10:
    gate = sum(int(d) for d in str(gate))
print(f'Seed: {seed}')
print(f'Digital root: {dr}')
print(f'Zone: {zone}')
print(f'Syzygy partner: {syzygy}')
print(f'Current: {current}')
print(f'Gate target: {gate}')
"
```

---

## Application Patterns

### Roguelike Map Seed
```bash
SEED=$(curl -s "https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new")
ZONE=$(python3 -c "print(sum(int(d) for d in str($SEED)) % 10 or 9)")
echo "Map seed $SEED, primary zone $ZONE"
# Feed SEED to procedural generation, ZONE determines terrain type
```

### Oracle Reading Seed
```bash
SEED=$(curl -s "https://blockchain.info/latestblock" | python3 -c "import sys,json; print(int(json.load(sys.stdin)['hash'][:8],16))")
ZONE=$(python3 -c "print(sum(int(d) for d in str($SEED)) % 10 or 9)")
echo "Oracle seed from block hash: $SEED → Zone $ZONE"
# Feed to numogram-oracle skill for full reading
```

### Creative Writing Seed
```bash
SEED=$(date +%s%N)  # nanosecond timestamp
KP=$(curl -s "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json" | python3 -c "import sys,json; print(json.load(sys.stdin)[-1][1])")
# Use Kp index as "warp influence" on the writing's tone
echo "Timestamp: $SEED, Warp influence: $KP"
```

See also: [[numogram-oracle]], [[numogram-calculator]], [[numogram-divination]]
