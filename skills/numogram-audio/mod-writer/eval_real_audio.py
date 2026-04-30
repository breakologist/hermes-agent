#!/usr/bin/env python3
"""
Phase 3.3 — Real Audio Validation
Predict AQ for tracks from music collection using trained classifier.
"""



def fmt(v, pattern="{:.1f}", default="?"):
    return pattern.format(v) if v is not None else default


import os, sys, tempfile, subprocess, csv, json, numpy as np, joblib
from collections import Counter

HOME = os.path.expanduser("~")
SKILL_DIR = os.path.join(HOME, ".hermes", "skills", "numogram-audio", "mod-writer")
sys.path.insert(0, SKILL_DIR)

from mod_writer.mir_profiler import MIRFeatureExtractor

# ── Classifier artifacts ────────────────────────────────────────────────
ARTIFACTS = os.path.join(SKILL_DIR, "mod_writer", "classifier", "artifacts")
scaler = joblib.load(os.path.join(ARTIFACTS, "scaler.joblib"))
model  = joblib.load(os.path.join(ARTIFACTS, "model.joblib"))

KEY_MAP = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}

def flatten_features(features: dict) -> np.ndarray:
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
    key_str = key.get('key')
    key_idx = KEY_MAP.get(key_str, 0) if key_str else 0
    key_onehot = [0]*12; key_onehot[key_idx] = 1; vec.extend(key_onehot)
    scale = key.get('scale') if key else None
    vec.extend([1,0,0] if scale=='major' else [0,1,0] if scale=='minor' else [0,0,1])
    meta = features.get('metadata',{}) or {}
    dur = meta.get('duration_s') or meta.get('duration') or 0.0
    vec.append(float(dur)/120.0)
    return np.array(vec, dtype=np.float32)

def aq_to_zone(aq):
    num = int(round(abs(aq)))
    dr = sum(int(d) for d in str(num)) % 9
    return 9 if dr==0 else dr

def transcode_to_wav(in_path: str) -> str:
    fd, tmp = tempfile.mkstemp(suffix='.wav'); os.close(fd)
    subprocess.run(
        ['ffmpeg','-y','-i',in_path,'-f','wav','-acodec','pcm_s16le','-ar','44100','-ac','2',tmp],
        capture_output=True, timeout=60
    )
    return tmp

def predict(audio_path: str) -> dict:
    ext = os.path.splitext(audio_path)[1].lower()
    wav_path = audio_path if ext == '.wav' else transcode_to_wav(audio_path)
    cleanup = (ext != '.wav')
    try:
        feats = MIRFeatureExtractor().extract(wav_path, use_all=False)
        vec = flatten_features(feats).reshape(1,-1)
        pred = float(model.predict(scaler.transform(vec))[0])
        meta = feats.get('metadata',{}) or {}
        return {
            'file': os.path.basename(audio_path),
            'path': audio_path,
            'predicted_aq': round(pred, 2),
            'zone': aq_to_zone(int(round(pred))),
            'duration_s': meta.get('duration_s', 0.0),
            'bpm': feats.get('midlevel',{}).get('bpm'),
            'key': (feats.get('key',{}).get('key') if feats.get('key') else None),
            'scale': (feats.get('key',{}).get('scale') if feats.get('key') else None),
        }
    except Exception as e:
        return {'file': os.path.basename(audio_path), 'path': audio_path, 'error': str(e)}
    finally:
        if cleanup and os.path.exists(wav_path):
            os.unlink(wav_path)

# ── Candidate track selection ────────────────────────────────────────────
MUSIC_ROOT = "/run/media/etym/Extreme SSD/music/"
ARTIST_DIRS = [
    "Kimberly Steele",
    "Gregorian Chant Rosary.mp3",
    "Death's Dynamic Shroud",
    "Current 93",
    "Nurse With Wound",
    "Coil",
    "Aphex Twin",
    "Autechre",
    "Z'EV",
    "Hildegarde von Bingen",
    "John Zorn",
    "Bjork",
    "Current 93",
]
EXTS = {'.mp3','.flac','.wav','.m4a','.ogg'}

candidates = []
for entry in ARTIST_DIRS:
    full = os.path.join(MUSIC_ROOT, entry)
    if os.path.isdir(full):
        for root, dirs, files in os.walk(full):
            for f in files:
                if os.path.splitext(f)[1].lower() in EXTS:
                    candidates.append(os.path.join(root, f))
                    break
            if candidates and os.path.dirname(candidates[-1]) == full:
                break
    elif os.path.isfile(full):
        candidates.append(full)
candidates = list(dict.fromkeys(candidates))  # dedup, preserve order

# ── Predict up to 10 valid tracks ───────────────────────────────────────
results = []
for path in candidates:
    if len(results) >= 10:
        break
    r = predict(path)
    if 'error' not in r:
        results.append(r)
        print(f"{len(results):<4} {r['file'][:55]:<55} AQ={r['predicted_aq']:>7.1f} Z={r['zone']}  BPM={fmt(r['bpm'])}  Key={r.get('key') or '?'}")
    else:
        print(f"    [SKIP] {os.path.basename(path)}: {r['error'][:60]}")

# ── Save CSV ─────────────────────────────────────────────────────────────
out_csv = os.path.join(ARTIFACTS, "real_audio_predictions.csv")
fieldnames = ['file','path','predicted_aq','zone','duration_s','bpm','key','scale']
with open(out_csv, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(results)

print(f"\n✅ {len(results)} tracks → {out_csv}")
if results:
    print("AQ range:", min(r['predicted_aq'] for r in results), "–", max(r['predicted_aq'] for r in results))
    print("Zone distribution:", dict(sorted(Counter(r['zone'] for r in results).items())))
