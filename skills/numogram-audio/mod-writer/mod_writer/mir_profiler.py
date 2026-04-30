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
    import essentia
    import essentia.standard as es
    _HAS_ESSENTIA = True
except ImportError:
    _HAS_ESSENTIA = False

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

        # ── Base: read audio ────────────────────────────────────────────────
        if _HAS_LIBROSA:
            y, sr = librosa.load(path, sr=None, mono=True)
        else:
            sr, y_int = _read_wav_scipy(path)
            y = y_int.astype(np.float32)

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

        # ── Mid‑level: tempo, key ──────────────────────────────────────────
        midlevel: Dict[str, Any] = {}
        if _HAS_LIBROSA:
            try:
                tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env if _HAS_LIBROSA else None,
                                                   sr=sr, hop_length=hop)
                midlevel['bpm'] = round(float(tempo), 2)
                midlevel['beat_confidence'] = None  # could fill later
            except Exception:
                midlevel['bpm'] = None
                midlevel['beat_confidence'] = None
            try:
                chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
                chroma_avg = np.mean(chroma, axis=1)
                key_idx = int(np.argmax(chroma_avg))
                key_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
                midlevel['key'] = key_names[key_idx]
            except Exception:
                midlevel['key'] = None
        else:
            midlevel['bpm'] = None
            midlevel['key'] = None

        # ── High‑level: tags, genre, mood ───────────────────────────────────
        highlevel: Dict[str, Any] = {}
        if _HAS_MUSICNN:
            try:
                tags, _ = _musicnn_extractor(path, model='MSD_musicnn', top_n=5)
                highlevel['tags'] = {t: float(s) for t, s in tags}
            except Exception:
                highlevel['tags'] = {}
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
