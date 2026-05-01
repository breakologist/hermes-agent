#!/usr/bin/env python3
"""
Phase 4.6 — Mixed-Dataset Retraining

Regenerate synthetic dataset (balanced 900), merge with real audio (40),
train RandomForest with sample weighting (synthetic=1.0, real=0.5),
evaluate pre/post on synthetic test set and real set; generate comparison report.
"""

import sys
from pathlib import Path
import json
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

# Paths
SKILL_ROOT = Path(__file__).resolve().parent.parent.parent  # mod-writer/
ARTIFACTS = SKILL_ROOT / "mod_writer" / "classifier" / "artifacts"
SYNTHETIC_PATH = ARTIFACTS / "dataset_balanced_900.npz"
PHASE44_MODEL_PATH = ARTIFACTS / "phase4.4_rf.joblib"
REAL_X_PATH = ARTIFACTS / "real_audio_run" / "real_audio_X.npz"
REAL_PRED_PATH = ARTIFACTS / "real_audio_run" / "predictions" / "real_predictions.json"
OUTPUT_MODEL_PATH = ARTIFACTS / "phase4.6_rf_mixed.joblib"
OUTPUT_REPORT_PATH = ARTIFACTS / "phase4.6_mixed_report.json"

# Hyperparameters matching Phase 4.4 (but without class_weight, using sample_weight instead)
RF_PARAMS = {
    "n_estimators": 500,
    "max_depth": None,
    "min_samples_leaf": 2,   # Phase 4.4 uses min_samples_leaf=2
    "n_jobs": -1,
    "random_state": 42
}

SAMPLE_WEIGHT_SYNTH = 1.0
SAMPLE_WEIGHT_REAL = 0.5

# ─────────────────────────────────────────────────────────────────────────────
def load_synthetic():
    print(f"[phase4.6] Loading synthetic dataset: {SYNTHETIC_PATH}")
    data = np.load(SYNTHETIC_PATH)
    X = data['X']
    y = data['y']
    zones = data['zones']
    print(f"  X shape: {X.shape}, y shape: {y.shape}")
    print(f"  Unique zones: {sorted(set(zones.tolist()))}")
    # Validate zones are 1-9
    assert set(zones) == {1,2,3,4,5,6,7,8,9}, f"Zones should be 1-9, got {set(zones)}"
    # Validate y equals zones (in this dataset, y is the zone label)
    # Actually, check what y represents - from phase4.4, y originally was AQ but they use zones separately
    # In the dataset, y appears to be the zone label (1-9). Let's verify by checking the shape...
    print(f"  y unique: {sorted(set(y.tolist()))}")
    return X, y, zones

def load_real():
    print(f"[phase4.6] Loading real audio features: {REAL_X_PATH}")
    X_real = np.load(REAL_X_PATH)['X']
    print(f"  X_real shape: {X_real.shape}")

    print(f"[phase4.6] Loading real predictions: {REAL_PRED_PATH}")
    with open(REAL_PRED_PATH, 'r') as f:
        real_preds = json.load(f)
    print(f"  Number of predictions: {len(real_preds)}")

    # Extract predicted_zone for each track
    y_real = np.array([p['predicted_zone'] for p in real_preds], dtype=int)
    print(f"  y_real shape: {y_real.shape}")
    print(f"  Real zone distribution: {dict(zip(*np.unique(y_real, return_counts=True)))}")

    assert X_real.shape[0] == len(y_real), "Mismatch: X_real rows != predictions count"

    # Track filenames for alignment sanity check (optional)
    track_names = [p['track'] for p in real_preds]

    return X_real, y_real, track_names

def stratified_split_synthetic(X, y, zones, test_size=0.2, random_state=42):
    """Split synthetic data 80/20 stratified by zones. Returns indices and splits."""
    indices = np.arange(len(X))
    X_train, X_test, y_train, y_test, z_train, z_test, idx_train, idx_test = train_test_split(
        X, y, zones, indices,
        test_size=test_size,
        random_state=random_state,
        stratify=zones
    )
    print(f"[phase4.6] Stratified split: train={len(idx_train)}, test={len(idx_test)}")
    # Verify zone distribution
    for split_name, z in [("train", z_train), ("test", z_test)]:
        uniq, counts = np.unique(z, return_counts=True)
        print(f"  {split_name} zone distribution: {dict(zip(uniq, counts))}")
    return idx_train, idx_test, X_train, X_test, y_train, y_test, z_train, z_test

def evaluate_model(model, X_test, y_test, model_name="Model"):
    """Compute accuracy, confusion matrix, classification report."""
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=sorted(set(y_test)))
    report = classification_report(y_test, y_pred, output_dict=True)
    print(f"[{model_name}] Accuracy: {acc:.4f}")
    print(f"[{model_name}] Classification report (macro avg): "
          f"precision={report['macro avg']['precision']:.4f}, "
          f"recall={report['macro avg']['recall']:.4f}, "
          f"f1={report['macro avg']['f1-score']:.4f}")
    return {
        "accuracy": acc,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "y_pred": y_pred.tolist()
    }

def compute_feature_importance(model, feature_names):
    """Extract Gini importance from RandomForest."""
    importances = model.feature_importances_
    order = np.argsort(importances)[::-1]
    top10 = [
        {"rank": i+1, "feature": feature_names[order[i]], "gini_importance": float(importances[order[i]])}
        for i in range(min(10, len(feature_names)))
    ]
    return top10

def main():
    print("=== Phase 4.6: Mixed-Dataset Retraining ===\n")

    # ── 1. Load synthetic dataset (must be regenerated first) ──────────────────
    X_synth, y_synth, zones_synth = load_synthetic()

    # Load feature names (from meta or reconstruct)
    synth_meta = np.load(SYNTHETIC_PATH, allow_pickle=True).get('meta', {})
    if isinstance(synth_meta, np.ndarray):
        synth_meta = synth_meta.item() if synth_meta.size > 0 else {}
    feature_names = synth_meta.get('feature_names')
    if feature_names is None:
        # Reconstruct from phase4.4 ordering
        bands = ['sub_bass','bass','low_mid','mid','high_mid','high']
        spectral = ['spectral_centroid_hz','spectral_bandwidth_hz','spectral_rolloff','dynamic_complexity']
        rhythm = ['onset_rate_norm','bpm_norm','beat_conf_norm']
        keys  = [f'key_{k}' for k in ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']]
        scales = ['scale_major','scale_minor','scale_unknown']
        meta_f = ['duration_norm']
        feature_names = bands + spectral + rhythm + keys + scales + meta_f
        print(f"[phase4.6] Reconstructed {len(feature_names)} feature names")
    else:
        print(f"[phase4.6] Using {len(feature_names)} stored feature names")

    # ── 2. Split synthetic: 80% train, 20% test (stratified) ──────────────────
    (idx_train, idx_test,
     X_synth_train, X_synth_test,
     y_synth_train, y_synth_test,
     z_synth_train, z_synth_test) = stratified_split_synthetic(
        X_synth, y_synth, zones_synth, test_size=0.2, random_state=42
    )

    # ── 3. Load real audio dataset ───────────────────────────────────────────
    X_real, y_real, track_names = load_real()
    n_real = X_real.shape[0]

    # ── 4. PRE-evaluation: Load Phase 4.4 model and evaluate on synthetic test ──
    print(f"\n[phase4.6] Loading Phase 4.4 model: {PHASE44_MODEL_PATH}")
    rf_phase44 = joblib.load(PHASE44_MODEL_PATH)
    pre_results = evaluate_model(rf_phase44, X_synth_test, z_synth_test, model_name="Phase4.4")

    # Also evaluate Phase 4.4 on real set
    pre_real_results = evaluate_model(rf_phase44, X_real, y_real, model_name="Phase4.4(Real)")
    pre_real_preds = rf_phase44.predict(X_real)

    # ── 5. Build mixed training set ──────────────────────────────────────────
    print(f"\n[phase4.6] Building mixed training set...")
    print(f"  Synthetic train samples: {X_synth_train.shape[0]} (weight={SAMPLE_WEIGHT_SYNTH})")
    print(f"  Real samples: {n_real} (weight={SAMPLE_WEIGHT_REAL})")

    X_mixed = np.vstack([X_synth_train, X_real])
    y_mixed = np.concatenate([y_synth_train, y_real])
    sample_weights = np.array(
        [SAMPLE_WEIGHT_SYNTH] * len(y_synth_train) + [SAMPLE_WEIGHT_REAL] * n_real,
        dtype=float
    )
    print(f"  Mixed X shape: {X_mixed.shape}, y shape: {y_mixed.shape}")
    print(f"  Sample weights: synths={sample_weights[:len(y_synth_train)].mean():.2f}, "
          f"real={sample_weights[len(y_synth_train):].mean():.2f}")

    # ── 6. Train mixed RandomForest ─────────────────────────────────────────
    print(f"\n[phase4.6] Training mixed RandomForest with sample weighting...")
    print(f"  RF params: {RF_PARAMS}")

    # For weighted training, we set class_weight=None to avoid conflict
    rf_mixed = RandomForestClassifier(**RF_PARAMS, class_weight=None)
    rf_mixed.fit(X_mixed, y_mixed, sample_weight=sample_weights)
    print("  Training complete.")

    # Save model
    joblib.dump(rf_mixed, OUTPUT_MODEL_PATH)
    print(f"  Saved mixed model: {OUTPUT_MODEL_PATH}")

    # ── 7. POST-evaluation on synthetic test ─────────────────────────────────
    print(f"\n[phase4.6] Evaluating mixed model on synthetic test set...")
    post_results = evaluate_model(rf_mixed, X_synth_test, z_synth_test, model_name="Mixed")

    # ── 8. POST-evaluation on real set ───────────────────────────────────────
    print(f"\n[phase4.6] Evaluating mixed model on real set...")
    post_real_results = evaluate_model(rf_mixed, X_real, y_real, model_name="Mixed(Real)")
    post_real_preds = rf_mixed.predict(X_real)

    # ── 9. Zone switching analysis on real set ───────────────────────────────
    switches = np.sum(pre_real_preds != post_real_preds)
    print(f"\n[phase4.6] Real audio zone changes: {switches} / {n_real} switched")

    # Per-track switching details
    switching_tracks = []
    for i, (track, pre_z, post_z) in enumerate(zip(track_names, pre_real_preds, post_real_preds)):
        if pre_z != post_z:
            switching_tracks.append({
                "track": track,
                "pre_zone": int(pre_z),
                "post_zone": int(post_z)
            })

    # ── 10. Feature importance comparison ────────────────────────────────────
    print("\n[phase4.6] Computing feature importance (Gini)...")
    pre_fi = compute_feature_importance(rf_phase44, feature_names)
    post_fi = compute_feature_importance(rf_mixed, feature_names)

    print("\nTop-10 features BEFORE (Phase 4.4):")
    for item in pre_fi:
        print(f"  {item['rank']}. {item['feature']}: {item['gini_importance']:.4f}")

    print("\nTop-10 features AFTER (Mixed):")
    for item in post_fi:
        print(f"  {item['rank']}. {item['feature']}: {item['gini_importance']:.4f}")

    # Compare rankings
    pre_ranks = {item['feature']: item['rank'] for item in pre_fi}
    post_ranks = {item['feature']: item['rank'] for item in post_fi}
    all_top_features = set(pre_ranks.keys()) | set(post_ranks.keys())
    rank_changes = []
    for feat in all_top_features:
        pre_r = pre_ranks.get(feat, None)
        post_r = post_ranks.get(feat, None)
        if pre_r is not None and post_r is not None:
            rank_changes.append({
                "feature": feat,
                "pre_rank": pre_r,
                "post_rank": post_r,
                "delta": pre_r - post_r  # positive = improved rank (lower number)
            })

    # ── 11. Generate comparison report ───────────────────────────────────────
    print("\n[phase4.6] Generating comparison report...")

    pre_zone_dist = dict(zip(*np.unique(y_real, return_counts=True)))
    post_zone_dist = dict(zip(*np.unique(post_real_preds, return_counts=True)))

    report = {
        "phase": "4.6",
        "description": "Mixed-dataset retraining with sample weighting (synthetic=1.0, real=0.5)",
        "synthetic_dataset": str(SYNTHETIC_PATH),
        "real_dataset": str(REAL_X_PATH),
        "n_synthetic_total": int(X_synth.shape[0]),
        "n_synthetic_train": int(X_synth_train.shape[0]),
        "n_synthetic_test": int(X_synth_test.shape[0]),
        "n_real": int(n_real),
        "sample_weights": {
            "synthetic": SAMPLE_WEIGHT_SYNTH,
            "real": SAMPLE_WEIGHT_REAL
        },
        "rf_parameters": RF_PARAMS,
        "test_split_random_state": 42,
        "synthetic_test_indices": idx_test.tolist(),  # for reproducibility
        "pre_phase4.4": {
            "synthetic_test_accuracy": pre_results['accuracy'],
            "synthetic_test_macro_f1": pre_results['classification_report']['macro avg']['f1-score'],
            "synthetic_confusion_matrix": pre_results['confusion_matrix']
        },
        "post_mixed": {
            "synthetic_test_accuracy": post_results['accuracy'],
            "synthetic_test_macro_f1": post_results['classification_report']['macro avg']['f1-score'],
            "synthetic_confusion_matrix": post_results['confusion_matrix']
        },
        "real_set_evaluation": {
            "pre_accuracy": pre_real_results['accuracy'],
            "post_accuracy": post_real_results['accuracy'],
            "pre_zone_distribution": {str(k): int(v) for k, v in pre_zone_dist.items()},
            "post_zone_distribution": {str(k): int(v) for k, v in post_zone_dist.items()},
            "n_switches": int(switches),
            "switching_tracks": switching_tracks
        },
        "feature_importance": {
            "pre_top10": pre_fi,
            "post_top10": post_fi,
            "rank_changes": sorted(rank_changes, key=lambda x: abs(x['delta']), reverse=True)[:20]
        },
        "accuracy_delta_synthetic": float(post_results['accuracy'] - pre_results['accuracy']),
        "accuracy_delta_real": float(post_real_results['accuracy'] - pre_real_results['accuracy'])
    }

    with open(OUTPUT_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {OUTPUT_REPORT_PATH}")

    # ── 12. Summary ───────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("PHASE 4.6 SUMMARY")
    print("="*60)
    print(f"Synthetic test accuracy:  BEFORE={pre_results['accuracy']:.4f}  AFTER={post_results['accuracy']:.4f}  Δ={report['accuracy_delta_synthetic']:+.4f}")
    print(f"Real set accuracy:        BEFORE={pre_real_results['accuracy']:.4f}  AFTER={post_real_results['accuracy']:.4f}  Δ={report['accuracy_delta_real']:+.4f}")
    print(f"Real zone distribution (pre):  {pre_zone_dist}")
    print(f"Real zone distribution (post): {post_zone_dist}")
    print(f"Real tracks switching zones: {switches}/{n_real}")
    print(f"\nTop-3 feature rank changes:")
    for change in sorted(rank_changes, key=lambda x: -abs(x['delta']))[:3]:
        print(f"  {change['feature']}: rank {change['pre_rank']} → {change['post_rank']} (Δ{change['delta']:+d})")

    # Flag significant degradation
    if (pre_results['accuracy'] - post_results['accuracy']) > 0.02:
        print("\n⚠️  WARNING: Synthetic test accuracy dropped >2%. Archetype preservation trade-off detected.")

    print("\nDone.")

if __name__ == "__main__":
    main()
