"""Phase 4.4 — Correlation analysis.

Train a RandomForest zone classifier, compute SHAP values, and generate
Baoyu‑styled artefacts:
  • feature_importance.svg  — horizontal bar chart
  • confusion_matrix.svg    — heatmap
  • shap_dependence_<top3>.svg — dependence plots for top features
  • correlation_matrix.svg  — Pearson feature–feature grid
  • phase4.4_report.json    — numeric metrics
"""

from __future__ import annotations
import argparse, json, sys, pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
import shap
import joblib

# ── local imports ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from mod_writer.classifier.data_collector import load_dataset  # type: ignore

# ── Constants ──────────────────────────────────────────────────────────────────
ART_DIR = pathlib.Path(__file__).parent / "artifacts"
ART_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = {
    "bg": "#0a0a0a", "fg": "#ccb8a0",
    "accent1": "#0055ff", "accent2": "#ff6b00", "accent3": "#00ff55",
    "text": "#e8dcc8", "grid": "#1a1a22",
}
ZONE_COLOR = {
    0: "#220022", 1: "#ff6b00", 2: "#ff4400", 3: "#ff0055",
    4: "#aa00ff", 5: "#0055ff", 6: "#00aaff", 7: "#00ffaa",
    8: "#00ff55", 9: "#ffffff",
}
plt.style.use('dark_background')


def prettify(name: str) -> str:
    """Make feature names report‑ready."""
    if name.startswith('key_'):   return f"Key: {name[4:]}"
    if name.startswith('scale_'): return name[6:].title()
    return (name
            .replace('_norm','')
            .replace('_',' ')
            .title())


# ── Main pipeline ──────────────────────────────────────────────────────────────
def run_phase4_4(dataset_path: pathlib.Path, n_estimators: int = 500, random_state: int = 42):
    print(f"[phase4.4] Loading dataset: {dataset_path}")
    data = load_dataset(str(dataset_path))
    X, y = data['X'], data['y']
    zones = np.array([int(z) for z in data['zones']])
    meta_raw = data.get('meta', {})
    # meta may be JSON string or dict
    if isinstance(meta_raw, (str, bytes)):
        meta = json.loads(meta_raw)
    else:
        meta = meta_raw

    # Feature names (reconstruct if missing from NPZ)
    feature_names = meta.get('feature_names')
    if feature_names is None:
        bands = ['sub_bass','bass','low_mid','mid','high_mid','high']
        spectral = ['spectral_centroid_hz','spectral_bandwidth_hz','spectral_rolloff','dynamic_complexity']
        rhythm = ['onset_rate_norm','bpm_norm','beat_conf_norm']
        keys  = [f'key_{k}' for k in ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']]
        scales = ['scale_major','scale_minor','scale_unknown']
        meta_f = ['duration_norm']
        feature_names = bands + spectral + rhythm + keys + scales + meta_f
        print(f"[phase4.4] Reconstructed {len(feature_names)} feature names.")
    else:
        print(f"[phase4.4] Using {len(feature_names)} stored feature names.")

    print(f"[phase4.4] X: {X.shape}, y: {y.shape}, zones: {sorted(set(zones.tolist()))}")

    # Collect artefacts for the report
    artifacts: dict[str, pathlib.Path | float | dict] = {}

    # Split (X, y=AQ, zones) → supervised classification targets = zones
    X_tr, X_te, y_tr, y_te, z_tr, z_te = train_test_split(
        X, y, zones, test_size=0.2, random_state=random_state, stratify=zones
    )
    print(f"[phase4.4] Split → train:{len(z_tr)}  test:{len(z_te)}  zones: {sorted(set(zones.tolist()))}")

    # RandomForest – predict zones (1-9).  y_tr/y_te are kept only for later correlation if desired.
    print(f"[phase4.4] Training RandomForest ({n_estimators} trees)…")
    rf = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=None,
        min_samples_leaf=2, random_state=random_state,
        n_jobs=-1, class_weight='balanced'
    )
    rf.fit(X_tr, z_tr)             # zones as labels
    acc = rf.score(X_te, z_te)     # zone accuracy
    print(f"[phase4.4] RF test zone accuracy: {acc:.2%}")

    # Zone predictions (needed for confusion matrix / report)
    z_pred = rf.predict(X_te)

    # SHAP
    print("[phase4.4] Computing SHAP values…")
    explainer = shap.TreeExplainer(rf)
    shap_vals = explainer.shap_values(X_te)  # list[n_classes] of (n_samples, n_features) or single array
    print(f"[phase4.4] SHAP array structure: {type(shap_vals)}  shapes: {[np.shape(a) for a in shap_vals] if isinstance(shap_vals, list) else np.shape(shap_vals)}")

    # Ensure shap_vals is stackable for averaging
    if isinstance(shap_vals, list):
        shap_stack = np.stack(shap_vals, axis=0)   # (n_classes, n_samples, n_features)
    else:
        shap_stack = shap_vals                     # already (n_samples, n_features, n_classes) or similar
        # If last axis is classes, transpose to front
        if shap_stack.ndim == 3 and shap_stack.shape[-1] == len(rf.classes_):
            shap_stack = np.moveaxis(shap_stack, -1, 0)

    # Save models
    rf_path = ART_DIR / "phase4.4_rf.joblib"
    explainer_path = ART_DIR / "phase4.4_explainer.joblib"
    joblib.dump(rf, rf_path)
    joblib.dump(explainer, explainer_path)
    artifacts['rf_model'] = rf_path
    artifacts['explainer'] = explainer_path

    # ── Plot: Feature importance ─────────────────────────────────────────────────
    importances = rf.feature_importances_
    order = np.argsort(importances)[::-1]
    fig, ax = plt.subplots(figsize=(10, 9), facecolor=PALETTE['bg'])
    ax.barh(range(len(importances)), importances[order],
            color=PALETTE['accent1'], alpha=0.85)
    ax.set_yticks(range(len(importances)))
    ax.set_yticklabels([prettify(feature_names[i]) for i in order],
                       color=PALETTE['fg'], fontsize=9)
    ax.set_xlabel('Gini importance', color=PALETTE['fg'])
    ax.set_title('Feature Importance — RandomForest Zone Classifier',
                 color=PALETTE['text'], fontsize=14, pad=16)
    ax.invert_yaxis()
    ax.grid(True, axis='x', color=PALETTE['grid'], alpha=0.3)
    fig.tight_layout()
    fi_path = ART_DIR / "feature_importance.svg"
    fig.savefig(fi_path, facecolor=PALETTE['bg'], edgecolor='none')
    plt.close(fig)
    artifacts['feature_importance'] = fi_path
    print(f"  → feature_importance.svg")

    # ── Plot: SHAP impact (mean |SHAP| across classes) ──────────────────────────
    mean_abs = np.abs(shap_stack).mean(axis=(0,1))  # (n_features,)
    order_s = np.argsort(mean_abs)[::-1]
    fig2, ax2 = plt.subplots(figsize=(10, 9), facecolor=PALETTE['bg'])
    ax2.barh(range(len(mean_abs)), mean_abs[order_s],
             color=PALETTE['accent2'], alpha=0.85)
    ax2.set_yticks(range(len(mean_abs)))
    ax2.set_yticklabels([prettify(feature_names[i]) for i in order_s],
                        color=PALETTE['fg'], fontsize=8)
    ax2.set_xlabel('Mean |SHAP value|', color=PALETTE['fg'])
    ax2.set_title('Feature Impact (SHAP) — Multi‑Class Average',
                  color=PALETTE['text'], fontsize=14, pad=16)
    ax2.invert_yaxis()
    ax2.grid(True, axis='x', color=PALETTE['grid'], alpha=0.3)
    fig2.tight_layout()
    shap_bar_path = ART_DIR / "shap_feature_impact.svg"
    fig2.savefig(shap_bar_path, facecolor=PALETTE['bg'], edgecolor='none')
    plt.close(fig2)
    artifacts['shap_impact'] = shap_bar_path
    print(f"  → shap_feature_impact.svg")

    # ── Plot: Confusion matrix ───────────────────────────────────────────────────
    cm = confusion_matrix(z_te, z_pred, labels=sorted(rf.classes_))
    fig_cm, ax_cm = plt.subplots(figsize=(8, 7), facecolor=PALETTE['bg'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='viridis', ax=ax_cm,
                cbar_kws={'label': 'Count'}, linewidths=0.5, linecolor=PALETTE['grid'])
    ax_cm.set_xlabel('Predicted Zone', color=PALETTE['fg'])
    ax_cm.set_ylabel('True Zone', color=PALETTE['fg'])
    ax_cm.set_title('Confusion Matrix — Test Set', color=PALETTE['text'], fontsize=14, pad=16)
    ax_cm.tick_params(colors=PALETTE['fg'])
    cm_path = ART_DIR / "confusion_matrix.svg"
    fig_cm.savefig(cm_path, facecolor=PALETTE['bg'], edgecolor='none')
    plt.close(fig_cm)
    artifacts['confusion_matrix'] = cm_path
    print(f"  → confusion_matrix.svg")

    # ── Dependence for top‑3 features ────────────────────────────────────────────
    for rank, fi in enumerate(order_s[:3], 1):
        fname = feature_names[fi]
        plt.figure(figsize=(7, 5), facecolor=PALETTE['bg'])
        for cls_idx, cls in enumerate(sorted(set(zones))):
            cls_vals = shap_stack[cls_idx, :, fi]
            plt.scatter(X_te[:, fi], cls_vals, s=12, alpha=0.5,
                        color=ZONE_COLOR.get(cls, '#ffffff'), label=f'Zone {cls}')
        plt.xlabel(prettify(fname), color=PALETTE['fg'])
        plt.ylabel('SHAP value', color=PALETTE['fg'])
        plt.title(f'SHAP Dependence — {prettify(fname)} (top-{rank})',
                  color=PALETTE['text'], fontsize=13, pad=14)
        plt.grid(True, color=PALETTE['grid'], alpha=0.3)
        plt.legend(facecolor=PALETTE['bg'], edgecolor='none',
                   labelcolor=PALETTE['fg'], fontsize=8, loc='best')
        dep_path = ART_DIR / f"shap_dependence_{rank}_{fname}.svg"
        plt.savefig(dep_path, facecolor=PALETTE['bg'], edgecolor='none')
        plt.close()
        artifacts[f'shap_dependence_{rank}'] = dep_path
        print(f"  → {dep_path.name}")

    # ── Correlation matrix ───────────────────────────────────────────────────────
    corr = np.corrcoef(X, rowvar=False)
    fig, ax = plt.subplots(figsize=(12, 10), facecolor=PALETTE['bg'])
    sns.heatmap(corr, cmap='coolwarm', center=0, ax=ax,
                cbar_kws={'label': 'Pearson r'}, linewidths=0.5, linecolor=PALETTE['grid'])
    ax.set_title('Feature Correlation Matrix — 29 MIR Descriptors',
                 color=PALETTE['text'], fontsize=14, pad=16)
    ax.tick_params(colors=PALETTE['fg'])
    corr_path = ART_DIR / "correlation_matrix.svg"
    fig.savefig(corr_path, facecolor=PALETTE['bg'], edgecolor='none')
    plt.close(fig)
    artifacts['correlation_matrix'] = corr_path
    print(f"  → correlation_matrix.svg")

    # ── Report ───────────────────────────────────────────────────────────────────
    rep = {
        "phase": "4.4",
        "description": "RandomForest + SHAP correlation analysis",
        "dataset": str(dataset_path),
        "n_samples_trainsize": int(X.shape[0]),
        "train_n": int(len(y_tr)), "test_n": int(len(y_te)),
        "n_features": int(X.shape[1]),
        "feature_names": feature_names,
        "rf_accuracy": float(acc),
        "rf_oob": None,
        "classification_report": classification_report(z_te, z_pred, output_dict=True),
        "top_10_features": [
            {"rank": r+1, "feature": feature_names[i], "gini_importance": float(importances[i]),
             "mean_abs_shap": float(mean_abs[i])}
            for r, i in enumerate(order[:10])
        ],
        "artifacts": {k: str(v) for k, v in artifacts.items() if isinstance(v, pathlib.Path)},
    }
    rep_path = ART_DIR / "phase4.4_report.json"
    with open(rep_path, 'w') as f:
        json.dump(rep, f, indent=2)
    print(f"  → phase4.4_report.json")

    print(f"\n[phase4.4] Done. All artefacts in {ART_DIR}\n")
    return rep


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.4 — RandomForest + SHAP correlation analysis"
    )
    parser.add_argument("--data", type=str, default=None,
                        help="Path to dataset .npz (default: balanced 900‑sample set)")
    parser.add_argument("--estimators", type=int, default=500, help="RandomForest tree count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    if args.data is None:
        default = pathlib.Path(__file__).parent / "artifacts" / "dataset_balanced_900.npz"
        dataset_path = default
    else:
        dataset_path = pathlib.Path(args.data)

    run_phase4_4(dataset_path, n_estimators=args.estimators, random_state=args.seed)
