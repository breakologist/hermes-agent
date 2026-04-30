"""Audio renderer — .mod → WAV/OGG + spectrogram + playback.

Uses two backends:
  * soft synth (pure Python): renders in‑memory ModWriter structures directly.
  * ffmpeg conversion: attempts external conversion for compatibility.
"""

from .renderer import render_mod_to_wav as render_via_ffmpeg, wav_to_ogg, generate_spectrogram, play_audio, analyze_wav
from .synth    import SoftSynth, render_mod_to_wav as render_via_softsynth, render_mod_to_wav
from .palettes import ZONE_COLOR, PALETTES, SYZYGY_COLORS, FFMPEG_COLORMAPS, TD_PROJECT_PATH

__all__ = [
    'render_mod_to_wav',          # tries ffmpeg first, falls back to soft synth automatically
    'render_via_ffmpeg',
    'render_via_softsynth',
    'wav_to_ogg',
    'generate_spectrogram',
    'play_audio',
    'analyze_wav',
    'SoftSynth',
    'ZONE_COLOR',
    'PALETTES',
    'SYZYGY_COLORS',
    'FFMPEG_COLORMAPS',
    'TD_PROJECT_PATH',
]
