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

## Future: Analysis layer

- Onset detection: count note onsets per second → BPM estimate
- Frequency centroid: measure "brightness" per zone/gate
- Gate effectiveness: how many distinct pattern changes per gate/cell
- Harmony coherence RMS of dissonant harmonics

This turns raw audio into structured feedback for oracle self-modification.