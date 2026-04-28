"""
Minimal .mod (Protracker) module writer.

Phase 1: valid binary output only.
Phase 2+: numogram mapping layers.
"""

__version__ = '0.1.0'

# Note name → semitone offset from C-4 (middle C = 60)
NOTE_OFFSETS = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
}

# Standard Protracker period table for note C-4 to B-8
# Period = int(8363 * 2**(21.6/12 - semitone/12)) approx
# Precomputed integer periods for semitones 0–(8*12+11)
BASE_PERIODS = [
    1712, 1616, 1524, 1440, 1356, 1280, 1208, 1140, 1076, 1016, 960, 907,  # C-4 to B-4
    856, 808, 762, 720, 678, 640, 604, 570, 538, 508, 480, 453,           # C-5 to B-5
    428, 404, 381, 360, 339, 320, 302, 285, 269, 254, 240, 226,           # C-6 to B-6
    214, 202, 190, 180, 170, 160, 151, 143, 135, 127, 120, 113,           # C-7 to B-7
    107, 101, 95, 90, 85, 80, 76, 71, 67, 63, 60, 57,                      # C-8 to B-8
]

def period_for_note(note_name: str, octave: int = 4) -> int:
    """Return Protracker period for note like 'C' in octave 4."""
    semitone = NOTE_OFFSETS[note_name] + (octave - 4) * 12 + 12  # +12 because base is C-5 period index 0? Actually table starts C-4
    idx = semitone  # index into BASE_PERIODS
    if 0 <= idx < len(BASE_PERIODS):
        return BASE_PERIODS[idx]
    # fallback: clamp
    if idx < 0:
        return BASE_PERIODS[0]
    return BASE_PERIODS[-1]

def note_name_from_zone(zone: int) -> str:
    """Map zone 1–9 to pentatonic degree (C D E G A)."""
    pentatonic = ['C', 'D', 'E', 'G', 'A']
    if zone == 9:
        return 'REST'  # special
    return pentatonic[(zone - 1) % 5]

# Instrument definitions (future: current→instrument mapping)
INSTRUMENTS = {
    'A': {'name': 'square', 'wave': 'square'},
    'B': {'name': 'triangle', 'wave': 'triangle'},
    'C': {'name': 'noise', 'wave': 'noise'},
}
