"""
Audio renderer: .mod → WAV/OGG + analysis pipeline.

Provides programmatic rendering, compression, and visual analysis (spectrograms).
Bridges mod writer to Hermes's auditory feedback loop.
"""

import subprocess
import tempfile
import os

__version__ = "0.1"


def render_mod_to_wav(mod_path: str, wav_path: str = None, **kw) -> str:
    """Convert .mod → WAV via ffmpeg (libopenmpt decoder).

    If wav_path is not provided, derives output name by replacing .mod with .wav
    or by using the same base name in the same directory.
    """
    if not os.path.isfile(mod_path):
        raise FileNotFoundError(mod_path)
    if wav_path is None:
        base = os.path.splitext(mod_path)[0]
        wav_path = base + '.wav'
    cmd = ['ffmpeg', '-y', '-i', mod_path]
    if 'duration' in kw and kw['duration']:
        cmd.extend(['-t', str(kw['duration'])])
    cmd.extend(['-f', 'wav', wav_path])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-1000:]}")
    if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
        raise RuntimeError("WAV not produced or empty")
    return wav_path


def wav_to_ogg(wav_path: str, ogg_path: str = None, quality: str = '6') -> str:
    """Compress WAV to OGG Vorbis/Opus for storage."""
    if ogg_path is None:
        base = os.path.splitext(wav_path)[0]
        ogg_path = base + '.ogg'
    cmd = ['ffmpeg', '-y', '-i', wav_path, '-c:a', 'libopus', '-b:a', f'{quality}k', ogg_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"OGG encode failed: {result.stderr[-500:]}")
    return ogg_path


def generate_spectrogram(wav_path: str, png_path: str = None, colormap: str = 'viridis', size: str = '800x400') -> str:
    """Generate spectrogram PNG (frequency vs time) using ffmpeg showspectrumpic.

    Colormap options (ffmpeg built-in): viridis, magma, plasma, cool.
    Size format: WIDTHxHEIGHT (e.g. '800x400').
    If png_path is None, replaces .wav with _spec.png.
    """
    if png_path is None:
        base = os.path.splitext(wav_path)[0]
        png_path = base + '_spec.png'
    # showspectrumpic parameters: scale=log (frequency), color=<colormap>, size=<WxH>
    # Note: 'slide' and 'legend' options are not universally available; use size.
    filter_str = f'showspectrumpic=scale=log:color={colormap}:size={size}'
    cmd = [
        'ffmpeg', '-y', '-i', wav_path,
        '-filter_complex', filter_str,
        '-frames:v', '1', png_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Spectrogram generation failed: {result.stderr[-500:]}")
    return png_path


# Analysis (ffmpeg-based) — comprehensive
from analyzer import full_analysis as analyze_wav, describe_audio


# analyze_wav() signature preserved for backward compatibility:
#   analyze_wav(wav_path: str) -> dict with extended metric set
#   returns same keys as full_analysis() (see analyzer.py)
#   embed into manifest or JSON as needed.

# describe_audio(analysis: dict, zone: int, gate: str, current: str) -> str
#   Generates oracle-readable textual portrait.


def play_audio(file_path: str, player: str = 'ffplay') -> None:
    """Play audio file via system player (blocks until finished)."""
    players = {
        'ffplay': ['ffplay', '-autoexit', '-nodisp', file_path],
        'aplay': ['aplay', file_path],
        'pw-play': ['pw-play', file_path],
        'mpg123': ['mpg123', file_path],
    }
    if player not in players:
        raise ValueError(f"Unknown player {player}; known: {list(players)}")
    subprocess.run(players[player], check=True)


# ── Test harness ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: renderer.py <mod_file> [--ogg] [--spec] [--play]")
        sys.exit(1)

    mod = sys.argv[1]
    do_ogg  = '--ogg'  in sys.argv
    do_spec = '--spec' in sys.argv
    do_play = '--play' in sys.argv

    print(f"Rendering {mod}...")
    wav = render_mod_to_wav(mod)
    print(f"  WAV: {wav} ({os.path.getsize(wav)} bytes)")

    if do_spec:
        spec = generate_spectrogram(wav)
        print(f"  Spectrogram: {spec}")

    if do_ogg:
        ogg = wav_to_ogg(wav)
        print(f"  OGG: {ogg} ({os.path.getsize(ogg)} bytes)")

    if do_play:
        print("  Playing via ffplay...")
        play_audio(wav)

    print("Done.")
