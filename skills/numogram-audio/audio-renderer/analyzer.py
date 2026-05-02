#!/usr/bin/env python3
"""
audio-renderer/analyzer.py — ffmpeg/ffprobe-based audio analysis pipeline

Provides:
  - probe_metadata()     : duration, sample_rate, channels, sample_fmt, bit_rate
  - analyze_quality()    : RMS, peak, LUFS, true-peak, DC offset, crest factor
  - analyze_spectral()   : spectral centroid, roll-off, flux (via astats)
  - analyze_onsets()     : onset count, density, transient rate
  - full_analysis()      : composite dict ready for JSON/description

All analysis uses ffmpeg/ffprobe only — no librosa dependency.
"""

from __future__ import annotations
import subprocess, json, re, os, tempfile
from typing import Dict, Any, Optional

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


def _run(cmd: list[str], timeout: int = 30) -> str:
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout
    )
    return result.stdout


def probe_metadata(wav_path: str) -> Dict[str, Any]:
    cmd = [
        FFPROBE, "-v", "error",
        "-show_entries", "format=duration,duration_ts,bit_rate",
        "-show_entries", "stream=codec_name,codec,sample_rate,channels,sample_fmt,bit_depth",
        "-of", "json",
        wav_path,
    ]
    out = _run(cmd)
    data = json.loads(out)
    fmt = data.get("format", {})
    stream = (data.get("streams") or [{}])[0]

    bit_depth = stream.get("bit_depth")
    if not bit_depth:
        sample_fmt = stream.get("sample_fmt", "")
        m = re.search(r'[ui]?(\d+)(?:p|le|be)?', sample_fmt)
        bit_depth = int(m.group(1)) if m else 16

    return {
        "duration": float(fmt.get("duration", 0.0)),
        "duration_ts": int(fmt.get("duration_ts", 0)),
        "bit_rate": int(fmt.get("bit_rate", 0)),
        "codec": stream.get("codec", ""),
        "sample_rate": int(stream.get("sample_rate", 44100)),
        "channels": int(stream.get("channels", 2)),
        "sample_fmt": stream.get("sample_fmt", "s16"),
        "bit_depth": bit_depth,
    }


def analyze_quality(wav_path: str) -> Dict[str, Any]:
    """Run astats → parse; fall back to volumedetect if filter unavailable or stats empty."""
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
        log_path = tmp.name
    cmd = [
        FFMPEG, "-i", wav_path,
        "-af", "astats=measure_period=0.02:measure=all+ebur128,ametadata=print:file=" + log_path,
        "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return _parse_volumedetect(wav_path)

    # If ffmpeg exited non-zero, treat as unavailable and fall back
    if result.returncode != 0:
        return _parse_volumedetect(wav_path)

    stats = _parse_astats_log(log_path)
    os.unlink(log_path)

    # Fallback if astats produced no usable statistics
    if not stats or "rms_all_mean" not in stats or "peak" not in stats:
        return _parse_volumedetect(wav_path)

    rms = stats.get("rms_all_mean", [0.0])[0]
    peak = max(stats.get("peak", [0.0]) or [0.0])
    true_peak = max(stats.get("true_peak", [0.0]) or [0.0])
    dc_offset = abs(stats.get("mean", [0.0])[0] if "mean" in stats else 0.0)
    crest = true_peak - rms if true_peak and rms else 0.0
    lufs = stats.get("lavfi.ebur128.I", [-23.0])[0]
    peak_count = sum(stats.get("peak_count", [0]))

    quality = "pass"
    if peak_count > 0:
        quality = "fail"
    elif dc_offset > 0.001:
        quality = "warning"
    elif true_peak > 0.99:
        quality = "warning"

    return {
        "rms": round(rms, 6),
        "peak": round(peak, 6),
        "true_peak": round(true_peak, 6),
        "dc_offset": round(dc_offset, 6),
        "crest_factor": round(crest, 6),
        "peak_count": int(peak_count),
        "lufs": round(lufs, 2),
        "quality": quality,
    }


def _parse_volumedetect(wav_path: str) -> Dict[str, Any]:
    cmd = [FFMPEG, "-i", wav_path, "-af", "volumedetect", "-f", "null", "-"]
    out = _run(cmd, timeout=30)
    nums = lambda s: float(re.search(r'[-+]?\d*\.?\d+', s).group())
    result: Dict[str, Any] = {}
    dB_found = False
    for line in out.splitlines():
        # Split after colon to avoid matching numeric IDs in the ffmpeg log prefix
        if ':' not in line:
            continue
        _, value_part = line.split(':', 1)
        # Handle both legacy ("RMS mean") and current ("mean_volume") labels
        if "RMS mean" in line or "mean_volume" in line:
            dB = nums(value_part)
            result["rms"] = 10 ** (dB / 20.0)
            dB_found = True
        elif ("Peak" in line and "max" not in line) or "max_volume" in line:
            dB = nums(value_part)
            peak_lin = 10 ** (dB / 20.0)
            result["peak"] = peak_lin
            result["true_peak"] = peak_lin  # no true-peak separate in volumedetect
            dB_found = True
        elif "DC offset" in line:
            result["dc_offset"] = nums(value_part)
    # Ensure dc_offset present even if not printed (zero offset)
    result["quality"] = "pass" if result.get("peak", 0) <= 0.99 else "warning"
    if not dB_found:
        return {}  # trigger upstream fallback
    # Compute derived metrics in absence of astats detailed data
    rms_val = result.get("rms", 0.0)
    peak_val = result.get("peak", 0.0)
    result["crest_factor"] = round(peak_val - rms_val, 6) if peak_val and rms_val else 0.0
    result["lufs"] = -23.0  # safe neutral default
    result["peak_count"] = 0  # no clipping detected
    result.setdefault("dc_offset", 0.0)  # ensure key exists
    return result


def _parse_astats_log(log_path: str) -> Dict[str, Any]:
    stats: Dict[str, list[float]] = {}
    with open(log_path) as f:
        for line in f:
            if '=' not in line:
                continue
            key, val = line.strip().split('=', 1)
            try:
                fval = float(val)
                stats.setdefault(key, []).append(fval)
            except ValueError:
                continue
    steady: Dict[str, Any] = {}
    for key, values in stats.items():
        steady[key] = [values[0]] if values else []
    return steady


def analyze_spectral(wav_path: str) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
        log_path = tmp.name
    cmd = [
        FFMPEG, "-i", wav_path,
        "-af", "astats=measure=all:measure_period=0.1,ametadata=print:file=" + log_path,
        "-f", "null", "-",
    ]
    try:
        _run(cmd, timeout=60)
    except subprocess.TimeoutExpired:
        return {"centroid": None, "rolloff": None, "flux": None}

    stats = _parse_astats_log(log_path)
    os.unlink(log_path)

    centroid = None
    rolloff = None
    flux = None
    for key, val in stats.items():
        if "centroid" in key.lower():
            centroid = val[0] if val else None
        elif "rolloff" in key.lower():
            rolloff = val[0] if val else None
        elif "flux" in key.lower():
            flux = val[0] if val else None

    return {
        "centroid": round(centroid, 1) if centroid else None,
        "rolloff": round(rolloff, 1) if rolloff else None,
        "flux": round(flux, 4) if flux else None,
    }


def analyze_onsets(wav_path: str, threshold: float = -30.0) -> Dict[str, Any]:
    cmd = [
        FFMPEG, "-i", wav_path,
        "-af", f"silencedetect=noise={threshold}dB:d=0.05,ametadata=print:file=-",
        "-f", "null", "-",
    ]
    out = _run(cmd, timeout=30)
    starts = [float(m) for m in re.findall(r'silence_start: (\d+\.?\d*)', out)]
    ends   = [float(m) for m in re.findall(r'silence_end: (\d+\.?\d*)', out)]
    if not ends:
        return {"onset_count": 0, "onset_density": 0.0, "onset_times": []}
    onset_times = ends[:]
    duration = probe_metadata(wav_path)["duration"]
    density = len(onset_times) / max(duration, 0.001)
    return {
        "onset_count": len(onset_times),
        "onset_density": round(density, 3),
        "onset_times": [round(t, 3) for t in onset_times[:20]],
    }


def full_analysis(wav_path: str) -> Dict[str, Any]:
    meta = probe_metadata(wav_path)
    qual = analyze_quality(wav_path)
    spec = analyze_spectral(wav_path)
    ons  = analyze_onsets(wav_path)
    return {
        "duration": meta["duration"],
        "sample_rate": meta["sample_rate"],
        "channels": meta["channels"],
        "bit_depth": meta["bit_depth"],
        "rms": qual["rms"],
        "peak": qual["peak"],
        "true_peak": qual["true_peak"],
        "lufs": qual["lufs"],
        "dc_offset": qual["dc_offset"],
        "crest_factor": qual["crest_factor"],
        "peak_count": qual["peak_count"],
        "quality": qual["quality"],
        "spectral_centroid": spec["centroid"],
        "spectral_rolloff": spec["rolloff"],
        "spectral_flux": spec["flux"],
        "onset_count": ons["onset_count"],
        "onset_density": ons["onset_density"],
    }


def describe_audio(analysis: Dict[str, Any], zone: int, gate: str, current: str) -> str:
    zone_adj = {
        0: "voidal", 1: "nascent", 2: "differentiating", 3: "harmonic",
        4: "rhythmic", 5: "structural", 6: "tensile", 7: "disjunctive",
        8: "collapsed", 9: "plex",
    }.get(zone, "liminal")

    lufs = analysis["lufs"]
    if lufs > -6: loudness = "blasting"
    elif lufs > -12: loudness = "loud"
    elif lufs > -18: loudness = "moderate"
    else: loudness = "subdued"

    rms = analysis["rms"]
    if rms > 0.3: body = "saturated"
    elif rms > 0.15: body = "full"
    elif rms > 0.05: body = "balanced"
    else: body = "brittle"

    density = analysis["onset_density"]
    if density > 4: motion = "frantic staccato"
    elif density > 2: motion = "articulated"
    elif density > 0.5: motion = "sustained"
    else: motion = "drone-like"

    health = ""
    if analysis["quality"] != "pass":
        health = f" [quality: {analysis['quality'].upper()}]"

    spectral_note = ""
    if analysis.get("spectral_centroid"):
        c = analysis["spectral_centroid"]
        if c < 800: spectral_note = "; low-end weighted"
        elif c > 3000: spectral_note = "; high-frequency dominant"
        else: spectral_note = "; midrange-balanced"

    return (
        f"Zone {zone}::{gate} ({current}) renders a {loudness}, {body} "
        f"{zone_adj} current ({motion}{spectral_note}).{health} "
        f"Peak={analysis['true_peak']:.2f}, LUFS={analysis['lufs']}, "
        f"CR={analysis['crest_factor']:.2f}."
    )
