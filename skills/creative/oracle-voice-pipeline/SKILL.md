---
name: oracle-voice-pipeline
version: 2.0.0
description: Physical modelling synthesis + formant speech → resonator convolution. TTS alone is too clean for physical modelling resonators — needs saturation, noise, transients as excitation. Formant synthesis (Plaits/Braids style) is preferred — gives resonators raw excitation that clean TTS cannot.
author: Etym
agentskills_spec: "1.0"
---

# Oracle Voice Pipeline

Generate spoken oracle readings where the voice is filtered through a zone-specific resonator — the terrain colours the speech. Based on physical modelling synthesis (Mutable Instruments Rings/Elements style).

## Architecture

**v1 (simple)**: TEXT → TTS → ZONE RESONATOR → MIX → OUTPUT
**v3 (enhanced)**: TTS → SATURATE + NOISE + TRANSIENTS → RESONATOR CONVOLVE + HIGH BOOST → OUTPUT
**v4 (formant)**: PHONEME SEQUENCE → FORMANT SYNTH → RESONATOR CONVOLVE → OUTPUT (recommended)

See also: `numogram-oracle-voice` skill for formant synthesis details.

## Formant Synthesis (v4 — Best Results)

Direct phoneme synthesis (Plaits/Braids style) gives the resonator more to work with than TTS. Controllable at the parameter level: pitch, formant frequencies (F1/F2/F3), breathiness, phoneme sequence.

```bash
cd ~/numogram-voices
python3 oracle_sentences.py --all      # all 10 zones with sentences
python3 oracle_sentences.py --zone 3   # single zone
python3 formant_voice.py --all         # raw phonemes + vowel sweeps
python3 formant_voice.py --sweep 3     # sweep through vowel space
```

Each zone has a voice profile: pitch (Hz), formant scale, breathiness, and a phoneme sequence that spells a sentence. Zone voices range from Zone 0 (pitch 140, breath 0.55, the void whispers) to Zone 9 (pitch 90, breath 0.45, the pandemonium gate).

### Mixing formant voice with resonator
```bash
python3 oracle_v3.py --zones 2 3 4 --method ring_plus_convolve
python3 oracle_v3.py --compare 3      # test all methods
```

### Zone Sentences (formant voices)
| Zone | Text | Pitch | Breath |
|------|------|-------|--------|
| 0 | "the depths of the void whisper" | 140 | 0.55 |
| 1 | "the gulp the first breath" | 180 | 0.25 |
| 2 | "boundaries break the path fractures" | 250 | 0.45 |
| 3 | "the warp spirals outward the signal exceeds" | 200 | 0.20 |
| 4 | "ancient growl beneath the floor" | 120 | 0.20 |
| 5 | "pressure builds the hiss with spittle" | 300 | 0.15 |
| 6 | "the static chews through the signal" | 180 | 0.35 |
| 7 | "exhale the rise carries you upward" | 160 | 0.60 |
| 8 | "the moan the lullaby the ascent of forgetting" | 150 | 0.45 |
| 9 | "the grunt the pandemonium gate opens" | 90 | 0.45 |

## Critical Finding: TTS vs Formant Synthesis

Clean TTS (edge-tts) is too "broadcast" — doesn't excite physical modelling resonators. The resonators need transients, noise, and harmonics to react. **Formant synthesis** (Plaits/Braids-style) with direct F1/F2/F3 control gives much more interesting results. The raw glottal pulse train through bandpass filters provides the excitation that physical models respond to.

## Quick Start

### 1. Generate Zone Resonator Sounds
```bash
cd ~/numogram-voices
python3 synthesize.py all        # All 10 zones
python3 synthesize.py 3          # Just Zone 3
python3 synthesize.py traversal  # Full 0→9 traversal
```

### 2. Generate TTS Speech
Use the hermes `text_to_speech` tool (edge-tts provider):
```
text_to_speech: "Zone three. The buzz-cutter. The Warp spirals outward."
```
This produces an .ogg file at `~/.hermes/audio_cache/`.

### 3. Mix TTS + Resonator
```bash
cd ~/numogram-voices
TTS="/path/to/tts_output.ogg"

# Convert TTS to wav
ffmpeg -y -i "$TTS" -ar 44100 -ac 1 tts_temp.wav

# Get duration
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 tts_temp.wav)

# Trim resonator to match
ffmpeg -y -i zone_3_zx.wav -t "$DUR" -af "volume=0.35" res_temp.wav

# Mix: speech foreground, resonator background texture
ffmpeg -y -i tts_temp.wav -i res_temp.wav \
  -filter_complex "[0]volume=1.0[sp];[1]volume=0.4[res];[sp][res]amix=inputs=2:duration=longest:dropout_transition=3" \
  oracle_output.wav

rm -f tts_temp.wav res_temp.wav
```

## Zone Resonator Mappings

| Zone | Name | Resonator | Character |
|------|------|-----------|-----------|
| 0 | eiaoung | Self-oscillation | Barely there, void whisper |
| 1 | gl | Membrane | Sharp percussive gulp |
| 2 | dt | Karplus-Strong string | Stuttering metallic |
| 3 | zx | Plate | Buzzing, insectoid, sustained |
| 4 | skr | Bar | Low metallic growl |
| 5 | ktt | Membrane | Sharp hiss, high brightness |
| 6 | tch | Tube/bow | Static friction, chewing |
| 7 | pb | Tube/blown | Breathy sigh, lips flapping |
| 8 | mnm | String/blown | Warm moan, lullaby |
| 9 | tn | String/blown | Low grunt, subsonic |

## Mixing — v1 (Simple) and v3 (Enhanced)

### v1: Simple Amix (works but limited)
```bash
ffmpeg -y -i tts.wav -i resonator.wav \
  -filter_complex "[0]volume=1.0[sp];[1]volume=0.4[res];[sp][res]amix=inputs=2:duration=longest:dropout_transition=3" \
  output.wav
```

### v3: Enhanced Excitation (recommended)

**Key finding**: Clean TTS doesn't excite physical modelling resonators enough. The resonator barely reacts because TTS lacks the transients, harmonics, and noise that physical models respond to. Five mixing methods were tested (amix, sidechain, vocoder, ring, convolve) — none worked well with clean TTS.

**Solution**: Pre-process TTS before feeding it to the resonator:

1. **Saturation** — soft-clipping via `tanh(audio * drive)` adds harmonics
2. **Noise injection** — shaped noise following the speech envelope adds texture
3. **Transient insertion** — impulse clicks at speech onsets excite the resonator's attack
4. **Harmonic generation** — add 2nd-4th harmonics for more spectral content
5. **High-frequency restoration** — boost highs on convolved output (convolution kills highs)

**Best methods (tested):**

```python
# exciter_stack — three exciters in parallel, each convolved separately
exciter1 = saturate(tts, drive=2.0)           # harmonics
exciter2 = add_noise_gate(tts, noise_level=0.1)  # texture
exciter3 = add_transients(tts, density=0.25)     # attack

# Each through its own convolution with the resonator IR
# Then stacked: saturated(0.5) + noise(0.2) + transients(0.3)
# High-boosted (1800Hz, gain 3.5) then mixed with original TTS (0.4)
```

```python
# ring_plus_convolve — ring mod for brightness + convolution for body
ring = tts * res                              # metallic presence
conv = convolve(saturate(tts, 1.8), ir)       # resonant body
ring = highpass_boost(ring, 2000Hz, gain=3.0) # restore highs
# Blend: ring(0.3) + conv(0.45) + tts(0.25)
```

```python
# harmonic_resonance — maximum harmonic content for resonator
tts_harm = harmonics_boost(tts, order=4, mix=0.4)
tts_sat = saturate(tts_harm, drive=2.2)
tts_excited = add_transients(tts_sat, density=0.2)
conv = convolve(tts_excited, ir)
# High-boost + blend with original TTS
```

### Mixing Parameters (v1 fallback)
- **Speech volume**: 1.0 (foreground)
- **Resonator volume**: 0.3–0.5 (background texture)
- **dropout_transition**: 3 seconds (smooth ducking when speech pauses)

For more resonator presence (ritual/oracular effect): increase to 0.5–0.7.
For clearer speech (informational): decrease to 0.2–0.3.

## Auto Zone Detection

The `synthesize.py` script can auto-detect zone from:
- A random.org seed: `digital_root(seed)` → zone
- Text AQ value: sum of base-36 letter values → digital root → zone
- Explicit zone number

## Files

- `~/numogram-voices/synthesize.py` — Physical modelling synthesis engine
- `~/numogram-voices/oracle_voice.py` — Pipeline framework (requires edge-tts or espeak for local TTS)
- `~/numogram-voices/zone_N_NAME.wav` — Individual quasiphonic particles
- `~/numogram-voices/numogram_traversal.wav` — Full 0→9 sequence
- `~/numogram-voices/oracle_zoneN.wav` — Mixed oracle voice readings

## Extending

### Add new resonator types
Add a function to `synthesize.py` following the existing pattern:
```python
def my_resonator(freq, dur, decay, bright, sr=SAMPLE_RATE):
    n = int(sr * dur)
    t = np.arange(n) / sr
    # Your synthesis here
    return output
```

### Connect to hermes-genesis
When hermes-genesis generates world events, map the event's zone to a resonator and speak the narrative through it. The world speaks its own description.

### Connect to roguelike
Use zone-specific ambient loops in each dungeon room. The quasiphonic particle IS the room's sound design.
