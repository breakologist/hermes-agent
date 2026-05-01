#!/usr/bin/env python3
"""
Phase 3 complete orchestrator — dataset generation → training → evaluation.
Run: python run_phase3.py
"""

import sys, os, tempfile, io, json, numpy as np, joblib, subprocess

skill_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, skill_root)
ar_path = os.path.join(os.path.expanduser("~/.hermes/skills/"), "numogram-audio/audio-renderer")
sys.path.insert(0, ar_path)

from mod_writer.song import SongBuilder
from mod_writer.mir_profiler import MIRFeatureExtractor
from renderer import render_mod_to_wav
from mod_writer.writer import ModWriter


def mod_to_bytes(mod_writer):
    out = io.BytesIO()
    out.write(mod_writer.pack_header())
    for pat in mod_writer.patterns:
        out.write(pat.pack())
    for samp in mod_writer.samples:
        out.write(samp.data)
    return out.getvalue()


FEATURE_NAMES = [
    'band_sub_bass','band_bass','band_low_mid','band_mid','band_high_mid','band_high',
    'centroid','bandwidth','rolloff','dyn_complexity',
    'onset_rate_norm','bpm_norm','beatconf_norm',
    'key_C','key_C#','key_D','key_D#','key_E','key_F','key_F#','key_G','key_G#','key_A','key_A#','key_B',
    'scale_major','scale_minor','scale_unknown','duration_norm'
]

KEY_MAP = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}


def flatten_features(features):
    vec = []
    bands = features.get('lowlevel', {}).get('bands', {})
    for b in ['sub_bass','bass','low_mid','mid','high_mid','high']:
        vec.append(bands.get(b, 0.0))
    t = features.get('lowlevel', {}).get('timbre', {})
    vec.append(t.get('spectral_centroid', 0.0))
    vec.append(t.get('spectral_bandwidth', 0.0))
    vec.append(t.get('spectral_rolloff', 0.0))
    vec.append(t.get('dynamic_complexity', 0.0))
    r = features.get('rhythm', {})
    vec.append(r.get('onset_rate', 0.0) / 200.0)
    vec.append(r.get('bpm', 0.0) / 200.0)
    vec.append(r.get('beat_confidence', 0.0) / 100.0)
    k = features.get('key', {})
    key_idx = KEY_MAP.get(k.get('key', 'C'), 0)
    key_onehot = [0]*12; key_onehot[key_idx] = 1; vec.extend(key_onehot)
    scale = k.get('scale')
    if scale == 'major': vec.extend([1,0,0])
    elif scale == 'minor': vec.extend([0,1,0])
    else: vec.extend([0,0,1])
    d = features.get('metadata', {}).get('duration', 0.0)
    vec.append(d / 120.0)
    return np.array(vec, dtype=np.float32)


def aq_to_zone(aq):
    dr = sum(int(d) for d in str(aq)) % 9
    return 9 if dr == 0 else dr


def build_dataset(aq_range=range(100)):
    out_path = os.path.join(skill_root, "mod_writer", "classifier", "artifacts", "dataset.npz")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        data = np.load(out_path, allow_pickle=False)
        meta = json.loads(data['meta'].item())
        return {'X': data['X'], 'y': data['y'], 'meta': meta}

    mir = MIRFeatureExtractor()
    X, y, failures = [], [], []
    print(f"[dataset] Generating {len(aq_range)} synthetic MOD→WAV profiles…")
    for aq in aq_range:
        try:
            sb = SongBuilder()
            sb.add_section(zone=1, aq_seed=str(aq))
            mod_obj = sb.build(verbose=False)
            mod_bytes = mod_to_bytes(mod_obj)
            with tempfile.NamedTemporaryFile(suffix='.mod', delete=False) as tmp:
                tmp.write(mod_bytes); tmp.flush(); mod_path = tmp.name
            wav_path = render_mod_to_wav(mod_path)
            features = mir.extract(wav_path)
            X.append(flatten_features(features))
            y.append(aq)
            os.unlink(mod_path); os.unlink(wav_path)
            if (aq+1) % 20 == 0:
                print(f"  [{aq+1}/{len(aq_range)}] done")
        except Exception as e:
            failures.append((aq, str(e)))
            if len(failures) <= 3:
                import traceback; traceback.print_exc()
            continue

    X = np.stack(X, dtype=np.float32) if X else np.zeros((0, len(FEATURE_NAMES)))
    y = np.array(y, dtype=np.int16)
    meta = {
        'n_samples': len(y), 'n_features': int(X.shape[1]),
        'feature_names': FEATURE_NAMES, 'generator': 'synthetic (zone=1 + aq_seed)',
        'date': '2026-05-01', 'failures': failures
    }
    np.savez_compressed(out_path, X=X, y=y, meta=json.dumps(meta))
    print(f"[dataset] Saved X={X.shape}, y={y.shape}")
    if failures:
        print(f"[dataset] {len(failures)} failures")
    return {'X': X, 'y': y, 'meta': meta}


def train(dataset=None):
    if dataset is None:
        path = os.path.join(skill_root, "mod_writer", "classifier", "artifacts", "dataset.npz")
        data = np.load(path, allow_pickle=False)
        meta = json.loads(data['meta'].item())
        X, y = data['X'], data['y']
    else:
        X, y, meta = dataset['X'], dataset['y'], dataset['meta']

    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.neural_network import MLPRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    zones = np.array([aq_to_zone(int(a)) for a in y])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=zones)
    print(f"[trainer] Train={len(y_train)}, Test={len(y_test)}")

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print("[trainer] Training MLPRegressor…")
    model = MLPRegressor(hidden_layer_sizes=(128,64), activation='relu', max_iter=1000, random_state=42, verbose=False)
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_test_s)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    acc5 = np.mean(np.abs(y_test - y_pred) <= 5)
    zone_pred = np.array([aq_to_zone(int(round(p))) for p in y_pred])
    zone_true = np.array([aq_to_zone(int(a)) for a in y_test])
    zone_acc = np.mean(zone_pred == zone_true)

    print(f"[trainer] MAE={mae:.3f} RMSE={rmse:.3f} Acc@5={acc5:.3%} ZoneAcc={zone_acc:.3%}")

    artifacts = os.path.join(skill_root, "mod_writer", "classifier", "artifacts")
    joblib.dump(scaler, os.path.join(artifacts, "scaler.joblib"))
    joblib.dump(model, os.path.join(artifacts, "model.joblib"))
    print(f"[trainer] Saved artifacts → {artifacts}")

    return {'mae': mae, 'rmse': rmse, 'acc5': float(acc5), 'zone_accuracy': float(zone_acc), 'n_test': len(y_test)}


if __name__ == '__main__':
    print("=== PHASE 3 — Mod-Writer Numogram Classifier ===")
    dataset = build_dataset(range(100))
    metrics = train(dataset)
    print("\\n=== RESULTS ===")
    print(json.dumps(metrics, indent=2))
