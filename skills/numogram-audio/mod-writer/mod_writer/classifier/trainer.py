"""Phase 3.2: Train a regressor to predict AQ from MIR features."""

import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

from .data_collector import load_dataset


def train(dataset_path=None, test_size=0.2, random_state=42):
    """
    Load synthetic dataset, train MLPRegressor, evaluate, save artifacts.
    """
    print("[trainer] Loading dataset…")
    data = load_dataset(dataset_path)
    X, y = data['X'], data['y']

    print(f"[trainer] Dataset: {X.shape[0]} samples, {X.shape[1]} features")

    # Stratify by zone (derived from AQ)
    zones = np.array([aq_to_zone(aq) for aq in y])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=zones
    )

    print(f"[trainer] Train: {len(y_train)}, Test: {len(y_test)}")

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("[trainer] Training MLPRegressor…")
    model = MLPRegressor(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        max_iter=1000,
        random_state=random_state,
        verbose=False
    )
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    acc5 = np.mean(np.abs(y_test - y_pred) <= 5)

    # Zone accuracy (round predicted AQ to nearest zone)
    zone_pred = np.array([aq_to_zone(int(round(p))) for p in y_pred])
    zone_true = np.array([aq_to_zone(aq) for aq in y_test])
    zone_acc = np.mean(zone_pred == zone_true)

    print(f"[trainer] MAE: {mae:.3f} AQ | RMSE: {rmse:.3f} | Acc@5: {acc5:.3%} | Zone Acc: {zone_acc:.3%}")

    # Save artifacts
    artifacts_dir = Path(__file__).parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(scaler, artifacts_dir / "scaler.joblib")
    joblib.dump(model, artifacts_dir / "model.joblib")

    # Feature importance (permutation — slow but accurate)
    print("[trainer] Artifacts saved to", artifacts_dir)

    return {
        'mae': mae,
        'rmse': rmse,
        'acc5': acc5,
        'zone_accuracy': zone_acc,
        'n_test': len(y_test)
    }


def aq_to_zone(aq):
    """Map AQ (0-99) → zone (0-9) via digital root."""
    dr = sum(int(d) for d in str(aq)) % 9
    return 9 if dr == 0 else dr


def train_zone_classifier(
    dataset_path: str | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
    hidden_sizes: tuple = (256, 128),
    dropout: float = 0.3,
    max_iter: int = 1000,
) -> dict:
    """Phase 4.3: Train a 9‑way zone classifier.

    Parameters
    ----------
    dataset_path : str | None
        Path to .npz produced by :func:`build_dataset`. Uses latest artifact if None.
    hidden_sizes, dropout, max_iter : MLP hyperparameters

    Returns
    -------
    dict with metrics and artifact paths.
    """
    from sklearn.neural_network import MLPClassifier
    from sklearn.metrics import accuracy_score, top_k_accuracy_score, confusion_matrix, classification_report

    print("[trainer-zone] Loading dataset…")
    data = load_dataset(dataset_path)
    X, zones = data['X'], data['zones']

    # Ensure zones are 1–9 integers
    zones = zones.astype(int)
    print(f"[trainer-zone] Dataset: {X.shape[0]} samples, {X.shape[1]} features, zones {set(zones)}")

    # Stratified split by zone
    X_train, X_test, z_train, z_test = train_test_split(
        X, zones, test_size=test_size, random_state=random_state, stratify=zones
    )
    print(f"[trainer-zone] Train: {len(z_train)}, Test: {len(z_test)}")

    # Scale
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # MLPClassifier
    print(f"[trainer-zone] Training MLPClassifier(hidden={hidden_sizes}, dropout={dropout})…")
    clf = MLPClassifier(
        hidden_layer_sizes=hidden_sizes,
        activation='relu',
        solver='adam',
        max_iter=max_iter,
        random_state=random_state,
        verbose=False,
    )
    clf.fit(X_train_s, z_train)

    # Predictions
    z_pred      = clf.predict(X_test_s)
    z_pred_proba = clf.predict_proba(X_test_s)

    # Metrics
    acc       = accuracy_score(z_test, z_pred)
    acc_top3  = top_k_accuracy_score(z_test, z_pred_proba, k=3)
    cm        = confusion_matrix(z_test, z_pred, labels=list(range(1,10)))
    report    = classification_report(z_test, z_pred, labels=list(range(1,10)), output_dict=True)

    print(f"[trainer-zone] Top-1 Acc: {acc:.3%} | Top-3 Acc: {acc_top3:.3%}")
    print("[trainer-zone] Confusion matrix (rows=true, cols=pred):")
    print(cm)

    # Save artifacts
    artifacts_dir = Path(__file__).parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, artifacts_dir / "zone_scaler.joblib")
    joblib.dump(clf,   artifacts_dir / "zone_clf.joblib")

    report_path = artifacts_dir / "phase4.3_report.json"
    import json
    with open(report_path, "w") as f:
        json.dump({
            'accuracy': acc,
            'top3_accuracy': acc_top3,
            'confusion_matrix': cm.tolist(),
            'classification_report': report,
            'n_test': len(z_test),
            'n_train': len(z_train),
            'n_features': X.shape[1],
        }, f, indent=2)

    print(f"[trainer-zone] Artifacts saved to {artifacts_dir}")
    return {
        'accuracy': acc,
        'top3_accuracy': acc_top3,
        'confusion_matrix': cm,
        'report_path': str(report_path),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train zone classifier or AQ regressor")
    parser.add_argument("--data", type=str, default=None, help="Path to dataset .npz (defaults to latest artifact)")
    parser.add_argument("--zone-classifier", action="store_true", help="Train 9-way zone classifier (Phase 4.3)")
    args = parser.parse_args()

    if args.zone_classifier:
        print("[trainer] Training zone classifier (Phase 4.3)…")
        metrics = train_zone_classifier(dataset_path=args.data)
        print(f"Top-1 Acc: {metrics['accuracy']:.3%} | Top-3 Acc: {metrics['top3_accuracy']:.3%}")
        print(f"Report saved: {metrics['report_path']}")
    else:
        print("[trainer] Training AQ regressor (Phase 3.2)…")
        metrics = train(dataset_path=args.data)
        print(f"MAE: {metrics['mae']:.3f} | Zone Acc: {metrics['zone_accuracy']:.3%}")
