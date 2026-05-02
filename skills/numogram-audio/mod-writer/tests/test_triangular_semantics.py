"""
Unit tests for triangular pattern semantics.

Validates that build_patterns_from_grid(triangular=True) produces
the expected pattern length based on max zone, and that zero-padding
behaves correctly.
"""
from mod_writer.composer import ModComposer

def test_triangular_length_simple():
    comp = ModComposer()
    # Add a triad with zones [1,3,6]; max zone = 6 => triangular(6)=21
    comp.add_note(zone=1, gate=0, current='A', row=0, channel=0)
    comp.add_note(zone=3, gate=0, current='A', row=0, channel=1)
    comp.add_note(zone=6, gate=0, current='A', row=0, channel=2)
    pat = comp.build_patterns_from_grid(triangular=True)
    # Triangular(6) = 6*7//2 = 21
    assert len(pat.rows) == 21

def test_triangular_length_cap_at_64():
    comp = ModComposer()
    # Use a high zone to exceed cap. Bypass add_note validation by populating zone_grid directly.
    # Simulate zone=12 (T(12)=78) which exceeds 64-row cap.
    comp.zone_grid[(0, 0)] = {'zone': 12, 'gate': 0, 'current': 'A', 'note': 'C', 'octave': 4}
    pat = comp.build_patterns_from_grid(triangular=True)
    assert len(pat.rows) == 64

def test_triangular_zone_variations():
    comp = ModComposer()
    # Zones [3,6,9] => max=9 => T(9)=45
    for z in [3,6,9]:
        comp.add_note(zone=z, gate=0, current='A', row=0, channel=0)
    pat = comp.build_patterns_from_grid(triangular=True)
    assert len(pat.rows) == 45

def test_triangular_fill_missing_cells_zero():
    comp = ModComposer()
    # Add a single note at row 0, channel 0 only, zones=[1]
    comp.add_note(zone=1, gate=0, current='A', row=0, channel=0)
    pat = comp.build_patterns_from_grid(triangular=True)
    # Triangular(1)=1 row, all 4 channels should be zero-filled except (0,0)
    assert len(pat.rows) == 1
    # channel 0 should have note data (non-zero period)
    period, sample, effect, param = pat.rows[0][0]
    assert period != 0  # note added
    # Channels 1,2,3 should be zeros
    for ch in [1,2,3]:
        period, sample, effect, param = pat.rows[0][ch]
        assert period == 0 and sample == 0 and effect == 0 and param == 0

def test_triangular_rows_overflow_ignored():
    comp = ModComposer()
    # Add a note at row 100 (beyond length after triangular)
    comp.add_note(zone=2, gate=0, current='A', row=100, channel=0)
    pat = comp.build_patterns_from_grid(triangular=True)
    # With only zone 2 -> T(2)=3 rows. Note at row 100 should be ignored.
    assert len(pat.rows) == 3
    # All cells in these 3 rows should be zero (no note added within range)
    for r in range(3):
        for ch in range(4):
            period, _, _, _ = pat.rows[r][ch]
            assert period == 0

if __name__ == '__main__':
    test_triangular_length_simple()
    test_triangular_length_cap_at_64()
    test_triangular_zone_variations()
    test_triangular_fill_missing_cells_zero()
    test_triangular_rows_overflow_ignored()
    print("All tests passed")
