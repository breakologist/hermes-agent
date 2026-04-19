---
name: entropy-sources
description: External entropy sources for procedural generation and seeding. Fetches true random data from outside the machine via random.org, USGS, and NOAA.
version: 1.0.0
author: Etym
---

# Entropy Sources Skill

Use when you need random seeds, noise, or entropy from external sources for procedural generation, roguelike maps, or creative seeding. Combines multiple sources for maximum entropy.

## Sources

### 1. random.org (True Random — Atmospheric Noise)
Free, no API key needed. One curl call.
```bash
# Single value
curl -s "https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new"

# Multiple values
curl -s "https://www.random.org/integers/?num=10&min=0&max=999999&col=1&base=10&format=plain&rnd=new"
```

### 2. USGS Earthquakes (Seismic Data)
Free, no key. Real-time feed.
```bash
curl -s "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d['features'][:5]:
    p=f['properties']
    print(f'{p[\"mag\"]} {p[\"place\"]} {p[\"time\"]}')
"
```
Use: magnitude as intensity modifier, coordinates as zone seeds, count as entropy measure.

### 3. NOAA Space Weather (Kp Index — Geomagnetic Activity)
Free, no key. Range 0-9.
```bash
curl -s "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json" | python3 -c "
import sys,json
data=json.load(sys.stdin)
latest=data[-1]
print(f'Kp index: {latest[1]} at {latest[0]}')
"
```
Use: Kp as "warp influence" on numogram zones. High Kp = more chaos.

### 4. NOAA Solar Wind (Bz Polarity)
Free, no key.
```bash
curl -s "https://services.swpc.noaa.gov/products/solar-wind/mag-2-hour.json" | python3 -c "
import sys,json
data=json.load(sys.stdin)
latest=data[-1]
print(f'Bt: {latest[6]} nT, Bz: {latest[3]} nT at {latest[0]}')
"
```
Use: Bz polarity (+/-) as constructive/destructive influence on procedural generation.

## Usage Pattern

1. Fetch from any source
2. Hash/seed-map the value to desired range
3. Use as input to procedural generation

```bash
seed=$(curl -s "https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new")
echo "Seed: $seed"
```

## Combining Sources
For maximum entropy, XOR or combine multiple sources:
```
combined_seed = random_org_value ^ (int(kp_index * 1000)) ^ earthquake_count
```

## Future: SDR Dongle
RTL-SDR v3/v4 (~$30) captures raw RF noise as local entropy source. Can monitor:
- Number stations
- Shortwave noise floor
- FM/AM signal strength variations
- Weather radio (NOAA APT satellites)
