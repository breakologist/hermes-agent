#!/usr/bin/env python3
"""
Validate zone‑bias: generate N mini‑patterns per target zone, classify,
and report pass rate. Expected: ≥90% classified as target.
"""
import argparse, os, sys, statistics
from hermes.skills.numogram_audio.mod_writer.composer import ModComposer
from hermes.skills.numogram_audio.mod_writer_composer.composer_extension import ZoneComposer, patch_mod_composer

def classify_track(mod_path: str) -> int:
    """Placeholder — call the actual classifier CLI and parse zone."""
    # For now: import classifier module if available
    try:
        from hermes.skills.numogram_audio.mod_writer.classifier import classify_mod_file
        zone, probs = classify_mod_file(mod_path)
        return zone
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zone', type=int, required=True, help='Target zone (1-9)')
    parser.add_argument('--rounds', type=int, default=50)
    parser.add_argument('--length', type=int, default=16)
    parser.add_argument('--outdir', default='/tmp/zone_bias_validation')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Apply monkey‑patch so we can call .target_zone directly
    patch_mod_composer()

    hits = 0
    details = []
    for i in range(args.rounds):
        composer = ModComposer(title=f"Z{args.zone}_v{i}")
        composer.target_zone(zone=args.zone, brightness="warm", density=0.3)
        composer.add_section(length=args.length, channel=0)
        mod_path = os.path.join(args.outdir, f"z{args.zone}_{i:03d}.mod")
        composer.write_mod(mod_path)

        pred = classify_track(mod_path)
        ok = (pred == args.zone)
        hits += int(ok)
        details.append({"idx": i, "file": mod_path, "pred": pred, "ok": ok})

    rate = hits / args.rounds
    print(f"Target zone: {args.zone}  →  Hit rate: {hits}/{args.rounds} = {rate:.1%}")
    if rate < 0.9:
        print("⚠  Below 90% threshold — centroid params or classifier may need retraining")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
