#!/usr/bin/env python3
"""Phase 4.1 — Balanced Multi-Zone Synthetic Dataset.

Runs build_dataset(zones=all, seeds_per_zone=100) to generate
~900 balanced examples across zones 1-9.
Saves to: artifacts/dataset_balanced_900.npz (separate from Phase 3 cache).
"""

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here))

from mod_writer.classifier.data_collector import build_dataset

print("=== Phase 4.1: Multi-Zone Balanced Dataset Generation ===")
output = _here / "mod_writer" / "classifier" / "artifacts" / "dataset_balanced_900.npz"
result = build_dataset(
    output_path=str(output),
    zones="all",             # zones 1-9
    seeds_per_zone=100,      # 100 distinct AQ seeds per zone → 900 total
    aq_range=None,           # use zone-based selection (not legacy single-zone)
)

print(f"\nDone. Generated {len(result['y'])} examples across zones {sorted(set(result['zones']))}")
print(f"X shape: {result['X'].shape}, y shape: {result['y'].shape}, zones shape: {result['zones'].shape}")
print(f"Artifacts saved to: {output}")
print("\nNext: python -m mod_writer.classifier.trainer --data dataset_balanced_900.npz --zone-classifier")
