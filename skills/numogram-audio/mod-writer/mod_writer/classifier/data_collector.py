"""Balanced synthetic dataset generator — Phase 4.1.

Extends the original Phase 3.1 collector with multi-zone balancing.
Generates MOD files, renders to WAV, extracts MIR features, saves NPZ.
"""

import sys
import os
from pathlib import Path
import json
import tempfile
import hashlib
import numpy as np

# ── Make sibling audio-renderer importable ────────────────────────────────────
# data_collector lives in:
#   ~/.hermes/skills/numogram-audio/mod-writer/mod_writer/classifier/
# The audio-renderer skill is a sibling directory at
#   ~/.hermes/skills/numogram-audio/audio-renderer
_this_file = Path(__file__).resolve()
_skill_root = _this_file.parent.parent.parent  # classifier/ → mod_writer/ → mod-writer/
_audio_renderer_path = _skill_root.parent / "audio-renderer"
if str(_audio_renderer_path) not in sys.path:
    sys.path.insert(0, str(_audio_renderer_path))

from renderer import render_mod_to_wav  # audio-renderer exposes this

# Local mod-writer packages
sys.path.insert(0, str(_skill_root))
from mod_writer.song import SongBuilder
from mod_writer.mir_profiler import MIRFeatureExtractor


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mod_to_bytes(mod_writer) -> bytes:
    out = bytearray()
    out.extend(mod_writer.pack_header())
    for pat in mod_writer.patterns:
        out.extend(pat.pack())
    for samp in mod_writer.samples:
        out.extend(samp.data)
    return bytes(out)


def _digital_root(n: int) -> int:
    dr = sum(int(d) for d in str(n)) % 9
    return 9 if dr == 0 else dr


def _aq_candidates_for_zone(zone: int, count: int, start_k: int = 0):
    """Yield `count` AQ integers whose digital root equals `zone`."""
    yielded = 0
    k = start_k
    while yielded < count:
        if zone == 9:
            aq = 9 * (k + 1)
        else:
            aq = zone + 9 * k
        yield aq
        yielded += 1
        k += 1


def _flatten_features(features: dict) -> np.ndarray:
    """Extract the feature vector for the classifier.

    Base 29-dim from lowlevel/midlevel/metadata. If ``features`` contains
    an ``essentia_features`` dict (produced by MIRFeatureExtractor with
    ``use_all=True``), those numeric scalars are appended in sorted-key order,
    expanding the vector to 60–100+ dimensions.
    """
    KEY_MAP = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6,
        'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
    }
    vec: List[float] = []
    low = features.get('lowlevel', {})
    # Band energies — stored as flat keys in lowlevel (not under 'bands' sub-dict)
    for band_name in ['sub_bass','bass','low_mid','mid','high_mid','high']:
        vec.append(low.get(band_name, 0.0))
    # Timbre features — also flat keys
    vec.append(low.get('spectral_centroid_hz', 0.0) or 0.0)
    vec.append(low.get('spectral_bandwidth_hz', 0.0) or 0.0)
    vec.append(low.get('spectral_rolloff', 0.0) or 0.0)
    vec.append(low.get('dynamic_complexity', 0.0) or 0.0)
    # Rhythm — stored in midlevel
    mid = features.get('midlevel', {})
    vec.append((mid.get('onset_rate') or 0.0) / 200.0)
    vec.append((mid.get('bpm') or 0.0) / 200.0)
    vec.append((mid.get('beat_confidence', 0.0) or 0.0) / 100.0)
    # Key — stored as string like 'F#', not a dict
    key_str = mid.get('key', '')
    key_idx = KEY_MAP.get(key_str, 0)
    key_onehot = [0]*12
    key_onehot[key_idx] = 1
    vec.extend(key_onehot)
    # Scale — stored as string 'major'/'minor' or absent
    scale_val = mid.get('scale')
    if scale_val == 'major':
        vec.extend([1,0,0])
    elif scale_val == 'minor':
        vec.extend([0,1,0])
    else:
        vec.extend([0,0,1])
    # Duration — from metadata
    meta = features.get('metadata', {}) or {}
    dur = meta.get('duration_s') or meta.get('duration') or 0.0
    vec.append(float(dur) / 120.0)

    # Optional: Essentia full-pool features (use_all=True)
    essen = features.get('essentia_features')
    if essen:
        # Deterministic order: sorted keys
        for k in sorted(essen.keys()):
            vec.append(float(essen[k]))

    return np.array(vec, dtype=np.float32)



# ── Public API ─────────────────────────────────────────────────────────────────

def build_dataset(
    output_path: str | None = None,
    zones: list[int] | str = "all",
    seeds_per_zone: int = 100,
    aq_range: range | None = None,
) -> dict:
    """
    Generate a synthetic dataset.

    Parameters
    ----------
    output_path : str | None
        Destination .npz file (default: artifacts/dataset.npz).
    zones : list[int] | "all"
        Target zones 1-9 for balanced multi-zone generation.
        Use ``"all"`` for 1-9, or pass a list like [1,3,6].
    seeds_per_zone : int
        Number of distinct AQ seeds to generate *per zone*.
    aq_range : range | None
        Legacy Phase-3.1 mode. If provided, ignores `zones`/`seeds_per_zone`
        and iterates exactly this integer AQ range (single-zone 1 baseline).

    Returns
    -------
    dict with keys 'X', 'y', 'zones', 'meta'
    """
    if output_path is None:
        output_path = Path(__file__).parent / "artifacts" / "dataset.npz"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"[dataset] Using cached {output_path}")
        cached = np.load(output_path)
        # Backward-compat: Phase 3 caches lack a 'zones' key; recompute from y
        if 'zones' in cached:
            zones_arr = cached['zones']
        else:
            zones_arr = np.array([_digital_root(int(a)) for a in cached['y']], dtype=np.int8)
        return {
            'X': cached['X'],
            'y': cached['y'],
            'zones': zones_arr,
            'meta': json.loads(cached['meta'])
        }


    # Resolve target zones
    if aq_range is not None:
        target_zones = None
        total = len(aq_range)
        print(f"[dataset] Legacy mode: {total} examples from aq_range={aq_range}")
        aq_iter = list(aq_range)
    else:
        if zones == "all":
            target_zones = list(range(1, 10))
        else:
            target_zones = sorted(set(zones))
            invalid = [z for z in target_zones if z not in range(1, 10)]
            if invalid:
                raise ValueError(f"zones must be 1-9; got {invalid}")
        total = seeds_per_zone * len(target_zones)
        print(f"[dataset] Balanced: {seeds_per_zone} seeds × {len(target_zones)} zones = {total} examples")

    mir = MIRFeatureExtractor()
    X_list = []
    y_list = []
    zone_list = []
    failures = []

    idx = 0

    if aq_range is not None:
        # Phase 3.1 baseline: zone 1, aq_iter supplied
        for aq in aq_iter:
            try:
                sb = SongBuilder()
                sb.add_section(zone=1, rows=16, aq_seed=str(aq))
                mod_obj = sb.build(verbose=False)
                mod_bytes = _mod_to_bytes(mod_obj)

                with tempfile.NamedTemporaryFile(suffix=".mod", delete=False) as tmp_mod:
                    tmp_mod.write(mod_bytes)
                    tmp_mod.flush()
                    mod_path = tmp_mod.name

                wav_path = render_mod_to_wav(mod_path)
                feats = mir.extract(wav_path, use_all=False)
                vec = _flatten_features(feats)

                X_list.append(vec)
                y_list.append(int(aq))
                zone_list.append(_digital_root(int(aq)))

                os.unlink(mod_path)
                os.unlink(wav_path)

                idx += 1
                if idx % 20 == 0:
                    print(f"  [{idx}/{total}] done")
            except Exception as e:
                failures.append((int(aq), str(e)))
                if len(failures) <= 3:
                    import traceback; traceback.print_exc()
                continue
    else:
        # Balanced multi-zone generation
        for zone in target_zones:
            for aq in _aq_candidates_for_zone(zone, seeds_per_zone):
                try:
                    sb = SongBuilder()
                    sb.add_section(zone=zone, rows=16, aq_seed=str(aq))
                    mod_obj = sb.build(verbose=False)
                    mod_bytes = _mod_to_bytes(mod_obj)

                    with tempfile.NamedTemporaryFile(suffix=".mod", delete=False) as tmp_mod:
                        tmp_mod.write(mod_bytes)
                        tmp_mod.flush()
                        mod_path = tmp_mod.name

                    wav_path = render_mod_to_wav(mod_path)
                    feats = mir.extract(wav_path, use_all=False)
                    vec = _flatten_features(feats)

                    X_list.append(vec)
                    y_list.append(int(aq))
                    zone_list.append(zone)

                    os.unlink(mod_path)
                    os.unlink(wav_path)

                    idx += 1
                    if idx % 50 == 0:
                        print(f"  [{idx}/{total}] done")
                except Exception as e:
                    failures.append((int(aq), str(e)))
                    if len(failures) <= 3:
                        import traceback; traceback.print_exc()
                    continue

    X = np.stack(X_list, dtype=np.float32) if X_list else np.zeros((0, 29), dtype=np.float32)
    y = np.array(y_list, dtype=np.int16)
    z = np.array(zone_list, dtype=np.int8)

    meta = {
        'n_samples': int(len(y)),
        'n_features': int(X.shape[1]),
        'zones_present': sorted(set(map(int, z))),
        'generator': 'mod-writer balanced synthetic dataset (Phase 4.1)',
        'date': '2026-04-30',
        'failures': failures,
    }

    np.savez_compressed(output_path, X=X, y=y, zones=z, meta=json.dumps(meta))
    print(f"[dataset] Saved X={X.shape}, y={y.shape}, zones={z.shape} → {output_path}")
    if failures:
        print(f"[dataset] {len(failures)} failures (first few shown above)")
    return {'X': X, 'y': y, 'zones': z, 'meta': meta}


def load_dataset(path: str | None = None) -> dict:
    if path is None:
        path = Path(__file__).parent / "artifacts" / "dataset.npz"
    data = np.load(path)
    # Backward-compat: Phase 3 caches lack 'zones'; derive from y
    zones = data['zones'] if 'zones' in data else np.array([_digital_root(int(a)) for a in data['y']], dtype=np.int8)
    # meta stored as JSON string; np.load returns a numpy scalar, convert to Python str
    meta_raw = data['meta']
    if isinstance(meta_raw, np.ndarray) and meta_raw.size == 1:
        meta_str = str(meta_raw.item())
    else:
        meta_str = str(meta_raw)
    return {
        'X': data['X'],
        'y': data['y'],
        'zones': zones,
        'meta': json.loads(meta_str)
    }

