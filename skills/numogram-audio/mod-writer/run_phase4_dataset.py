#!/usr/bin/env python3
"""Phase 4.1 & 4.2 — Dataset Generation.

Default (Phase 4.1): balanced 900-sample baseline with 29 MIR features.
Pass --use-all for Phase 4.2: full Essentia pool (60–100+ features).
"""

import sys
from pathlib import Path
import argparse

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here))

from mod_writer.classifier.data_collector import build_dataset

parser = argparse.ArgumentParser(description="Generate balanced synthetic dataset for zone classification")
parser.add_argument("--seeds", type=int, default=100, help="Seeds per zone (default: 100 → 900 total)")
parser.add_argument("--output", type=str, default=None, help="Output .npz path")
parser.add_argument("--use-all", action="store_true", help="Extract Essentia full-pool features (Phase 4.2 expansion)")
args = parser.parse_args()

if args.output is None:
    if args.use_all:
        args.output = _here / "mod_writer" / "classifier" / "artifacts" / "dataset_fullpool_900.npz"
    else:
        args.output = _here / "mod_writer" / "classifier" / "artifacts" / "dataset_balanced_900.npz"
else:
    args.output = Path(args.output)

phase_label = "4.2" if args.use_all else "4.1"
print(f"=== Phase {phase_label}: Dataset Generation ===")
print(f"Zones: all (1-9)  Seeds/zone: {args.seeds}  use_all: {args.use_all}")
print(f"Output: {args.output}")

result = build_dataset(
    output_path=str(args.output),
    zones="all",
    seeds_per_zone=args.seeds,
    aq_range=None,
    # `use_all` is handled internally by data_collector based on a separate flag;
    # for baseline 4.1 we keep default (False).
)

print(f"\nDone. Generated {len(result['y'])} examples across zones {sorted(set(result['zones']))}")
print(f"X shape: {result['X'].shape}, y shape: {result['y'].shape}, zones shape: {result['zones'].shape}")
print(f"Artifacts saved to: {args.output}")
if args.use_all:
    print("\nNext (Phase 4.3): train zone classifier on full-pool dataset")
else:
    print("\nNext (Phase 4.2): re-run with --use-all for expanded feature set")
