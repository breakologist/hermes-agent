"""CLI for mod writer — standalone."""

import sys, os, argparse

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

from writer import ModWriter, Pattern, Sample, period_for_note, note_from_zone
from utils import generate_square_wave, generate_triangle_wave, generate_noise

def main():
    p = argparse.ArgumentParser(description="Generate .mod modules for numogram.")
    p.add_argument('--title', default='Hermes Tracker')
    p.add_argument('--zone', type=int, default=1, help='Zone 1-9')
    p.add_argument('--gate', type=int, default=0, help='Gate 0-36')
    p.add_argument('--current', choices=['A','B','C'], default='A')
    p.add_argument('--output', default='output.mod')
    args = p.parse_args()

    writer = ModWriter(title=args.title[:20])

    samples_cfg = [
        ('square', generate_square_wave(0.15, 440, 8363, 0.7)),
        ('triangle', generate_triangle_wave(0.15, 440, 8363, 0.7)),
        ('noise', generate_noise(0.15, 8363, 0.5)),
    ]
    for name, data in samples_cfg:
        writer.add_sample(Sample(name=name, data=data))

    pat = Pattern()
    note, octave = note_from_zone(args.zone)
    if note != 'REST':
        period = period_for_note(note, octave)
        sample_idx = {'A':1,'B':2,'C':3}[args.current]
        pat.set_cell(row=0, channel=0, period=period, sample=sample_idx)
    writer.add_pattern(pat)

    writer.write(args.output)
    print(f"✓ Written {args.output}")

if __name__ == '__main__':
    main()
