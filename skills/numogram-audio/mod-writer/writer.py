"""Binary .mod file writer — Protracker M.K. (1084-byte header)."""

import struct
from typing import List, Tuple

# Constants
MOD_MAGIC = b'M.K.'
SAMPLE_COUNT = 31
CHANNEL_COUNT = 4
MAX_ORDERS = 128
SAMPLE_HEADER_SIZE = 30   # bytes per sample entry
SAMPLE_NAME_LEN = 22

# Period table (C-2 to B-8 approx) — index = octave*12 + note_offset
# Using Amiga PAL clock: 3546895 Hz / (2 * (period)) = note freq
# Precomputed:
PERIOD_TABLE = [
    1712, 1616, 1524, 1440, 1356, 1280, 1208, 1140, 1076, 1016,  960,  907,
     856,  808,  762,  720,  678,  640,  604,  570,  538,  508,  480,  453,
     428,  404,  381,  360,  339,  320,  302,  285,  269,  254,  240,  226,
     214,  202,  190,  180,  170,  160,  151,  143,  135,  127,  120,  113,
     107,  101,   95,   90,   85,   80,   76,   71,   67,   63,   60,   57,
      54,   51,   48,   45,   43,   40,   38,   36,   34,   32,   30,   28,
      27,   25,   24,   23,   21,   20,   19,   18,   17,   16,   15,   14,
      13,   12,    0
]

NOTE_OFFSET = {
    'C': 0, 'C#':1, 'Db':1, 'D':2, 'D#':3, 'Eb':3,
    'E':4, 'F':5, 'F#':6, 'Gb':6, 'G':7, 'G#':8, 'Ab':8,
    'A':9, 'A#':10, 'Bb':10, 'B':11,
}

class Sample:
    """31-sample entry, 30 bytes each."""
    __slots__ = ('name','data','finetune','volume','repeat_offset','repeat_length')
    def __init__(self, name: str = '', data: bytes = b''):
        self.name = name[:SAMPLE_NAME_LEN]
        self.data = data
        self.finetune = 0          # -8..+7 stored as 0-15 (signed nibble; we keep 0)
        self.volume = 64          # 0..64, 64=max
        self.repeat_offset = 0    # in words from start of sample
        self.repeat_length = 0    # in words (2*length), 0 = no loop
    def pack(self) -> bytes:
        name_b = self.name.encode('latin1', 'replace')
        name_b = (name_b + b'\x00' * SAMPLE_NAME_LEN)[:SAMPLE_NAME_LEN]
        length_words = len(self.data) // 2  # counts 16-bit words
        return struct.pack(
            '<22s H B B H H',
            name_b,
            length_words & 0xFFFF,
            self.finetune & 0xF,
            self.volume & 0x7F,
            self.repeat_offset & 0xFFFF,
            self.repeat_length & 0xFFFF,
        )

class Pattern:
    """64 rows × CHANNEL_COUNT cells. Each cell 4 bytes."""
    def __init__(self):
        # rows × channels: (period, sample, effect, param)
        self.rows: List[List[Tuple[int,int,int,int]]] = [
            [(0,0,0,0) for _ in range(CHANNEL_COUNT)] for _ in range(64)
        ]
    def set_cell(self, row:int, channel:int, period:int, sample:int=1, effect:int=0, param:int=0):
        if 0 <= row < 64 and 0 <= channel < CHANNEL_COUNT and 1 <= sample <= 31:
            self.rows[row][channel] = (period, sample, effect, param)
    def pack(self) -> bytes:
        out = bytearray()
        for row_vals in self.rows:
            for period, sample, effect, param in row_vals:
                if period == 0 and effect == 0:
                    out.extend(b'\x00\x00\x00\x00')
                else:
                    # Encode: byte1 = sample high(4) | period high(4)
                    #         byte2 = period low(8)
                    #         byte3 = sample low(4) | effect high(4)
                    #         byte4 = effect low(4) | param high(4?) but effect is 0..F, param low nibble
                    period_lo = period & 0xFF
                    period_hi = (period >> 8) & 0x0F
                    sample_hi = (sample >> 4) & 0x0F    # bits 4-7 = sample index high nibble (sample 1-31 => hi=0 or 1? Actually sample index in .mod stored as high 4 bits + low 4 bits separately)
                    sample_lo = sample & 0x0F
                    eff_hi = (effect >> 4) & 0x0F if effect else 0
                    eff_lo = effect & 0x0F if effect else param & 0x0F   # if no effect, param goes to low nibble? Actually if effect==0, nibble4 is effect=0? But cell unused → 0. For empty cell we set all zeros.
                    b1 = (sample_hi << 4) | period_hi
                    b2 = period_lo
                    b3 = (sample_lo << 4) | (eff_hi if effect else 0)
                    b4 = eff_lo
                    out.extend([b1, b2, b3, b4])
        return bytes(out)

class ModWriter:
    """Assembles a valid M.K. 4-channel Protracker module."""
    def __init__(self, title: str = "Untitled"):
        self.title_str = title[:20]
        self.samples: List[Sample] = []
        self.patterns: List[Pattern] = []
        self.orders: List[int] = []
        self.restart_pos = 0   # order index to restart; typically 0
    def add_sample(self, sample: Sample):
        if len(self.samples) < SAMPLE_COUNT:
            self.samples.append(sample)
    def add_pattern(self, pattern: Pattern) -> int:
        idx = len(self.patterns)
        self.patterns.append(pattern)
        self.orders.append(idx)
        return idx
    def pack_header(self) -> bytes:
        # Title (20 bytes, zero-padded)
        t = self.title_str.encode('latin1', 'replace')
        title_bytes = (t[:20] + b'\x00'*20)[:20]

        # Sample headers (31 × 30)
        sample_bytes = b''.join(s.pack() for s in self.samples)
        if len(sample_bytes) < SAMPLE_COUNT * SAMPLE_HEADER_SIZE:
            sample_bytes += b'\x00' * (SAMPLE_COUNT * SAMPLE_HEADER_SIZE - len(sample_bytes))

        # Song length + restart (2 bytes)
        song_len = min(len(self.orders), 128)
        status = struct.pack('BB', song_len, self.restart_pos)

        # Order list (128 bytes)
        order_bytes = bytes(self.orders[:MAX_ORDERS])
        if len(order_bytes) < MAX_ORDERS:
            order_bytes += b'\x00' * (MAX_ORDERS - len(order_bytes))

        # Magic (4 bytes)
        magic = MOD_MAGIC

        return title_bytes + sample_bytes + status + order_bytes + magic

    def write(self, path: str):
        with open(path, 'wb') as fh:
            fh.write(self.pack_header())
            for pat in self.patterns:
                fh.write(pat.pack())
            for s in self.samples:
                fh.write(s.data)

# ── Helpers for generating waveforms ──────────────────────────────────────
def square_wave(frequency: float = 110.0, duration: float = 0.1,
                sample_rate: int = 8000, amplitude: int = 80) -> bytes:
    """Generate 8-bit unsigned square wave samples (simple)."""
    n = int(sample_rate * duration)
    period = sample_rate / frequency
    samples = bytearray()
    for i in range(n):
        t = i / sample_rate
        val = amplitude if (i % period) < (period/2) else 255-amplitude
        samples.append(int(val))
    return bytes(samples)

def triangle_wave(frequency: float = 110.0, duration: float = 0.1,
                  sample_rate: int = 8000, amplitude: int = 80) -> bytes:
    n = int(sample_rate * duration)
    period = sample_rate / frequency
    samples = bytearray()
    for i in range(n):
        phase = (i % period) / period  # 0..1
        # triangle: 0→1 linear up then down, offset to 0-255 range 128±amp
        if phase < 0.5:
            val = 128 + int(amplitude * (4*phase - 1))
        else:
            val = 128 + int(amplitude * (3 - 4*phase))
        samples.append(val)
    return bytes(samples)

def noise_wave(duration: float = 0.1, sample_rate: int = 8000) -> bytes:
    import random
    n = int(sample_rate * duration)
    return bytes(random.getrandbits(8) for _ in range(n))

# ── Numogram mappings ─────────────────────────────────────────────────────
def period_for_note(note: str, octave: int) -> int:
    """Look up Protracker period for note/octave (C-0 = index 0)."""
    offset = NOTE_OFFSET.get(note.upper(), 0)
    idx = octave * 12 + offset
    if idx >= len(PERIOD_TABLE):
        idx = len(PERIOD_TABLE) - 1
    return PERIOD_TABLE[idx]

def note_from_zone(zone: int) -> Tuple[str, int]:
    """Pentatonic mapping: zones 1-8 → notes, zone9 = REST."""
    pentatonic = ['C','D','E','G','A']
    if zone == 9:
        return ('REST', 0)
    note = pentatonic[(zone - 1) % 5]
    octave = 4 if zone <= 5 else 5
    return (note, octave)
