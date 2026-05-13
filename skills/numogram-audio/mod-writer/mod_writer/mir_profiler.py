"""MIR feature extraction with optional dependencies.

All heavy libraries (librosa, madmom, essentia, musicnn) are optional.
Core features (RMS, peak, band energy, spectral shape) use only numpy/scipy.
Missing libraries simply produce empty sections in the output JSON.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

try:
    from scipy.io import wavfile
    from scipy.signal import welch
    _SCIPY_WAV = True
    _SCIPY_WELCH = True
except ImportError:
    _SCIPY_WAV = False
    _SCIPY_WELCH = False

# Optional dependency availability flags
try:
    import librosa
    _HAS_LIBROSA = True
except ImportError:
    _HAS_LIBROSA = False

try:
    import madmom
    _HAS_MADMOM = True
except ImportError:
    _HAS_MADMOM = False

try:
    import essentia.standard as es
    _HAS_ESSENTIA = True
except ImportError:
    _HAS_ESSENTIA = False


# Duration cap for real-world tracks (seconds)
MAX_ANALYSIS_SECONDS = 180

try:
    from musicnn.extractor import extractor as _musicnn_extractor
    _HAS_MUSICNN = True
except ImportError:
    _HAS_MUSICNN = False


# ── Band definitions (Hz) ──────────────────────────────────────────────────
BANDS = [
    (0, 150),      # sub-bass
    (150, 300),    # bass
    (300, 1000),   # low-mid
    (1000, 3000),  # mid
    (3000, 8000),  # high-mid
    (8000, 22050), # high (Nyquist for 44.1k)
]

BAND_NAMES = ['sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'high']


# ── Helper functions ───────────────────────────────────────────────────────

def _read_wav_scipy(path: str) -> tuple[int, np.ndarray]:
    """Read a WAV file via scipy.io.wavfile. Returns (sr, data float32)."""
    if not _SCIPY_WAV:
        raise ImportError("scipy.io.wavfile not available")
    sr, data = wavfile.read(path)
    # Normalise to float32 in [-1, 1]
    if data.dtype.kind == 'i':
        max_val = float(2**(data.itemsize * 8 - 1))
        data = data.astype(np.float32) / max_val
    elif data.dtype.kind == 'f':
        data = data.astype(np.float32)
    else:
        raise ValueError(f"Unsupported WAV dtype: {data.dtype}")
    # Ensure mono
    if data.ndim > 1:
        data = data.mean(axis=1)
    return sr, data


def _sane_bpm(tempo: float | None, onset_rate: float | None, beat_confidence: float | None = None) -> float | None:
    """Return a plausible BPM or None.
    - tempo: raw beat_track output
    - onset_rate: onsets per second (200-normalized later)
    - beat_confidence: optional confidence [0-1]
    Fallback order:
      1. If tempo in [30,200] and (beat_confidence is None or beat_confidence > 0.4) → use it
      2. Else if onset_rate available → onset_rate * 60
      3. Else tempo (even if out of range)
    """
    if tempo is None:
        return None
    # Reasonable musical range
    if 30 <= tempo <= 200:
        # If we have confidence, require it to be non-trivial
        if beat_confidence is not None and beat_confidence < 0.3:
            # Low confidence — consider fallback
            if onset_rate is not None and 0.5 <= onset_rate <= 5.0:  # 30-300 BPM equivalent
                return round(onset_rate * 60.0, 2)
        return round(float(tempo), 2)
    # Out of range — try onset_rate proxy
    if onset_rate is not None and 0.5 <= onset_rate <= 5.0:
        return round(onset_rate * 60.0, 2)
    # Last resort: return clamped tempo
    return round(float(tempo), 2)

def _onset_density(rms_frames: np.ndarray, sr: int, hop_length: int = 512) -> float:
    """Simple peak detection on an RMS frame envelope → onset density (Hz)."""
    peaks = (rms_frames[1:-1] > rms_frames[:-2]) & (rms_frames[1:-1] > rms_frames[2:])
    count = int(np.sum(peaks))
    duration = len(rms_frames) * hop_length / sr
    return count / duration if duration > 0 else 0.0


# ── Public API ─────────────────────────────────────────────────────────────

class MIRFeatureExtractor:
    """Extract a unified MIR feature set from an audio file."""

    @staticmethod
    def extract(path: str, use_all: bool = False) -> Dict[str, Any]:
        """Main entry point: analyse file and return feature dict."""
        path = str(Path(path).expanduser().resolve())
        if not Path(path).exists():
            raise FileNotFoundError(path)

        # ── Base: read audio (capped to MAX_ANALYSIS_SECONDS for efficiency) ───
        if _HAS_LIBROSA:
            y, sr = librosa.load(path, sr=None, mono=True, duration=MAX_ANALYSIS_SECONDS)
        else:
            sr, y_int = _read_wav_scipy(path)
            y = y_int.astype(np.float32)
            # Manual crop if longer than cap
            max_samples = int(MAX_ANALYSIS_SECONDS * sr)
            if len(y) > max_samples:
                y = y[:max_samples]

        duration = len(y) / sr
        channels_orig = 1  # forced mono above

        # Basic waveform stats
        peak = float(np.max(np.abs(y)))
        rms = float(np.sqrt(np.mean(y**2)))
        crest = peak / (rms + 1e-12)

        # ── Low-level spectral analysis ────────────────────────────────────
        if _SCIPY_WELCH:
            nperseg = min(2048, len(y))
            f, Pxx = welch(y, sr, nperseg=nperseg)
            power = Pxx  # power spectral density (V^2/Hz)
        else:
            window = np.hanning(len(y))
            mag = np.abs(np.fft.rfft(y * window))
            f = np.fft.rfftfreq(len(y), d=1.0/sr)
            power = mag**2

        total_power = np.sum(power) + 1e-12
        lowlevel: Dict[str, float] = {}
        for (f0, f1), name in zip(BANDS, BAND_NAMES):
            mask = (f >= f0) & (f < f1)
            if np.any(mask):
                band_power = float(np.sum(power[mask]))
                lowlevel[name] = float(round(band_power / total_power, 4))
            else:
                lowlevel[name] = 0.0

        centroid = np.sum(f * power) / total_power
        bandwidth = np.sqrt(np.sum((f - centroid)**2 * power) / total_power)
        lowlevel['spectral_centroid_hz'] = round(float(centroid), 2)
        lowlevel['spectral_bandwidth_hz'] = round(float(bandwidth), 2)
        lowlevel['crest_factor'] = round(crest, 2)
        lowlevel['rms_db'] = round(20 * np.log10(rms + 1e-12), 2)
        lowlevel['peak_db'] = round(20 * np.log10(peak + 1e-12), 2)

        # ── Onset envelope & density ──────────────────────────────────────
        hop = 512
        onset_density_val = 0.0
        onset_list: List[float] = []
        if _HAS_LIBROSA:
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
            onset_times = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr,
                                                     hop_length=hop, units='time')
            onset_density_val = len(onset_times) / duration if duration else 0.0
            onset_list = onset_times.tolist()
        else:
            # Simple RMS‑based peak detection on non‑overlapping frames
            if len(y) > hop:
                trim = (len(y) // hop) * hop
                frames = y[:trim].reshape(-1, hop)
                frame_rms = np.sqrt(np.mean(frames**2, axis=1))
            else:
                frame_rms = np.array([rms])
            onset_density_val = _onset_density(frame_rms, sr, hop)

        # Capture onset rate (Hz) for BPM fallback
        onset_rate_hz = onset_density_val

        # ── Mid‑level: tempo, key ──────────────────────────────────────────
        midlevel: Dict[str, Any] = {}

        if _HAS_LIBROSA:
            try:
                tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop)
                midlevel['bpm'] = _sane_bpm(tempo.item() if tempo is not None else None,
                                            onset_rate_hz, beat_confidence=None)
            except Exception:
                midlevel['bpm'] = None
            try:
                chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
                chroma_avg = np.mean(chroma, axis=1)
                key_idx = int(np.argmax(chroma_avg))
                key_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
                midlevel['key'] = key_names[key_idx]
            except Exception:
                midlevel['key'] = None

        elif _HAS_ESSENTIA:
            try:
                rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
                _, _, tempo, beat_confidence, _ = rhythm_extractor(y)
                # beat_confidence is an array; take mean for a single value
                bc = float(np.mean(beat_confidence))
                midlevel['beat_confidence'] = round(bc, 3)
                midlevel['bpm'] = _sane_bpm(tempo.item() if tempo is not None else None,
                                            onset_rate_hz, beat_confidence=bc)
            except Exception as e:
                midlevel['bpm'] = None
                midlevel['beat_confidence'] = None
                midlevel['_rhythm_error'] = str(e)
            try:
                key_extractor = es.KeyExtractor()
                key, scale, strength = key_extractor(y)
                # key is already a string (e.g. "C", "G#") in recent Essentia versions
                # scale: 1=major, 2=minor, else None
                midlevel['key'] = str(key) if key else None
                midlevel['scale'] = 'major' if scale == 1 else 'minor' if scale == 2 else None
                midlevel['key_strength'] = round(float(strength), 3)
            except Exception as e:
                midlevel['key'] = None
                midlevel['scale'] = None
                midlevel['key_strength'] = None
                midlevel['_key_error'] = str(e)

        # ── High‑level: tags, genre, mood ───────────────────────────────────
        highlevel: Dict[str, Any] = {}
        if _HAS_MUSICNN:
            try:
                tags, _ = _musicnn_extractor(path, model='MSD_musicnn', top_n=5)
                highlevel['tags'] = {t: float(s) for t, s in tags}
            except Exception:
                highlevel['tags'] = {}
        elif _HAS_ESSENTIA:
            try:
                genre_extractor = es.GenreTinyCNN()
                genres = genre_extractor(y)
                highlevel['genres'] = [(str(g), float(p)) for g, p in genres[:3]]
            except Exception:
                highlevel['genres'] = []
            highlevel['tags'] = {}  # musicnn not present, leave empty
        else:
            highlevel['tags'] = {}

        # ── Derived & combined fields ───────────────────────────────────────
        derived = {
            'onset_density_hz': round(onset_density_val, 2),
            'source_onsets_count': len(onset_list),
        }

        # ── Sources record ─────────────────────────────────────────────────
        sources = {
            'librosa': _HAS_LIBROSA,
            'madmom': _HAS_MADMOM,
            'essentia': _HAS_ESSENTIA,
            'musicnn': _HAS_MUSICNN,
        }

        # ── Assemble final profile ─────────────────────────────────────────
        profile = {
            'metadata': {
                'filename': Path(path).name,
                'duration_s': round(duration, 3),
                'sample_rate': sr,
                'channels': channels_orig,
                'peak_db': round(20*np.log10(peak+1e-12), 2),
                'rms_db': round(20*np.log10(rms+1e-12), 2),
                'crest_factor': round(crest, 2),
            },
            'lowlevel': lowlevel,
            'midlevel': {k: (round(v, 2) if isinstance(v, float) else v) for k, v in midlevel.items()},
            'highlevel': highlevel,
            'derived': derived,
            'sources': sources,
        }

        # ── Optional: full Essentia MusicExtractor pool ───────────────────────
        if use_all and _HAS_ESSENTIA:
            try:
                me = es.MusicExtractor(
                    lowlevelStats=['mean', 'stdev'],
                    rhythmStats=['mean'],
                    tonalStats=['mean'],
                    highlevel=[],
                )
                pool, _pool_frames = me(y)
                # Flatten every *scalar* descriptor into a flat dict
                essentia_features: Dict[str, float] = {}
                for name in pool.descriptorNames():
                    val = pool[name]
                    # Essentia returns vectors for some descriptors; skip non-scalars
                    if isinstance(val, (float, int, np.floating, np.integer)):
                        essentia_features[name] = float(val)
                    elif isinstance(val, np.ndarray) and val.size == 1:
                        essentia_features[name] = float(val.item())
                    # vectors/multi-dim descriptors are skipped for now
                profile['essentia_features'] = essentia_features
                profile['sources']['essentia_pool'] = True
            except Exception as e:
                profile['essentia_features'] = {}
                profile['sources']['essentia_pool'] = False
                profile['essentia_error'] = str(e)

        return profile

    @staticmethod
    def profile_to_seed(profile: Dict[str, Any], length: int = 8) -> str:
        """Derive a deterministic short hex seed from a feature profile."""
        canonical = json.dumps(profile, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        h = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return h[:length]

    @staticmethod
    def profile_hash(profile: Dict[str, Any]) -> str:
        """Full 64‑char hex hash of profile."""
        canonical = json.dumps(profile, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
