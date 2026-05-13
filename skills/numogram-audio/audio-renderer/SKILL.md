---
name: audio-renderer
description: "Audio rendering, analysis, and verification for tracker modules. Provides WAV conversion, spectrogram generation, and comprehensive audio quality metrics via ffmpeg/ffprobe."
tags: []
related_skills: []
---
# Audio Renderer — .mod → WAV/OGG + analysis

Bridges the gap between binary module generation and Hermes's sensory apparatus.
Provides programmatic rendering, playback, and visual analysis (spectrograms).

## Capabilities

- **render(mod_path)**: Convert any .mod file to linear PCM WAV using ffmpeg + libopenmpt.
- **compress(wav_path)**: Transcode WAV to OGG (Opus) for storage (lossless→lossy compression).
- **analyze(wav_path)**: Generate PNG spectrogram (frequency vs time) with `showspectrumpic`.
- **play(mod_or_wav)**: Play audio via ffplay or system audio sink.
- **convert_to_midi()**: [future] optionally generate symbolic MIDI from patterns for cross-format analysis
- **waveform_extract()**: [future] extract amplitude envelope for visualization

## Dependencies

- **ffmpeg** compiled with `--enable-libopenmpt` (confirmed present: `ffmpeg -version | grep libopenmpt`)
- Optional: `sox` for additional transforms
- System audio (PulseAudio/Wayland) for playback

## Implementation notes

FFmpeg's libopenmpt decoder automatically handles ProTracker/MOD formats.
Command pattern:
```
ffmpeg -i input.mod -f wav -  # raw PCM to stdout
ffmpeg -i input.mod -vn -acodec libopus output.ogg
ffmpeg -i input.mod -filter_complex "showspectrumpic=...:mode=compact" spectrogram.png
```
All formats are autodetected; no need to specify format explicitly.

## Integration with mod-writer

ModWriter skill will emit modules → this renderer consumes them → pipeline:
generate .mod → render WAV → compress OGG → play/analyze → embed waveform/score in wiki asset.

## Phase 4 — Analysis, Verification, and Description

The `analyzer.py` module provides a comprehensive audio quality analysis pipeline using `ffmpeg` and `ffprobe`. It extracts perceptual features, verifies technical integrity, and generates oracle-ready descriptions.

### Core functions

- `full_analysis(wav_path) → dict` — runs all sub-analyzers and returns a flat JSON-serialisable dict with keys:
  - `duration`, `sample_rate`, `channels`, `bit_depth`
  - `rms`, `peak`, `true_peak`, `dc_offset`
  - `lufs` (integrated loudness, if `ebur128` filter available), else `null`
  - `crest_factor`
  - `spectral_centroid`, `spectral_rolloff`, `spectral_flux` (if `astats` available), else `null`
  - `onset_count`, `onset_density` (onsets per second)
  - `quality` — one of `"pass"`, `"warning"`, `"fail"` (fails on hard clipping or DC offset)
  - `warnings` — list of condition strings (e.g., `"DC offset detected"`, `"clipping detected"`)

- `describe_audio(analysis_dict, zone=None, gate=None, current=None) → str` — produces a one-sentence oracle portrait combining technical metrics with numogram context. Example:
  ```
  Zone 3::6 (A) renders a loud, saturated harmonic current (frantic staccato; high-frequency dominant). Peak=0.98, LUFS=-8.4, CR=1.42. [quality: WARNING]
  ```

### Fallback handling

If the ffmpeg build lacks `astats` or `ebur128` filters, the analyzer gracefully degrades:
- Without `astats`: spectral fields (`spectral_centroid`, `spectral_rolloff`, `spectral_flux`) are set to `null`.
- Without `ebur128`: `lufs` is `null`.
Hard clipping and DC offset detection use simpler `volumedetect` and `sidedetect` filters, which are widely available.

### Integration points

- **mod-writer** — after `--render`, runs `full_analysis()` if `--analyze` flag is set; writes `<wav>_analysis.json`; embeds analysis dict in `--manifest` and `--json` outputs; `--verify` exits non-zero if `quality != "pass"`; `--describe` prints portrait.
- **mod-forensic-analyzer** — uses the same analyzer to assess imported modules; merges analysis into `td_state.json` via `td-watcher.py`.
- **TouchDesigner watcher** — `td-watcher.py` scans for `<base>_analysis.json` sidecar files and merges them into the consolidated `td_state.json` along with `health_color` derived from quality.
- **audio-to-mod-seed** — consumes `full_analysis` output (plus optional RMS band extractions) to infer numogram generation parameters (zone, gate, current, AQ seed, pattern rows) and produce a sibling `.mod` module or a wiki documentation page.

### File tree (updated)

```
audio-renderer/
  __init__.py      # re-exports: render_mod_to_wav, generate_spectrogram, analyze_wav, describe_audio, palettes
  renderer.py      # ffmpeg wrapper + delegates to analyzer for quality metrics
  analyzer.py      # NEW: full_analysis, describe_audio, quality logic
  synth.py         # fallback soft synth (unchanged)
  palettes.py      # zone colors (CCRU), ANSI FG, TD constants, ZONE_PROMPTS
  td-watcher.py    # polls directory, merges analysis sidecars into td_state.json
  SKILL.md         # this document
```

### Verification

```bash
# Generated module quality check
python -m numogram_audio.mod_writer --zone 3 --gate 6 --current A --syzygy \
  --render --analyze --describe --verify --output check.mod

# External import verification (mod-forensic-analyzer)
python -m numogram_audio.mod_forensic_analyzer --input chippy_nr_137_2.mod \
  --render --analyze --describe --verify
```