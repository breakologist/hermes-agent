#!/usr/bin/env python3
"""
Validate zone‑bias: generate N mini‑patterns per target zone, classify via the
Phase 4 zone classifier, and report pass rate. Expected: ≥90% classified as
target zone.
"""
import argparse, os, sys, tempfile, joblib
# Extend Python path to include mod-writer and audio-renderer skills
sys.path.insert(0, '/home/etym/.hermes/skills/numogram-audio/mod-writer')
sys.path.insert(0, '/home/etym/.hermes/skills/numogram-audio/audio-renderer')

from mod_writer.song import SongBuilder
from renderer import render_mod_to_wav
from mod_writer.mir_profiler import MIRFeatureExtractor
import numpy as np

# ── Zone classifier artefacts ───────────────────────────────────────────────
ARTIFACTS_DIR = (
    '/home/etym/.hermes/skills/numogram-audio/mod-writer/'
    'mod_writer/classifier/artifacts'
)
ZONE_SCALER = joblib.load(os.path.join(ARTIFACTS_DIR, 'zone_scaler.joblib'))
ZONE_CLF   = joblib.load(os.path.join(ARTIFACTS_DIR, 'zone_clf.joblib'))

def classify_track(mod_path: str) -> int | None:
    """Render a .mod file, extract MIR features, predict zone using Phase 4 zone classifier."""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            wav_path = os.path.join(tmp, 'tmp.wav')
            render_mod_to_wav(mod_path, wav_path)
            feas = MIRFeatureExtractor().extract(wav_path, use_all=False)
            # Flatten to base 29‑dim vector exactly as training did
            vec = _flatten_features(feas).reshape(1, -1)
            vec_scaled = ZONE_SCALER.transform(vec)
            zone_pred = ZONE_CLF.predict(vec_scaled)[0]
            return int(zone_pred)
    except Exception as e:
        print(f"[error] classify_track({mod_path}): {e}", file=sys.stderr)
        return None

def _flatten_features(features: dict) -> np.ndarray:
    """Extract 29‑dim feature vector (same as data_collector._flatten_features)."""
    KEY_MAP = {k: i for i, k in enumerate(
        ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    )}
    vec = []
    low = features.get('lowlevel', {})
    for band_name in ['sub_bass','bass','low_mid','mid','high_mid','high']:
        vec.append(low.get(band_name, 0.0))
    vec.append(low.get('spectral_centroid_hz', 0.0) or 0.0)
    vec.append(low.get('spectral_bandwidth_hz', 0.0) or 0.0)
    vec.append(low.get('spectral_rolloff', 0.0) or 0.0)
    vec.append(low.get('dynamic_complexity', 0.0) or 0.0)
    mid = features.get('midlevel', {})
    vec.append((mid.get('onset_rate') or 0.0) / 200.0)
    vec.append((mid.get('bpm') or 0.0) / 200.0)
    vec.append((mid.get('beat_confidence', 0.0) or 0.0) / 100.0)
    key_str = mid.get('key', '')
    key_idx = KEY_MAP.get(key_str, 0)
    key_onehot = [0]*12; key_onehot[key_idx] = 1
    vec.extend(key_onehot)
    scale = mid.get('scale', 'major')
    scale_onehot = [1,0,0] if scale=='major' else ([0,1,0] if scale=='minor' else [0,0,1])
    vec.extend(scale_onehot)
    meta = features.get('metadata', {})
    dur = meta.get('duration_s', 0.0)
    vec.append(dur / 120.0)
    return np.array(vec, dtype=np.float32)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zone', type=int, required=True, help='Target zone (1-9)')
    parser.add_argument('--rounds', type=int, default=50)
    parser.add_argument('--length', type=int, default=16)
    parser.add_argument('--outdir', default='/tmp/zone_bias_validation')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Monkey‑patch to use ModComposer.target_zone
    sys.path.insert(0, '/home/etym/.hermes/skills/numogram-audio/mod-writer-composer')
    from composer_extension import patch_mod_composer
    patch_mod_composer()

    from mod_writer.composer import ModComposer

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
