"""Binary .mod file writer (Protracker M.K. format)."""

import struct
from typing import List

MOD_MAGIC = b'M.K.'
SAMPLE_COUNT = 31
CHANNEL_COUNT = 4
MAX_ORDERS = 128

PERIOD_TABLE = [
    1712, 1616, 1524, 1440, 1356, 1280, 1208, 1140, 1076, 1016, 960, 907,
    856, 808, 762, 720, 678, 640, 604, 570, 538, 508, 480, 453,
    428, 404, 381, 360, 339, 320, 302, 285, 269, 254, 240, 226,
    214, 202, 190, 180, 170, 160, 151, 143, 135, 127, 120, 113,
    107, 101, 95, 90, 85, 80, 76, 71, 67, 63, 60, 57,
    54, 51, 48, 45, 43, 40, 38, 36, 34, 32, 30, 28,
    27, 25, 24, 23, 21, 20, 19, 18, 17, 16, 15, 14,
    13, 12, 0
]

NOTE_OFFSET = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
}

class Sample:
    def __init__(self, name: str = '', data: bytes = b''):
        self.name = name[:22]
        self.data = data
        self.length_words = len(data) // 2
        self.finetune = 0
        self.volume = 64
        self.repeat_offset = 0
        self.repeat_length = 0
    def pack(self) -> bytes:
        name_b = self.name.encode('latin1', errors='replace')
        if len(name_b) < 22:
            name_b = name_b + b'\x00' * (22 - len(name_b))
        else:
            name_b = name_b[:22]
        return struct.pack(
            '<22s H B B H H',
            name_b,
            self.length_words & 0xFFFF,
            self.finetune & 0xF,
            self.volume & 0x7F,
            self.repeat_offset & 0xFFFF,
            self.repeat_length & 0xFFFF,
        )

class Pattern:
    def __init__(self):
        self.rows: List[List[tuple]] = [
            [(0, 0, 0, 0) for _ in range(CHANNEL_COUNT)]
            for _ in range(64)
        ]
    def set_cell(self, row: int, channel: int, period: int, sample: int = 1,
                 effect: int = 0, param: int = 0):
        if 0 <= row < 64 and 0 <= channel < 4 and 1 <= sample <= 31:
            self.rows[row][channel] = (period, sample, effect, param)
    def pack(self) -> bytes:
        out = bytearray()
        for row in range(64):
            for ch in range(4):
                period, sample, effect, param = self.rows[row][ch]
                if period == 0 and effect == 0:
                    out.extend(b'\x00\x00\x00\x00')
                else:
                    period_lo = period & 0xFF
                    period_hi = (period >> 8) & 0x0F
                    sample_hi = (sample >> 4) & 0x0F
                    sample_lo = sample & 0x0F
                    eff_hi = (effect >> 4) & 0x0F
                    b1 = (sample_hi << 4) | period_hi
                    b2 = period_lo
                    b3 = (sample_lo << 4) | eff_hi
                    b4 = effect & 0x0F if effect else param & 0xF
                    out.extend([b1, b2, b3, b4])
        return bytes(out)

class ModWriter:
    def __init__(self, title: str = "Untitled"):
        self.title_str = title[:20]
        self.samples: List[Sample] = []
        self.patterns: List[Pattern] = []
        self.orders: List[int] = []
        # Header metadata
        self.restart_pos = 0   # pattern to restart on loop (0 = first)
        self.channels = CHANNEL_COUNT
        self.flags = 0
    def add_sample(self, sample: Sample):
        if len(self.samples) < SAMPLE_COUNT:
            self.samples.append(sample)
    def add_pattern(self, pattern: Pattern) -> int:
        idx = len(self.patterns)
        self.patterns.append(pattern)
        self.orders.append(idx)
        return idx
    def pack_header(self) -> bytes:
        # Title
        t = self.title_str.encode('latin1', errors='replace')
        title_bytes = (t[:20] + b'\x00' * 20)[:20]
        # Sample headers
        sample_bytes = b''.join(s.pack() for s in self.samples)
        if len(sample_bytes) < SAMPLE_COUNT * 30:
            sample_bytes += b'\x00' * (SAMPLE_COUNT * 30 - len(sample_bytes))
        # Status bytes: song length, restart, channels, flags
        song_len = len(self.orders) if self.orders else 0
        if song_len > 128:
            song_len = 128
        status = struct.pack('BBBB', song_len, self.restart_pos, self.channels, self.flags)
        # Order list (128 bytes)
        order_bytes = bytes(self.orders[:MAX_ORDERS])
        if len(order_bytes) < MAX_ORDERS:
            order_bytes += b'\x00' * (MAX_ORDERS - len(order_bytes))
        return title_bytes + sample_bytes + status + order_bytes + MOD_MAGIC
    def write(self, path: str):
        with open(path, 'wb') as fh:
            fh.write(self.pack_header())
            for pat in self.patterns:
                fh.write(pat.pack())
            for samp in self.samples:
                fh.write(samp.data)

def period_for_note(note: str, octave: int) -> int:
    offset = NOTE_OFFSET.get(note.upper(), 0)
    idx = (octave * 12) + offset
    if idx >= len(PERIOD_TABLE):
        idx = len(PERIOD_TABLE) - 1
    p = PERIOD_TABLE[idx]
    return p if p != 0 else 1

def note_from_zone(zone: int) -> tuple:
    pentatonic = ['C','D','E','G','A']
    if zone == 9:
        return ('REST', 0)
    note = pentatonic[(zone - 1) % 5]
    octave = 4 if zone <= 5 else 5
    return (note, octave)
