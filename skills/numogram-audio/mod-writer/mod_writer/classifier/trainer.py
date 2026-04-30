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
