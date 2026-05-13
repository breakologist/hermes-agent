"""Tests for MIR feature extraction (Phase 6 — optional deps)."""

import sys
import json
import tempfile
import numpy as np
from pathlib import Path

# Ensure local import
sys.path.insert(0, Path(__file__).parent.parent.as_posix())

from mod_writer.mir_profiler import MIRFeatureExtractor

try:
    from scipy.io import wavfile
    _SCIPY_WAV = True
except ImportError:
    _SCIPY_WAV = False


def _make_test_wav(path: str, duration_s: float = 2.0, sr: int = 44100):
    """Generate a simple test tone WAV (sine + octave)."""
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False, dtype=np.float32)
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    tone += 0.3 * np.sin(2 * np.pi * 220 * t)
    tone = tone / (np.max(np.abs(tone)) + 1e-12)
    data = (tone * 32767).astype(np.int16)
    wavfile.write(path, sr, data)


def test_extract_schema():
    """MIRFeatureExtractor.extract returns a dict with required top-level keys."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    try:
        _make_test_wav(wav_path, duration_s=1.0)
        profile = MIRFeatureExtractor.extract(wav_path)

        for key in ("metadata", "lowlevel", "midlevel", "highlevel", "derived", "sources"):
            assert key in profile, f"Missing top-level key: {key}"

        for subkey in ("duration_s", "sample_rate", "channels", "peak_db", "rms_db"):
            assert subkey in profile["metadata"], f"Missing metadata: {subkey}"

        for band in ("sub_bass", "bass", "low_mid", "mid", "high_mid", "high"):
            assert band in profile["lowlevel"], f"Missing band: {band}"

        for src in ("librosa", "madmom", "essentia", "musicnn"):
            assert isinstance(profile["sources"][src], bool), f"Source flag not bool: {src}"

        print("✓ Schema test passed")
    finally:
        Path(wav_path).unlink(missing_ok=True)


def test_profile_to_seed_deterministic():
    """profile_to_seed returns same hex for identical profile dicts."""
    profile = {
        "metadata": {"duration_s": 1.0, "sample_rate": 44100, "channels": 1, "peak_db": -3, "rms_db": -20, "crest_factor": 17},
        "lowlevel": {"sub_bass": 0.1, "bass": 0.2, "low_mid": 0.1, "mid": 0.1, "high_mid": 0.1, "high": 0.1,
                     "spectral_centroid_hz": 2000, "spectral_bandwidth_hz": 1000, "crest_factor": 17,
                     "rms_db": -20, "peak_db": -3},
        "midlevel": {"bpm": 120.0, "key": "C"},
        "highlevel": {"tags": {}},
        "derived": {"onset_density_hz": 2.5, "source_onsets_count": 5},
        "sources": {"librosa": False, "madmom": False, "essentia": False, "musicnn": False},
    }
    seed1 = MIRFeatureExtractor.profile_to_seed(profile, length=16)
    seed2 = MIRFeatureExtractor.profile_to_seed(profile, length=16)
    assert seed1 == seed2, "Seed not deterministic"
    assert len(seed1) == 16, "Seed length wrong"
    print(f"✓ Deterministic seed: {seed1}")

    profile2 = profile.copy()
    profile2["metadata"] = profile["metadata"].copy()
    profile2["metadata"]["duration_s"] = 2.0
    seed3 = MIRFeatureExtractor.profile_to_seed(profile2, length=16)
    assert seed3 != seed1, "Different profile produced same seed"
    print(f"✓ Different profile: {seed3}")


def test_extract_runs_on_synthetic_wav():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    try:
        _make_test_wav(wav_path, duration_s=0.5)
        profile = MIRFeatureExtractor.extract(wav_path)
        assert profile["metadata"]["duration_s"] > 0
        assert profile["metadata"]["sample_rate"] in (44100, 48000)
        assert 0 <= profile["lowlevel"]["sub_bass"] <= 1
        print("✓ Extraction integration test passed")
    finally:
        Path(wav_path).unlink(missing_ok=True)


def test_missing_file_raises():
    try:
        MIRFeatureExtractor.extract("/nonexistent/path.wav")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        print("✓ Missing file raises error as expected")
    except Exception as e:
        assert False, f"Unexpected exception: {e}"


if __name__ == "__main__":
    test_extract_schema()
    test_profile_to_seed_deterministic()
    test_extract_runs_on_synthetic_wav()
    test_missing_file_raises()
    print("\nAll MIR profiler tests passed.")