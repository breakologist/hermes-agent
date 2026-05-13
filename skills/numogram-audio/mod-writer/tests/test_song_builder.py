
import pytest
from mod_writer.song import SongBuilder
from mod_writer.composer import ModComposer

def test_songbuilder_basic_composition(tmp_path):
    """Sanity-check: two-section song builds and writes a single .mod file."""
    db = {
        "title": "TestSong",
        "bpm": 125,
        "sections": [
            {"motif": "Warp", "rows": 16},
            {"motif": "Warp", "rows": 32},
        ],
    }
    builder = SongBuilder()
    builder.from_dict(db)
    output = tmp_path / "test_song.mod"
    builder.write(str(output))
    assert output.exists(), "expected .mod file was not written"

def test_songbuilder_propagates_just_intonation(tmp_path):
    """Just-intonation=True must reach every ModComposer instance."""
    db = {
        "sections": [{"motif": "Warp", "rows": 8}],
    }
    builder = SongBuilder(just_intonation=True)
    builder.from_dict(db)
    # Spy on ModComposer construction
    original_init = ModComposer.__init__
    seen = []
    def spy_init(self, *args, **kwargs):
        seen.append(kwargs.get('just_intonation'))
        return original_init(self, *args, **kwargs)
    ModComposer.__init__ = spy_init
    try:
        builder.write(str(tmp_path / "out.mod"))
        assert all(flag is True for flag in seen), f"not all True: {seen}"
    finally:
        ModComposer.__init__ = original_init
