"""Audio renderer — .mod → WAV/OGG + spectrogram + playback.

Uses two backends:
  * soft synth (pure Python): renders in‑memory ModWriter structures directly.
  * ffmpeg conversion: attempts external conversion for compatibility.
"""

from .renderer import render_mod_to_wav as render_via_ffmpeg, wav_to_ogg, generate_spectrogram, play_audio
from .synth    import SoftSynth, render_mod_to_wav as render_via_softsynth, render_mod_to_wav

__all__ = [
    'render_mod_to_wav',          # tries ffmpeg first, falls back to soft synth automatically
    'render_via_ffmpeg',
    'render_via_softsynth',
    'wav_to_ogg',
    'generate_spectrogram',
    'play_audio',
    'SoftSynth',
]
