#!/usr/bin/env python3
"""Phase 4.6 — Mixed-Dataset Retraining

Merge synthetic (900) + real (40) examples with sample weighting:
  synthetic weight = 1.0  (anchor archetypes)
  real weight      = 0.5  (teach rhythm without overwhelming)

Outputs:
  phase4.6_rf_mixed.joblib
  phase4.6_mixed_report.json
"""

import sys, pathlib, json, numpy as np, joblib, time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

_this = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(_this.parent))
from mod_writer.classifier.data_collector import _digital_root  # for fallback zone derivation

mod_writer = _this.parent / 'mod_writer'
art = mod_writer / 'classifier' / 'artifacts'

# ── Synthetic ────────────────────────────────────────────────────────────────
synth_path = art / 'dataset_balanced_900.npz'
print(f"Loading synthetic: {synth_path.name}")
synth = np.load(synth_path)
X_synth = synth['X']
# Use zones as classification target, not raw AQ values
zones_synth = synth['zones'] if 'zones' in synth else np.array([_digital_root(int(a)) for a in synth['y']], dtype=np.int8)
print(f"  X_synth={X_synth.shape}, zones={sorted(set(zones_synth.tolist()))}")

# Hold-out test split (same random_state as Phase 4.4 training for fair compare)
X_synth_train, X_synth_test, z_synth_train, z_synth_test = train_test_split(
    X_synth, zones_synth, test_size=0.20, random_state=42, stratify=zones_synth
)
print(f"  Train: {X_synth_train.shape[0]}, Test: {X_synth_test.shape[0]}")

# ── Real ─────────────────────────────────────────────────────────────────────
real_dir = art / 'real_audio_run'
X_real = np.load(real_dir / 'real_audio_X.npz')['X']
real_preds = json.loads((real_dir / 'predictions' / 'real_predictions.json').read_text())
z_real = np.array([p['predicted_zone'] for p in real_preds], dtype=np.int8)
print(f"\nReal: X_real={X_real.shape}, zones={sorted(set(z_real.tolist()))}")

# ── Combine with weights ─────────────────────────────────────────────────────
X_mixed = np.vstack([X_synth_train, X_real])
z_mixed = np.concatenate([z_synth_train, z_real])
sample_weight = np.concatenate([
    np.full(len(z_synth_train), 1.0, dtype=np.float32),
    np.full(len(z_real),      0.5, dtype=np.float32)
])
print(f"\nMixed train: {X_mixed.shape[0]} total "
      f"(synth {len(z_synth_train)}×1.0 + real {len(z_real)}×0.5)")

# ── Train ─────────────────────────────────────────────────────────────────────
print("\nTraining RandomForest (mixed)...")
start = time.time()
rf = RandomForestClassifier(
    n_estimators=500, max_depth=None, min_samples_split=2,
    n_jobs=-1, random_state=42, verbose=0
)
rf.fit(X_mixed, z_mixed, sample_weight=sample_weight)
print(f"  done in {time.time()-start:.1f}s")

# ── Evaluate synthetic test ──────────────────────────────────────────────────
z_pred_synth = rf.predict(X_synth_test)
acc_synth = np.mean(z_pred_synth == z_synth_test)
orig_report = json.loads((art / 'phase4.4_report.json').read_text())
acc_orig = orig_report['rf_accuracy']
print(f"\nSynthetic test accuracy: {acc_orig:.4f} (Phase4.4) → {acc_synth:.4f} (Δ {acc_synth-acc_orig:+.4f})")

# ── Real predictions ─────────────────────────────────────────────────────────
z_real_pred = rf.predict(X_real)
dist_after = dict(zip(*np.unique(z_real_pred, return_counts=True)))
dist_before = dict(zip(*np.unique(z_real, return_counts=True)))
print(f"\nReal zone distribution:")
print(f"  before: Z1:{dist_before.get(1,0)}, Z6:{dist_before.get(6,0)}, Z7:{dist_before.get(7,0)}")
print(f"  after:  Z1:{dist_after.get(1,0)}, Z6:{dist_after.get(6,0)}, Z7:{dist_after.get(7,0)}")
changes = [(i, z_real[i], z_real_pred[i]) for i in range(len(z_real)) if z_real[i] != z_real_pred[i]]
print(f"  switches: {len(changes)}/{len(z_real)}")

# ── Save ─────────────────────────────────────────────────────────────────────
joblib.dump(rf, art / 'phase4.6_rf_mixed.joblib')
report = {
    "phase": "4.6", "description": "Mixed retraining (synthetic 900 train + real 40, weight 0.5)",
    "n_synthetic_train": len(z_synth_train), "n_real": len(z_real),
    "synthetic_test": {"accuracy_before": acc_orig, "accuracy_after": acc_synth},
    "real_distribution": {
        "before": {int(k): int(v) for k, v in dist_before.items()},
        "after": {int(k): int(v) for k, v in dist_after.items()},
        "switches": len(changes)
    },
    "feature_importance": [
        {"rank": i+1, "feature": orig_report['feature_names'][idx],
         "importance": float(rf.feature_importances_[idx])}
        for i, idx in enumerate(np.argsort(rf.feature_importances_)[::-1][:10])
    ],
}
(art / 'phase4.6_mixed_report.json').write_text(json.dumps(report, indent=2))
print(f"\n✓ Model saved: phase4.6_rf_mixed.joblib")
print(f"✓ Report saved: phase4.6_mixed_report.json")
