"""
Soft synthesizer: renders a ModWriter's in-memory structures to WAV.

Bridges the gap between Hermes generative patterns and auditory perception.
No external dependencies; pure‑Python resampling mixer for 4‑channel .mod‑like data.
"""

import math
import array
import wave
from typing import List, Optional

PAL_CLOCK   = 3546895.0   # Amiga PAL clock (Hz)
DEFAULT_BPM = 125
DEFAULT_SPEED = 6          # ticks per row  (default PT)
OUTPUT_RATE = 44100       # Hz, 16-bit stereo (mono for now)


class Voice:
    __slots__ = ('sample_data', 'sample_rate', 'volume', 'phase', 'increment', 'active')

    def __init__(self):
        self.sample_data: Optional[bytes] = None
        self.sample_rate: float = 0.0
        self.volume: float = 0.0
        self.phase: float = 0.0
        self.increment: float = 0.0
        self.active: bool = False

    def trigger(self, sample_data: bytes, period: int, volume: int) -> None:
        if period == 0 or volume == 0 or not sample_data:
            self.active = False
            return
        self.sample_data = sample_data
        self.sample_rate = PAL_CLOCK / (2.0 * period)
        self.volume = volume / 64.0    # normalise 0.0…1.0
        self.phase = 0.0
        self.increment = self.sample_rate / OUTPUT_RATE
        self.active = True

    def stop(self) -> None:
        self.active = False

    def render(self, nframes: int) -> array.array:
        """Render `nframes` mono 16‑bit signed samples for this voice."""
        out = array.array('h')
        if not self.active or self.sample_data is None:
            out.extend([0] * nframes)
            return out

        data = self.sample_data
        length = len(data)
        phase = self.phase
        inc = self.increment
        vol = self.volume

        for _ in range(nframes):
            if phase >= length:
                self.active = False
                out.append(0)
                continue
            idx = int(phase)
            # 8‑bit unsigned (0‑255) → signed ‑128…127 → 16‑bit centred
            sample8 = data[idx] - 128
            sample16 = int(sample8 * vol * 256)   # *256 gives ≈ full‑scale 16‑bit headroom
            if sample16 > 32767: sample16 = 32767
            if sample16 < -32768: sample16 = -32768
            out.append(sample16)
            phase += inc
        self.phase = phase
        return out


class SoftSynth:
    """4‑voice mixer that walks a ModWriter's order/pattern data."""

    def __init__(self, mod):
        self.mod = mod
        # Build lookup: sample index (1‑based) → raw bytes
        self.samples = {i+1: s.data for i, s in enumerate(mod.samples)}
        self.voices = [Voice() for _ in range(4)]   # MOD = 4 channels

    @staticmethod
    def row_duration(bpm: int, speed: int) -> float:
        """Seconds per row = (2.5 × speed) / BPM."""
        return (2.5 * speed) / bpm

    def render(self, bpm: int = DEFAULT_BPM, speed: int = DEFAULT_SPEED) -> array.array:
        dur   = self.row_duration(bpm, speed)
        fpr   = max(1, int(round(dur * OUTPUT_RATE)))   # frames per row
        total_rows = len(self.mod.orders) * 64
        total_frames = total_rows * fpr
        output = array.array('h', [0] * total_frames)

        # Global row index → (pattern_step, row_in_pattern)
        for grobal_row in range(total_rows):
            pattern_step = grobal_row // 64
            row_in_pat   = grobal_row % 64
            pat_idx      = self.mod.orders[pattern_step]
            pat          = self.mod.patterns[pat_idx]

            # Update channel states from this row's cells
            for ch in range(4):
                period, samp_idx, eff, param = pat.rows[row_in_pat][ch]
                if period != 0 and samp_idx != 0:
                    vol = self.mod.samples[samp_idx-1].volume
                    self.voices[ch].trigger(self.samples[samp_idx], period, vol)
                elif period == 0:
                    self.voices[ch].stop()          # note‑cut

            # Mix all voices for this row
            start = grobal_row * fpr
            for voice in self.voices:
                chunk = voice.render(fpr)
                for i, s in enumerate(chunk):
                    idx = start + i
                    val = output[idx] + s
                    if val > 32767: val = 32767
                    if val < -32768: val = -32768
                    output[idx] = val

        return output

    def write_wav(self, filename: str, bpm: int = DEFAULT_BPM, speed: int = DEFAULT_SPEED) -> None:
        samples = self.render(bpm, speed)
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(OUTPUT_RATE)
            wf.writeframes(samples.tobytes())


def render_mod_to_wav(mod, wav_path: str, **kw) -> str:
    """Render an in‑memory ModWriter to a WAV file (soft‑synth path)."""
    SoftSynth(mod).write_wav(wav_path, **kw)
    return wav_path
