# TouchDesigner File Watcher — numogram-audio

Watches an output directory for newly generated `.wav` and `_spectrogram.png`
files from `mod-writer` and writes a compact `td_state.json` that TouchDesigner
can consume via **File In DAT** or **File Watch CHOP**.

## Quick start

```bash
python3 td-watcher.py --dir ~/numogram/outputs --poll 2.0
```

The watcher writes `~/numogram/outputs/td_state.json`:

```json
{
  "latest": {
    "wav": "/home/user/numogram/outputs/phase4_test.wav",
    "wav_mtime": 1745678901.123,
    "spectrogramrogram": "/home/user/numogram/outputs/phase4_test_spec.png",
    "mod": "/home/user/numogram/outputs/phase4_test.mod",
    "title": "phase4_test",
    "zone": 3,
    "gate": 6,
    "current": "A",
    "palette": "plasma",
    "timestamp": "2026-04-29T14:32:00"
  },
  "count": 5
}
```

## TouchDesigner setup

1. **File In DAT** → `watch_json`
   Parameters → *File*: `td_state.json`
   Set *Polling* on, *Poll Interval* = 1 s

2. **Movie File In TOP** → Source: `spectrogram` column from `watch_json`
   Use `op('watch_json').par.file` as the file path (or `op('watch_json')[0]['spectrogram']`)

3. **Audio File In CHOP** → Source: `wav` column

4. **Text TOP** → Source: `zone`, `gate`, `current` columns
   Format e.g. `Zone: {zone}  Gate: {gate}  Current: {current}`

5. **Color** → map zone to `ZONE_COLOR` via a Table DAT or expression:
   `pars = ('#1a1a1a','#00d4ff','#ffb300','#00ff9d','#6e6e6e','#9d00ff','#00ffea','#ff003c','#e0aaff','#ffffff')`
   `op('text1').par.color = pars[op('watch_json')[0]['zone']]`

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--dir` | `.` | Directory to watch |
| `--poll` | `2.0` | Poll interval in seconds |
| `--state-file` | `td_state.json` | Output JSON filename |

## Notes

- The watcher only updates `td_state.json` when the newest `.wav` changes (by mtime).
- It merges metadata from the companion `{basename}.json` produced by `mod-writer --json`.
- Designed for local, single-user workflows; for networked setups consider `touchdesigner-mcp` skill.

## Dependencies

Python 3.11+, stdlib only.
