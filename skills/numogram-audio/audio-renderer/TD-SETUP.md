# TouchDesigner Project Setup — numogram-audio integration

This document describes the minimal TD network required to visualize
numogram-audio output in real-time.

## Network layout (copy-paste into a fresh TD project)

```
[File In DAT]   [File Watch DAT]
      |               |
      v               v
[Table DAT] ←──── (optional merge)
      |
      v
[Movie File In TOP]   [Audio File In CHOP]   [Text TOP]
      |                   |                     |
      +--------[Null TOP]<-+---------------------+
                     |
                     v
              [Output COMP / Container]
```

### Nodes

1. **File In DAT** (`watch_json`)
   - *File*: `/path/to/td_state.json`
   - *Polling*: Enabled, Interval: 1
   - *Cook*: Always

2. **File Watch DAT** (optional, for instant update)
   - *File*: Same `td_state.json`
   - *Callback*: `op('watch_json').par.refresh.pulse()`

3. **Table DAT** (`td_table`)
   - *Script*: ``
     ```python
     # On change from watch_json, populate table columns
     src = op('watch_json')
     if src and src['wav']:
         row = len(this.dict())
         this.appendRow()
         this[row, 'wav'] = src['wav']
         this[row, 'spec'] = src['spectrogram']
         this[row, 'zone'] = src['zone']
         this[row, 'gate'] = src['gate']
         this[row, 'current'] = src['current']
     ```
     ``
   - Or simply reference the DAT directly: `op('watch_json')` is already a table-like structure.

4. **Movie File In TOP** (`spec_top`)
   - *File*: `op('watch_json')[0]['spectrogram']` (expression)
   - *Pre-Fetch*: 1 frame
   - *On Missing File*: Black

5. **Audio File In CHOP** (`audio_chop`)
   - *File*: `op('watch_json')[0]['wav']`
   - *Trim Start*: 0
   - *Length*: 10 (sec) or `-1` for full

6. **Text TOP** (`info_text`)
   - *Text*: `Zone: {zone}  Gate: {gate}  Current: {current}`
   - Use text parameters referencing `watch_json` columns
   - *Font*: monospace (e.g. JetBrains Mono)
   - *Color*: dynamic from zone palette (see below)

7. **Palette mapping**
   - Create a **Table DAT** (`zone_palette`) with columns `zone` (0–9) and `hex`
   - Values from `ZONE_COLOR` in `palettes.py`
   - Use **Lookup DAT** to map `zone` → `hex` → **Color DAT** → drive Text TOP color

## Export / version control

Save the project as `~/TouchDesigner/numogram_audio.toe` and reference it
from `TD_PROJECT_PATH` in `palettes.py`.

---

*Generated 2026-04-29 — Phase 4 complete.*
