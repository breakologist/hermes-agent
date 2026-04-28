"""CLI for mod writer — full Phase 2 integration.

Generates .mod files with:
- Zone → pentatonic note mapping
- Gate → Protracker effect encoding
- Current → instrument selection
- Metadata embedded in sample names and title (within 20/22-char limits)
"""

import sys
import os
import argparse

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

from writer import ModWriter, Pattern, Sample, period_for_note
from utils import generate_square_wave, generate_triangle_wave, generate_noise
from mapping import (
    note_and_octave_from_zone,
    mod_effect_from_gate,
    CURRENT_TO_INSTRUMENT,
    ZONE_TO_NOTE,
)


def _sample_name(base_wave: str, zone: int, gate: int, current: str) -> str:
    """Build an informative 22-char sample name: WAVE-Zz-Ggg-Cc."""
    # Abbreviate: SQ/TRI/NOI
    abbr = {'square': 'SQ', 'triangle': 'TR', 'noise': 'NO'}.get(base_wave, base_wave[:2].upper())
    name = f"{abbr}-Z{zone}-G{gate}-{current}"
    # Pad/truncate to 22
    if len(name) < 22:
        name = name.ljust(22)
    return name[:22]


def main():
    p = argparse.ArgumentParser(description="Generate .mod modules with numogram mapping.")
    p.add_argument('--title', default='HermesTracker', help='Song title (max 20 chars)')
    p.add_argument('--zone', type=int, default=1, help='Zone (1-9)')
    p.add_argument('--gate', type=int, default=0, help='Gate (0-36)')
    p.add_argument('--current', choices=['A', 'B', 'C'], default='A', help='Current A/B/C')
    p.add_argument('--syzygy', action='store_true', help='Add syzygy harmony on channels 1-3')
    p.add_argument('--syzygy-channels', type=int, default=3, help='Number of harmony channels (default 3)')
    p.add_argument('--entropy', type=float, help='Entropy injection rate 0-1')
    p.add_argument('--entropy-seed', type=int, help='Entropy RNG seed')
    p.add_argument('--triangular', action='store_true', help='Pattern length = triangular number of zone')
    p.add_argument('--aq-seed', help='AQ seed string to constrain gate progression')
    p.add_argument('--rows', type=int, default=16, help='Base pattern row count (default 16)')
    p.add_argument('--output', default='output.mod', help='Output .mod filename')
    args = p.parse_args()

    # Phase 2b/3: if any advanced flag present, use ModComposer
    advanced = any([
        args.syzygy,
        args.entropy is not None,
        args.triangular,
        args.aq_seed is not None,
    ])
    if advanced:
        from composer import ModComposer
        comp = ModComposer(title=args.title)
        # Build seed sequence across channel 0
        for r in range(args.rows):
            comp.add_note(args.zone, args.gate, args.current, row=r, channel=0)
        if args.syzygy:
            comp.apply_syzygy_harmony(partner_channels=list(range(1, args.syzygy_channels+1)))
        if args.entropy is not None:
            comp.inject_entropy(rate=args.entropy, rng_seed=args.entropy_seed)
        if args.aq_seed:
            comp.constrain_gates_by_aq(args.aq_seed)
        comp._triangular = args.triangular
        comp.write_mod(args.output)
        print(f"✔ Composed {args.output}")
        print(f"  Zone={args.zone} Gate={args.gate} Current={args.current} Rows={args.rows}")
        if args.syzygy:
            print(f"  Syzygy harmony on ch1‑{args.syzygy_channels}")
        if args.entropy is not None:
            print(f"  Entropy rate={args.entropy} seed={args.entropy_seed}")
        if args.triangular:
            print(f"  Triangular pattern length (T({args.zone})={args.zone*(args.zone+1)//2})")
        if args.aq_seed:
            print(f"  AQ‑seeded gate progression: {args.aq_seed}")
        sys.exit(0)


    zone = args.zone
    gate = args.gate
    current = args.current

    # Title encoding: prefix small meta tag to keep within 20 chars
    title_prefix = f"Z{zone}G{gate}{current}"
    raw_title = args.title[: (20 - len(title_prefix) - 1)]  # space for hyphen
    title_str = f"{title_prefix}-{raw_title}" if raw_title else title_prefix[:20]
    title_str = title_str[:20]

    writer = ModWriter(title=title_str)

    # Generate all three base samples, but label them with current context
    samples_cfg = [
        ('square', generate_square_wave(0.15, 440, 8363, 0.7)),
        ('triangle', generate_triangle_wave(0.15, 440, 8363, 0.7)),
        ('noise', generate_noise(0.15, 8363, 0.5)),
    ]
    for wave_name, data in samples_cfg:
        samp_name = _sample_name(wave_name, zone, gate, current)
        writer.add_sample(Sample(name=samp_name, data=data))

    # Build a single pattern row encoding the note + gate effect
    pat = Pattern()
    note, octave = note_and_octave_from_zone(zone)
    sample_idx = CURRENT_TO_INSTRUMENT[current]  # 1,2,3 respectively

    if note != 'REST':
        period = period_for_note(note, octave)
    else:
        period = 0  # rest

    eff_cmd, eff_param = mod_effect_from_gate(gate)

    pat.set_cell(row=0, channel=0, period=period, sample=sample_idx,
                 effect=eff_cmd, param=eff_param)

    writer.add_pattern(pat)
    writer.write(args.output)
    print(f"✓ Written {args.output}")
    print(f"  Title: {title_str}")
    print(f"  Zone={zone} Note={note} Oct={octave} Period={period}")
    print(f"  Current={current} → sample #{sample_idx}")
    print(f"  Gate={gate} → effect 0x{eff_cmd:X} param 0x{eff_param:X}")


if __name__ == '__main__':
    main()
