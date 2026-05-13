#!/usr/bin/env python3
"""
Compute per‑zone MIR centroids from the Phase 4 synthetic corpus.

Now reads the .npz file directly (dataset_balanced_900.npz) and extracts
spectral centroid and BPM statistics per zone from the feature matrix.

Input: ~/.hermes/skills/numogram-audio/mod-writer/mod_writer/classifier/artifacts/dataset_balanced_900.npz
Output: ~/numogram/mod_writer_artifacts/zone_centroids.json
"""
import argparse, json, os, sys, numpy as np

# Default input: the Phase 4.1 balanced NPZ
DEFAULT_IN = os.path.expanduser(
    '~/.hermes/skills/numogram-audio/mod-writer/mod_writer/classifier/artifacts/dataset_balanced_900.npz'
)
DEFAULT_OUT = os.path.expanduser('~/numogram/mod_writer_artifacts/zone_centroids.json')

# Feature column indices in the 29‑dim vector
COL_SPECTRAL_CENTROID = 6   # Hz
COL_BPM = 11               # scaled: BPM/200
COL_ONSET_RATE = 10        # scaled: onset_rate/200

def main():
    parser = argparse.ArgumentParser(description="Compute zone centroids from synthetic corpus")
    parser.add_argument('--input', default=DEFAULT_IN, help='Input .npz path')
    parser.add_argument('--output', default=DEFAULT_OUT, help='Output JSON path')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: input not found — {args.input}")
        print("Phase 4 corpus must be generated first by run_phase4_dataset.py")
        return 1

    data = np.load(args.input)
    X = data['X']        # (n_samples, 29)
    zones = data['zones']  # (n_samples,) int8
    print(f"Loaded: X{X.shape}, zones{zones.shape}, unique zones={sorted(set(zones))}")

    # Group statistics per zone
    centroids = {}
    for zone in range(1, 10):
        mask = (zones == zone)
        if not np.any(mask):
            print(f"  zone {zone}: no samples")
            continue
        Xz = X[mask]
        # Spectral centroid (Hz) — column 6
        cents = Xz[:, COL_SPECTRAL_CENTROID]
        # BPM — column 11 scaled, multiply back
        bpms = Xz[:, COL_BPM] * 200.0
        # Onset rate → could inform density proxy
        onsets = Xz[:, COL_ONSET_RATE] * 200.0

        c_mean = round(float(np.mean(cents)), 1)
        c_std  = round(float(np.std(cents)), 1) if len(cents) > 1 else 0.0
        b_mean = round(float(np.mean(bpms)), 1)
        b_std  = round(float(np.std(bpms)), 1) if len(bpms) > 1 else 0.0
        o_mean = round(float(np.mean(onsets)), 1)

        centroids[str(zone)] = {
            "centroid_mean": c_mean,
            "centroid_std":  c_std,
            "centroid":      c_mean,          # ZoneComposer legacy key
            "bpm_mean":      b_mean,
            "bpm_std":       b_std,
            "bpm":           (int(max(60, b_mean - 10)), int(min(200, b_mean + 10))),
            "onset_rate_mean": o_mean,
            "track_count":   int(np.sum(mask)),
        }
        d = centroids[str(zone)]
        print(f"  zone {zone}: centroid={d['centroid_mean']}±{d['centroid_std']} Hz  "
              f"bpm≈{d['bpm_mean']}  onset_rate={d['onset_rate_mean']}/s  n={d['track_count']}")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(centroids, f, indent=2)
    print(f"\n✓ zone_centroids.json written: {args.output}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
