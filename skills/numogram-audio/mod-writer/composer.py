"""
ModComposer — high‑level composition layer (Phase 2b/3).

 mirrors midiutil/MIDIFile convenience:
   composer = ModComposer()
   composer.add_note(zone=3, gate=6, current='A', row=0, channel=0)
   composer.apply_syzygy_harmony()
   composer.inject_entropy(rate=0.1)
   composer.constrain_gates_by_aq('CHAOS')
   composer.write_mod('out.mod')
"""

from typing import List, Dict, Tuple, Optional
import random
import hashlib

# Import from sibling modules robustly
import sys, os
DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

from writer import ModWriter, Pattern, Sample, period_for_note
from utils import generate_square_wave, generate_triangle_wave, generate_noise
from mapping import (
    note_and_octave_from_zone,
    mod_effect_from_gate,
    CURRENT_TO_INSTRUMENT,
    SYZYGY_PARTNERS,
    adjacent_pentatonic_zones,
    syzygy_partners,
)


# Pentatonic adjacency for entropy: zone → neighboring zones (within same pentatonic slice)



class ModComposer:
    """Compose tracker modules via an event list, then encode to .mod binary."""

    def __init__(self, title: str = "HermesComposition"):
        self.title = title[:20]
        self.writer = ModWriter(title=self.title)

        # Generate the three base samples once
        self._samples_built = False

        # zone_grid: (row, channel) → dict(zone, gate, current)
        # We aggregate notes before pattern construction
        self.zone_grid: Dict[Tuple[int, int], Dict[str, int]] = {}

        # Track which channels have been used (for ordering)
        self.used_channels = set()

        # Default pattern length (rows) — computed later if triangular
        self.pattern_length: Optional[int] = None

    # ── Sample infrastructure ──────────────────────────────────────────────────

    def _ensure_samples(self):
        """Add square/triangle/noise samples to writer (once)."""
        if self._samples_built:
            return
        samples_cfg = [
            ('square', generate_square_wave(0.15, 440, 8363, 0.7)),
            ('triangle', generate_triangle_wave(0.15, 440, 8363, 0.7)),
            ('noise', generate_noise(0.15, 8363, 0.5)),
        ]
        for wave_name, data in samples_cfg:
            abbr = {'square': 'SQ', 'triangle': 'TR', 'noise': 'NO'}.get(wave_name, wave_name[:2].upper())
            samp_name = f"{abbr}-DEF".ljust(22)
            self.writer.add_sample(Sample(name=samp_name[:22], data=data))
        self._samples_built = True

    # ── Note placement API ────────────────────────────────────────────────────

    def add_note(
        self,
        zone: int,
        gate: int,
        current: str,
        row: int,
        channel: int = 0,
    ):
        """Place a note at (row, channel). Overwrites if same cell filled twice."""
        if not (1 <= zone <= 9):
            raise ValueError(f"zone must be 1-9, got {zone}")
        if not (0 <= gate <= 36):
            raise ValueError(f"gate must be 0-36, got {gate}")
        if current not in ('A', 'B', 'C'):
            raise ValueError(f"current must be A/B/C, got {current}")
        if row < 0:
            raise ValueError(f"row must be ≥ 0, got {row}")
        if not (0 <= channel <= 3):
            raise ValueError(f"channel must be 0-3, got {channel}")

        self.zone_grid[(row, channel)] = {
            'zone': zone,
            'gate': gate,
            'current': current,
        }
        self.used_channels.add(channel)

    def add_sequence(
        self,
        zones: List[int],
        gates: List[int],
        currents: List[str],
        start_row: int = 0,
        channel: int = 0,
    ):
        """Add a sequence of notes with matching-length lists."""
        if not (len(zones) == len(gates) == len(currents)):
            raise ValueError("zones, gates, currents must be same length")
        for i, (z, g, cur) in enumerate(zip(zones, gates, currents)):
            self.add_note(z, g, cur, start_row + i, channel)

    # ── Pattern construction ──────────────────────────────────────────────────

    def _compute_max_row(self) -> int:
        if not self.zone_grid:
            return 0
        return max(r for (r, _) in self.zone_grid.keys()) + 1

    def _fill_missing_cells(self, pattern: Pattern, length: int):
        """Ensure every (row,ch) cell exists (MOD format requires all 4 channels per row)."""
        for row in range(length):
            for ch in range(4):
                if (row, ch) not in self.zone_grid:
                    # Empty cell: period=0 (no note), sample=0, effect=0
                    pattern.set_cell(row=row, channel=ch, period=0, sample=0, effect=0, param=0)

    def build_patterns_from_grid(
        self,
        length: Optional[int] = None,
        triangular: bool = False,
    ) -> Pattern:
        """
        Flatten zone_grid into a single Pattern.
        If triangular=True, length = triangular number of a representative zone.
        """
        if triangular:
            # Use max zone among placed notes, or default to zone 5 (T(5)=15)
            zones_present = [v['zone'] for v in self.zone_grid.values()]
            rep_zone = max(zones_present) if zones_present else 5
            tri_len = rep_zone * (rep_zone + 1) // 2
            length = min(tri_len, 64)  # hard cap at 64 rows for Phase 3
        else:
            length = length or self._compute_max_row()
            length = max(1, length)

        pat = Pattern(rows=length)

        for (row, ch), data in self.zone_grid.items():
            if row >= length:
                # Skip overflow - or could log warning
                continue
            zone = data['zone']
            gate = data['gate']
            current = data['current']

            note, octave = note_and_octave_from_zone(zone)
            sample_idx = CURRENT_TO_INSTRUMENT.get(current, 1)
            eff_cmd, eff_param = mod_effect_from_gate(gate)

            period = period_for_note(note, octave) if note != 'REST' else 0
            pat.set_cell(
                row=row,
                channel=ch,
                period=period,
                sample=sample_idx,
                effect=eff_cmd,
                param=eff_param,
            )

        self._fill_missing_cells(pat, length)
        return pat

    # ── Transformation passes ─────────────────────────────────────────────────

    def apply_syzygy_harmony(self, partner_channels: List[int] = [1, 2, 3]):
        """
        For each note on channel 0, add its syzygy partner notes on partner_channels.
        Partner zones are computed via partners_for_zone(root_zone).
        """
        # Collect existing (row, channel=0) notes
        root_cells = [
            (row, self.zone_grid[(row, 0)])
            for (row, ch) in self.zone_grid if ch == 0
        ]
        for row, data in root_cells:
            root_zone = data['zone']
            gate = data['gate']
            current = data['current']
            partners = syzygy_partners(root_zone)
            for i, pz in enumerate(partners[:len(partner_channels)]):
                ch = partner_channels[i]
                # Overwrite any existing note at that cell (prefer harmony)
                self.zone_grid[(row, ch)] = {
                    'zone': pz,
                    'gate': gate,
                    'current': current,
                }
                self.used_channels.add(ch)

    def inject_entropy(self, rate: float = 0.1, rng_seed: Optional[int] = None):
        """
        With probability `rate`, substitute a note's zone with an adjacent pentatonic zone.
        Adjacency defined by PENTATONIC_ADJACENCY.
        """
        if not (0.0 <= rate <= 1.0):
            raise ValueError(f"entropy rate must be 0-1, got {rate}")
        rng = random.Random(rng_seed)
        modified = 0
        total = len(self.zone_grid)
        for key, data in list(self.zone_grid.items()):
            if rng.random() < rate:
                zone = data['zone']
                adj = adjacent_pentatonic_zones(zone)
                if adj:
                    new_zone = rng.choice(adj)
                    data['zone'] = new_zone
                    modified += 1
        return {'modified': modified, 'total': total, 'rate_applied': rate}

    def constrain_gates_by_aq(self, aq_seed: str):
        """
        Deterministically shuffle gate sequence according to AQ numeric value.
        Algorithm: sum of char codes mod 37 produces base delta; apply cyclic
        shift to every gate value: new_gate = (old_gate + delta) % 37 (capped 0-36).
        """
        # Compute AQ numeric signature
        h = hashlib.sha1(aq_seed.encode()).hexdigest()
        # Use first 8 hex digits as int, then mod 37
        aq_val = int(h[:8], 16) % 37

        delta = aq_val % 37
        for data in self.zone_grid.values():
            orig = data['gate']
            data['gate'] = (orig + delta) % 37
        return {'aq_value': aq_val, 'delta': delta, 'cells': len(self.zone_grid)}

    # ── Output ────────────────────────────────────────────────────────────────

    def _finalise_samples(self):
        """Call once before writing to ensure samples are added."""
        self._ensure_samples()

    def write_mod(self, filename: str):
        """Encode composed grid to a valid .mod file."""
        self._ensure_samples()

        length = self._compute_max_row()
        if length == 0:
            raise ValueError("composer is empty — add_note() before write_mod()")

        triangular = getattr(self, '_triangular', False)
        pat = self.build_patterns_from_grid(length=length, triangular=triangular)
        self.writer.add_pattern(pat)

        self.writer.write(filename)
        return filename

    # Convenience: one‑shot compose with flags
    @classmethod
    def compose(
        cls,
        *,
        zone: int,
        gate: int,
        current: str,
        rows: int = 16,
        title: str = "Compose",
        syzygy: bool = False,
        entropy: Optional[float] = None,
        entropy_seed: Optional[int] = None,
        triangular: bool = False,
        aq_seed: Optional[str] = None,
        output: str = "out.mod",
    ):
        """
        Synthesise a single‑note seed into a full module.
        Creates a linear sequence of `rows` notes with the given zone/gate/current,
        then applies transformation passes.
        """
        comp = cls(title=title)
        # Build linear seed sequence across channel 0
        for r in range(rows):
            comp.add_note(zone, gate, current, row=r, channel=0)

        if syzygy:
            comp.apply_syzygy_harmony()
        if entropy is not None:
            comp.inject_entropy(rate=entropy, rng_seed=entropy_seed)
        if aq_seed:
            comp.constrain_gates_by_aq(aq_seed)
        # triangular flag handled at build time via build_patterns_from_grid call

        comp.write_mod(output)
        return output


# Composer test harness (run directly)
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description="ModComposer CLI — high‑level module generator")
    p.add_argument('--zone', type=int, required=True)
    p.add_argument('--gate', type=int, required=True)
    p.add_argument('--current', choices=['A','B','C'], default='A')
    p.add_argument('--rows', type=int, default=16, help='Number of rows (pattern length)')
    p.add_argument('--title', default='Compose')
    p.add_argument('--output', default='compose.mod')
    p.add_argument('--syzygy', action='store_true', help='Add syzygy harmony on ch1‑3')
    p.add_argument('--entropy', type=float, help='Entropy rate 0‑1')
    p.add_argument('--entropy-seed', type=int, help='Entropy RNG seed')
    p.add_argument('--triangular', action='store_true', help='Pattern length = triangular(zone)')
    p.add_argument('--aq-seed', help='AQ string to constrain gate progression')
    args = p.parse_args()

    ModComposer.compose(
        zone=args.zone,
        gate=args.gate,
        current=args.current,
        rows=args.rows,
        title=args.title,
        syzygy=args.syzygy,
        entropy=args.entropy,
        entropy_seed=args.entropy_seed,
        triangular=args.triangular,
        aq_seed=args.aq_seed,
        output=args.output,
    )
    print(f"✔ Composed {args.output}")
