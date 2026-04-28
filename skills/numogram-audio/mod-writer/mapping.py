"""
Numogram to music mappings.
"""
from typing import Tuple, List


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

def note_and_octave_from_zone(zone: int) -> Tuple[str, int]:
    """Return (note_name, octave) for zone (1-9). Zone 9 returns ('REST', 0)."""
    if zone == 9:
        return ('REST', 0)
    note = ZONE_TO_NOTE[zone]
    octave = ZONE_TO_OCTAVE[zone]
    return (note, octave)


def mod_effect_from_gate(gate: int) -> Tuple[int, int]:
    """
    Map numogram gate (0-36) to Protracker effect command and parameter.
    Returns (effect_cmd, effect_param) as integers.
    Families: 0-9=Arpeggio, 10-19=PortaUp, 20-29=Volume,
              30-31=PatternJump/Break, 32-34=Extended filter,
              35=Syzygy, 36=Entropy.
    """
    if 0 <= gate <= 9:
        # Arpeggio: cmd=0x0, param encodes two offsets as nibbles (symmetric)
        param = ((gate & 0xF) << 4) | (gate & 0xF)
        return (0x0, param)
    elif 10 <= gate <= 19:
        # Porta up: cmd=0x1
        speed = (gate - 10) * 25  # 0,25,50,...,225
        return (0x1, speed)
    elif 20 <= gate <= 29:
        # Set volume: cmd=0xA, param 0-64
        vol = (gate - 20) * 6  # yields 0,6,12,...,54
        return (0xA, vol)
    elif gate == 30:
        # Position jump (order jump): cmd=0xB, param not used meaningfully here
        return (0xB, 0)
    elif gate == 31:
        # Pattern break: cmd=0xB
        return (0xB, 0)
    elif 32 <= gate <= 34:
        # Extended effects: cmd=0xE
        return (0xE, gate - 32)
    elif gate == 35:
        # Syzygy special effect
        return (0xE, 10)
    elif gate == 36:
        # Entropy special effect
        return (0xF, 36)
    else:
        return (0x0, 0)

# Pentatonic adjacency for entropy injection (zone → neighboring zones within pentatonic set)
# Used by composer.inject_entropy()
PENTATONIC_ADJACENCY = {
    1: (2, 5),   # C → D, A
    2: (1, 3),   # D → C, E
    3: (2, 4),   # E → D, G
    4: (3, 5),   # G → E, A
    5: (1, 4),   # A → C, G
    6: (7, 2),   # C (oct5) → D, E (octave‑shifted pentatonic neighbours)
    7: (6, 8),   # D (oct5)
    8: (7, 9),   # E (oct5)  → 9 (rest) allowed
    9: (8, 1, 3, 5, 7),  # REST neighbours (all zones that touch 9 in syzygy graph)
}

def adjacent_pentatonic_zones(zone: int) -> Tuple[int, ...]:
    """Return tuple of adjacent pentatonic zones for entropy substitution."""
    return PENTATONIC_ADJACENCY.get(zone, ())

# Syzygy harmony helpers
def syzygy_partners(zone: int, max_channels: int = 4) -> Tuple[int, ...]:
    """
    Return up to `max_channels` partner zones for triangular harmony.
    Root zone occupies channel 0; partners fill channels 1..N.
    """
    partners = partners_for_zone(zone)
    return partners[:max_channels]

def harmony_channels_for_zone(zone: int, total_channels: int = 4) -> List[int]:
    """
    Given a root zone, return list of channel numbers to use for harmony.
    Channel 0 = root; channels 1+ = partner zones (up to total_channels-1).
    """
    partners = syzygy_partners(zone, max_channels=total_channels-1)
    return [0] + list(range(1, 1+len(partners)))
