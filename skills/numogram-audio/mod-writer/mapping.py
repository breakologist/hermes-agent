"""
Numogram to music mappings.
"""

# Zone (1-9) → pentatonic degree (C major pentatonic: C D E G A)
ZONE_TO_NOTE = {
    1: 'C', 2: 'D', 3: 'E', 4: 'G', 5: 'A',
    6: 'C', 7: 'D', 8: 'E', 9: 'REST'
}

# Octave mapping: zones 1-5 → octave 4, zones 6-8 → octave 5, zone 9 → mute
ZONE_TO_OCTAVE = {
    1: 4, 2: 4, 3: 4, 4: 4, 5: 4,
    6: 5, 7: 5, 8: 5, 9: 4  # 9 = rest (no note)
}

# Gate (0-36) → effect category
# 0-9:   arpeggio pattern (0=off, 1=up, 2=down, 3=random, 4=chord)
# 10-19: pitch slide speed  (10=slow, 19=fast)
# 20-29: volume/tempo      (20=vol0, 29=vol9; or tempo offset)
# 30-36: special / current-coded effects
GATE_TO_EFFECT = {
    **{i: ('ARP', i) for i in range(10)},      # arpeggio type
    **{i: ('SLIDE', i-10) for i in range(10,20)},  # slide speed
    **{i: ('VOL', i-20) for i in range(20,30)},    # volume level 0-9
    30: 'JUMP', 31: 'BREAK', 32: 'C-A', 33: 'C-B', 34: 'C-C',
    35: 'SYZYGY', 36: 'ENTROPY',
}

# Current (A/B/C) → instrument selection (sample index 1/2/3)
CURRENT_TO_INSTRUMENT = {
    'A': 1,  # square
    'B': 2,  # triangle
    'C': 3,  # noise
}

# Syzygy partners for triangle completion (precomputed for zones 1-9)
# Triangular syzygy: center zone + two partners (total three vertices)
SYZYGY_PARTNERS = {
    1: (5, 9),   2: (4, 8),   3: (6, 9),
    4: (2, 7),   5: (1, 6),   6: (3, 5),
    7: (4, 9),   8: (2, 9),   9: (1, 3, 5, 7, 8)  # 9 partners with many
}

def partners_for_zone(zone: int) -> tuple:
    """Return partner zones for triangular syzygy."""
    return SYZYGY_PARTNERS.get(zone, ())

def effect_from_gate(gate: int):
    """Return (effect_code, parameter) for gate value."""
    mapping = GATE_TO_EFFECT.get(gate, ('NONE', 0))
    return mapping
