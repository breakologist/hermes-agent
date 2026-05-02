#!/usr/bin/env python3
# Phase 4.5 — Real-audio generalisation gap assessment
#
# Workflow
# --------
# 1. Load artist→[paths] mapping from real_curation/ssd_candidate_final.json
# 2. Pick one representative track per artist (largest file, heuristically highest quality)
# 3. If < max_tracks, optionally fill remainder via youtube-dl (TBD)
# 4. Extract MIR features → flatten to 29-dim vector using data_collector._flatten_features
# 5. Predict zones with Phase-4.4 RandomForest
# 6. Save workspace + predictions + gap commentary
#
# Usage:  python phase4_5_real_audio.py  --max-tracks 40

import sys, os, json, argparse, pathlib, random, shutil
from pathlib import Path
from collections import Counter

# ── Paths ────────────────────────────────────────────────────────────────────
_this = Path(__file__).resolve()
_skill_root = _this.parent.parent.parent          # .../mod-writer/
_artifacts = _skill_root / 'mod_writer' / 'classifier' / 'artifacts'

sys.path.insert(0, str(_skill_root))
from mod_writer.mir_profiler import MIRFeatureExtractor
from mod_writer.classifier.data_collector import _flatten_features
import numpy as np
import joblib

# ── Helpers ──────────────────────────────────────────────────────────────────
def _pick_track_per_artist(by_artist: dict[str, list[str]], rng: random.Random,
                          max_per_artist: int = 1, max_total: int = 40) -> list[str]:
    """Randomly select up to `max_per_artist` files per artist (no size stat)."""
    picks = []
    for artist, files in by_artist.items():
        if not files:
            continue
        # Randomly choose without replacement
        chosen = rng.sample(files, k=min(max_per_artist, len(files)))
        picks.extend(chosen)
    if len(picks) > max_total:
        picks = rng.sample(picks, max_total)
    return picks


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='Phase 4.5: real-audio zone prediction from SSD library')
    ap.add_argument('--max-tracks', type=int, default=40, help='Target number of tracks to evaluate')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--outdir', default=str(_artifacts / 'real_audio_run'))
    args = ap.parse_args()

    # 1 Load SSD candidate mapping (pre-built by audit scan)
    map_path = _this.parent / 'real_curation' / 'ssd_candidate_final.json'
    if not map_path.exists():
        sys.exit(f"Candidate map missing; run SSD scan first: {map_path}")

    with open(map_path) as fh:
        by_artist_raw = json.load(fh)   # artist → list of file paths (strings)

    print(f"Artist coverage in SSD map: {len(by_artist_raw)} artists, "
          f"{sum(len(v) for v in by_artist_raw.values())} total files")

    # 2 Select tracks
    rng = random.Random(args.seed)
    selected_paths = _pick_track_per_artist(by_artist_raw, rng, max_per_artist=1, max_total=args.max_tracks)
    print(f"Selected {len(selected_paths)} tracks for evaluation")

    # 3 Workspace
    out = Path(args.outdir)
    if out.exists():
        shutil.rmtree(out)
    (out / 'source_files').mkdir(parents=True)
    (out / 'features').mkdir()
    (out / 'predictions').mkdir()

    manifest_list = []
    for src_str in selected_paths:
        src = Path(src_str)
        dst = out / 'source_files' / f"{src.parent.name} - {src.name}"
        # Ensure dst does not pre-exist (clean slate across runs)
        if dst.exists():
            try: dst.unlink()
            except OSError: pass
        try:
            os.symlink(src, dst)
            link_action = 'symlink'
        except (OSError, NotImplementedError, FileExistsError):
            # Fallback to copy — ensure dst is gone first
            if dst.exists():
                try: dst.unlink()
                except OSError: pass
            try:
                shutil.copy2(src, dst)
                link_action = 'copy'
            except shutil.SameFileError:
                # src and dst already point to same file — just record it
                link_action = 'already'
        manifest_list.append({'original': str(src), 'workspace': str(dst), 'action': link_action})

    with open(out / 'selected_files.json', 'w') as fh:
        json.dump(manifest_list, fh, indent=2)

    # 4 MIR extraction + flatten
    print("\n--- MIR extraction + flatten ---")
    extractor = MIRFeatureExtractor()
    feature_vectors = []
    failures     = []
    success_entries = []   # only those extracted successfully

    for entry in manifest_list:
        src = entry['original']
        label = f"{Path(src).parent.name} / {Path(src).name}"
        try:
            nested = extractor.extract(src)          # dict
            flat   = _flatten_features(nested)      # np.ndarray (29,)
            feature_vectors.append(flat)
            success_entries.append(entry)           # keep aligned with feature_vectors
            print(f"  ✓ {label}")
        except Exception as e:
            failures.append(label)
            print(f"  ✗ {label} — {e}")

    if failures:
        print(f"\nExtraction failures ({len(failures)}):")
        for f in failures:
            print(f"  {f}")

    if not feature_vectors:
        sys.exit("No features extracted — aborting.")

    X = np.stack(feature_vectors)
    np.savez_compressed(out / 'real_audio_X.npz', X=X)
    with open(out / 'feature_names.json', 'w') as fh:
        # Exact order must match _flatten_features constructor
        fh.write(json.dumps([
            'sub_bass','bass','low_mid','mid','high_mid','high',
            'spectral_centroid_hz','spectral_bandwidth_hz','spectral_rolloff','dynamic_complexity',
            'onset_rate_norm','bpm_norm','beat_conf_norm',
            'key_C','key_C#','key_D','key_D#','key_E','key_F','key_F#','key_G','key_G#','key_A','key_A#','key_B',
            'scale_major','scale_minor','scale_unknown',
            'duration_norm'
        ], indent=2))
    print(f"\nFeature matrix: {X.shape}")

    # 5 Predict zones (RF was trained on raw features; no scaler needed)
    import joblib
    rf = joblib.load(_artifacts / 'phase4.4_rf.joblib')
    preds      = rf.predict(X)
    pred_proba = rf.predict_proba(X)

    predictions = []
    for i, entry in enumerate(success_entries):
        predictions.append({
            'track': f"{Path(entry['original']).parent.name} – {Path(entry['original']).name}",
            'predicted_zone': int(preds[i]),
            'probability': {f'zone_{z}': float(pred_proba[i, z-1]) for z in range(1,10)}
        })

    with open(out / 'predictions' / 'real_predictions.json', 'w') as fh:
        json.dump(predictions, fh, indent=2)

    # 6 Summary
    zone_counts = Counter(preds)
    print(f"\nPredicted zone distribution:")
    for z in range(1, 10):
        print(f"  Zone {z}: {zone_counts.get(z,0)} tracks")

    # Load baseline for comparison
    baseline = _artifacts / 'phase4.4_report.json'
    if baseline.exists():
        with open(baseline) as fh:
            base_data = json.load(fh)
        print(f"\nSynthetic baseline RF test accuracy: {base_data['rf_accuracy']:.2%}")
        print(f"Note: real tracks lack ground-truth labels; predictions show model bias.")

    print(f"\nWorkspace: {out}")
    print("Done.")

if __name__ == '__main__':
    main()
