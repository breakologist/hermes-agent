"""Phase 3.1: Synthetic dataset generation from mod-writer.

Generates MOD files for every AQ value (0-99), renders to WAV in-memory,
extracts MIR features, flattens to feature vector, stores (X, y) NPZ.
"""

import numpy as np
import json
import tempfile
import os
from pathlib import Path

from ..song import SongBuilder
from ..audio_renderer import render_audio  # existing render function
from ..mir_profiler import MIRFeatureExtractor


def build_dataset(output_path=None, aq_range=range(100)):
    """
    Generate synthetic dataset.

    For each AQ in aq_range:
      1. SongBuilder(aq_seed=aq) → MOD data bytes
      2. render_audio(mod_data, format='wav') → WAV bytes
      3. MIRFeatureExtractor.profile(WAV bytes) → features JSON
      4. Flatten features → numpy vector
      5. Append to X (features) and y (aq)

    Returns:
      dict: {'X': np.ndarray, 'y': np.ndarray, 'meta': dict}
    """
    if output_path is None:
        output_path = Path(__file__).parent / "artifacts" / "dataset.npz"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"[dataset] Using cached {output_path}")
        cached = np.load(output_path)
        return {'X': cached['X'], 'y': cached['y'], 'meta': json.loads(cached['meta']) }

    print(f"[dataset] Generating synthetic data for {len(aq_range)} AQ values…")
    mir = MIRFeatureExtractor()
    X_list = []
    y_list = []
    meta = {
        'n_samples': len(aq_range),
        'features': mir.get_feature_names(),
        'generated_by': 'mod-writer synthetic dataset builder (Phase 3.1)'
    }

    for aq in aq_range:
        try:
            sb = SongBuilder(aq_seed=aq, just_intonation=False, use_periods=False)
            mod_bytes = sb.render_mod()

            # Render to WAV (in-memory)
            wav_bytes = render_audio(mod_bytes, format='wav')

            # Profile
            features = mir.profile_bytes(wav_bytes, fmt='wav')

            # Flatten
            vec = mir.flatten_features(features)
            X_list.append(vec)
            y_list.append(aq)

            if (aq + 1) % 10 == 0:
                print(f"  [{aq+1}/100] done")
        except Exception as e:
            print(f"  [WARN] AQ {aq} failed: {e}")
            continue

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int16)

    # Save
    np.savez_compressed(
        output_path,
        X=X, y=y,
        meta=json.dumps(meta)
    )
    print(f"[dataset] Saved {X.shape[0]} samples × {X.shape[1]} features → {output_path}")
    return {'X': X, 'y': y, 'meta': meta}


def load_dataset(path=None):
    """Load cached dataset NPZ."""
    if path is None:
        path = Path(__file__).parent / "artifacts" / "dataset.npz"
    if not Path(path).exists():
        raise FileNotFoundError(f"Dataset not found: {path}. Run build_dataset() first.")
    data = np.load(path)
    return {'X': data['X'], 'y': data['y'], 'meta': json.loads(data['meta'])}
