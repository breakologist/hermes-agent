
import pytest
from mod_writer.composer import ModComposer

def test_just_intonation_overrides_third_and_fifth():
    """Major triad should use 5/4 and 3/2 period ratios for third and fifth."""
    c = ModComposer(just_intonation=True)
    # Use apply_triad_motif to populate; root period at zone 7, root note C4 etc.
    # Warp motif: zone 7, triad usually (C, major, 4) giving root_period for C4
    meta = c.apply_triad_motif(motif="Warp", rows=1, gate=0, current="A", channels=[0,1,2])
    # After apply, zone_grid contains entries. ch1 (third) and ch2 (fifth) should have period_override
    root_entry = c.zone_grid.get((0,0))
    third_entry = c.zone_grid.get((0,1))
    fifth_entry = c.zone_grid.get((0,2))

    assert third_entry is not None and third_entry.get('period_override') is not None
    assert fifth_entry is not None and fifth_entry.get('period_override') is not None

    # Verify third_override and fifth_override follow just ratios
    # We can't easily know root_period base without replicating internal calc,
    # but we can at least check they differ from the default equal-tempered periods
    # (since they are stored in zone_grid, not directly accessible as period)
    # Alternatively, compute expected by following same logic as composer.
    from mod_writer.writer import period_for_note
    # Use meta info to reconstruct expected periods
    root_note, quality, octave = meta['root'], meta['quality'], meta['octave']
    root_period = period_for_note(root_note, octave)
    third_ratio = 5/4 if quality == 'major' else 6/5
    fifth_ratio = 3/2
    expected_third = max(1, int(round(root_period / third_ratio)))
    expected_fifth = max(1, int(round(root_period / fifth_ratio)))

    assert third_entry['period_override'] == expected_third
    assert fifth_entry['period_override'] == expected_fifth

def test_just_intonation_off_leaves_periods_untouched():
    """When just_intonation=False, period_override should be absent."""
    c = ModComposer(just_intonation=False)
    c.apply_triad_motif(motif="Warp", rows=1)
    for r in range(1):
        for ch in range(3):
            entry = c.zone_grid.get((r,ch))
            if entry:
                assert entry.get('period_override') is None
