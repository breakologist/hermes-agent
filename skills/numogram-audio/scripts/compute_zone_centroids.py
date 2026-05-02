#!/usr/bin/env python3
"""
Compute per‑zone MIR centroids from the Phase 4 synthetic 900‑track corpus.

Input: ~/numogram/mod_writer_artifacts/synthetic_900_balanced.jsonl
  Each line: {"zone": N, "mod_file": "...", "features": {...}}

Output: ~/numogram/mod_writer_artifacts/zone_centroids.json
  {"N": {"centroid_mean":…, "centroid_std":…, "bpm_mean":…, "density_mean":…}}
"""
import argparse, json, os, statistics
from typing import Dict, List

DEFAULT_IN = os.path.expanduser('~/numogram/mod_writer_artifacts/synthetic_900_balanced.jsonl')
DEFAULT_OUT = os.path.expanduser('~/numogram/mod_writer_artifacts/zone_centroids.json')

def load_lines(path: str) -> List[Dict]:
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

def extract_feature(rec: Dict, key: str) -> float:
    features = rec.get("features", {})
    return features.get(key, None)

def main():
    parser = argparse.ArgumentParser(description="Zone centroid computation")
    parser.add_argument('--input', default=DEFAULT_IN)
    parser.add_argument('--output', default=DEFAULT_OUT)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: input not found — {args.input}")
        print("Phase 4 corpus must be generated first by mod-writer batch export.")
        return 1

    records = load_lines(args.input)
    by_zone: Dict[int, List[Dict]] = {}
    for r in records:
        zone = r.get("zone")
        if zone is None:
            continue
        by_zone.setdefault(zone, []).append(r)

    centroids: Dict[str, Dict] = {}
    for zone, items in sorted(by_zone.items()):
        # Spectral centroid (Hz) — ESSENTIA average per track
        cents = [extract_feature(r, "spectral_centroid_mean") for r in items]
        cents = [c for c in cents if c is not None]
        # BPM (if stored as rough estimate)
        bpms  = [extract_feature(r, "bpm") for r in items]
        bpms  = [b for b in bpms if b is not None]
        # Density = (note cells) / (rows * channels)
        dens  = [extract_feature(r, "density") for r in items]
        dens  = [d for d in dens if d is not None]

        centroids[str(zone)] = {
            "centroid_mean": round(statistics.mean(cents), 1) if cents else None,
            "centroid_std":  round(statistics.stdev(cents), 1) if len(cents) > 1 else 0.0,
            "bpm_mean":      round(statistics.mean(bpms), 1) if bpms else None,
            "bpm_std":       round(statistics.stdev(bpms), 1) if len(bpms) > 1 else 0.0,
            "density_mean":  round(statistics.mean(dens), 3) if dens else None,
            "density_std":   round(statistics.stdev(dens), 3) if len(dens) > 1 else 0.0,
            "track_count":   len(items),
        }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(centroids, f, indent=2)
    print(f"Centroids written: {args.output}  ({len(centroids)} zones)")
    # Print summary
    for z in sorted(int(k) for k in centroids):
        d = centroids[str(z)]
        print(f"  zone {z}: centroid={d['centroid_mean']} Hz  bpm≈{d['bpm_mean']}  dens={d['density_mean']}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
