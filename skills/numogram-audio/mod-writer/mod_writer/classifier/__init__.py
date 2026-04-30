"""
mod_writer.classifier — MIR features → AQ prediction.

Public API:
  predict_audio(path: str) -> dict
  batch_predict(directory: str, limit=100) -> List[dict]
  load_artifacts() -> (scaler, model)
"""

import os, sys, tempfile, numpy as np, joblib, subprocess

# Ensure mod_writer package importable
_skill_root = os.path.join(os.path.dirname(__file__), "..", "..")
if _skill_root not in sys.path:
    sys.path.insert(0, _skill_root)

from mod_writer.mir_profiler import MIRFeatureExtractor

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
_scaler = None
_model = None

KEY_MAP = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}


def load_artifacts():
    global _scaler, _model
    if _scaler is None:
        _scaler = joblib.load(os.path.join(ARTIFACTS_DIR, "scaler.joblib"))
        _model  = joblib.load(os.path.join(ARTIFACTS_DIR, "model.joblib"))
    return _scaler, _model


def _flatten(features: dict) -> np.ndarray:
    vec = []
    bands = features.get('lowlevel',{}).get('bands',{})
    for b in ['sub_bass','bass','low_mid','mid','high_mid','high']:
        vec.append(bands.get(b, 0.0))
    timbre = features.get('lowlevel',{}).get('timbre',{})
    vec.append(timbre.get('spectral_centroid',0.0) or 0.0)
    vec.append(timbre.get('spectral_bandwidth',0.0) or 0.0)
    vec.append(timbre.get('spectral_rolloff',0.0) or 0.0)
    vec.append(timbre.get('dynamic_complexity',0.0) or 0.0)
    rhythm = features.get('rhythm',{})
    vec.append((rhythm.get('onset_rate') or 0.0) / 200.0)
    vec.append((rhythm.get('bpm') or 0.0) / 200.0)
    vec.append((rhythm.get('beat_confidence') or 0.0) / 100.0)
    key = features.get('key') or {}
    key_idx = KEY_MAP.get(key.get('key'), 0) if key.get('key') else 0
    key_onehot = [0]*12; key_onehot[key_idx] = 1; vec.extend(key_onehot)
    scale = key.get('scale') if key else None
    vec.extend([1,0,0] if scale=='major' else [0,1,0] if scale=='minor' else [0,0,1])
    meta = features.get('metadata',{}) or {}
    dur = meta.get('duration_s') or meta.get('duration') or 0.0
    vec.append(float(dur)/120.0)
    return np.array(vec, dtype=np.float32)


def _aq_to_zone(aq):
    num = int(round(abs(aq)))
    dr = sum(int(d) for d in str(num)) % 9
    return 9 if dr == 0 else dr


def predict_audio(path: str) -> dict:
    """Transcode if necessary, extract MIR features, predict AQ."""
    ext = os.path.splitext(path)[1].lower()
    if ext != '.wav':
        fd, wav = tempfile.mkstemp(suffix='.wav'); os.close(fd)
        subprocess.run(
            ['ffmpeg','-y','-i',path,'-f','wav','-acodec','pcm_s16le','-ar','44100','-ac','2',wav],
            capture_output=True, timeout=60
        )
        cleanup = True
    else:
        wav = path; cleanup = False

    try:
        feats = MIRFeatureExtractor().extract(wav, use_all=False)
        vec = _flatten(feats).reshape(1, -1)
        scaler, model = load_artifacts()
        pred = float(model.predict(scaler.transform(vec))[0])
        meta = feats.get('metadata',{}) or {}
        return {
            'file': os.path.basename(path),
            'path': path,
            'predicted_aq': round(pred, 2),
            'zone': _aq_to_zone(int(round(pred))),
            'duration_s': meta.get('duration_s', 0.0),
            'bpm': feats.get('midlevel',{}).get('bpm'),
            'key': (feats.get('key',{}).get('key') if feats.get('key') else None),
            'scale': (feats.get('key',{}).get('scale') if feats.get('key') else None),
        }
    finally:
        if cleanup and os.path.exists(wav):
            os.unlink(wav)


def batch_predict(directory: str, limit: int = 100) -> list:
    """Walk `directory`, predict first `limit` audio files."""
    exts = {'.mp3','.flac','.wav','.m4a','.ogg'}
    results = []
    count = 0
    for root, dirs, files in os.walk(directory):
        for f in files:
            if os.path.splitext(f)[1].lower() in exts:
                try:
                    r = predict_audio(os.path.join(root, f))
                    results.append(r)
                    count += 1
                    if count >= limit:
                        return results
                except Exception:
                    continue
    return results
