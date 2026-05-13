---
name: numogram-oracle-voice
version: 1.0.0
description: Physical modelling synthesis + formant speech → resonator convolution for oracle/game voice design. Replaces clean TTS with controllable formant phoneme synthesis.
author: Etym
agentskills_spec: "1.0"
metadata:
  hermes:
    tags: [audio, synthesis, numogram, roguelike, creative]
    category: creative
    requires_toolsets: [terminal]
---

# Numogram Oracle Voice Engine

Physical modelling synthesis + formant speech → resonator convolution for oracle/game voice design.

## Architecture

```
FORMANT SYNTHESIZER (phoneme-level control)
    ↓
EXCITER PROCESSING (saturation, noise, transients, harmonics)
    ↓
RESONATOR (Karplus-Strong, membrane, plate, bar, tube, self-oscillation)
    ↓
MIXING (convolve, sidechain, ring, vocoder, exciter stack)
    ↓
OUTPUT (zone-characterized oracle voice)
```

## Key Learning: TTS vs Formant Synthesis

**Problem**: Clean TTS (edge-tts, etc.) is too "broadcast" — doesn't excite physical modelling resonators. The resonators need transients, noise, and harmonics to react.

**Solution**: Replace TTS with **formant synthesis** (Plaits/Braids-style). Direct control over:
- F1/F2/F3 formant frequencies → vowel/consonant space
- Glottal pulse train pitch → voice character per zone
- Breathiness → noise level through formants
- Phoneme sequence → controllable speech without TTS dependency

## Mixing Methods — Tested Results

Five methods tested with formant voice + zone resonator. Ranked by effectiveness:

| Method | Verdict | Notes |
|--------|---------|-------|
| **ring_plus_convolve** | BEST overall | Ring mod gives brightness/presence, convolve gives body. Both combined with TTS clarity. |
| **exciter_stack** | BEST saturation | Three parallel exciters (saturated, noise, transient) each convolved separately. Most energy into resonator. |
| **convolve_enhanced** | Good body | Saturated TTS + noise → convolve → high boost (1800Hz, gain 3.5x). Fixes muffled v1. |
| **harmonic_resonance** | Rich | Harmonics up to 4th order, saturated, transient-enhanced, then convolved. |
| **amix (simple)** | WEAK | Just layers signals. Doesn't excite resonator enough. |
| **vocope** | WEAK | TTS spectral envelope → resonator. Good concept, too clean in practice. |
| **sidechain** | WEAK | Resonator swells in gaps. Nice breathing effect but not enough fusion. |

## Exciter Processing Chain

Pre-process formant voice before hitting resonator:

```python
# 1. Saturation — adds harmonics
tts_sat = np.tanh(tts * 2.5)  # drive 2.0-2.5

# 2. Shaped noise — follows speech envelope
noise = np.random.uniform(-1, 1, len(tts)) * 0.06
noise *= speech_envelope  # only where speech exists

# 3. Transient insertion — at speech onsets
# Detect energy difference, insert impulses at peaks

# 4. High-frequency boost — fixes muffled convolution
# Highpass at 1500-2000Hz, gain 3-4x
```

## Formant Phoneme Database

30+ phonemes with Praat-style formant values (F1/F2/F3 in Hz):

**Vowels**: a(730/1090/2440), e(530/1840/2480), i(270/2300/3000), o(570/840/2410), u(300/870/2240)
**Fricatives**: z(300/2000/5000 voiced), s(300/2000/5500 unvoiced), sh(300/1800/3500)
**Plosives**: p/b(200/800), t/d(200/1700), k/g(200/1800)
**Nasals**: m(250/1000), n(250/1500), ng(250/1800)

See `~/numogram-voices/formant_voice.py` for full database.

## Zone Voice Profiles

Each zone has: pitch, formant scale, breathiness, phoneme sequence.

| Zone | Pitch | Scale | Breath | Character |
|------|-------|-------|--------|-----------|
| 0 | 140 | 0.8 | 0.55 | Void whisper, heavily breathy |
| 1 | 180 | 1.0 | 0.25 | Glottal spasm, sharp |
| 2 | 250 | 1.0 | 0.45 | Stuttering, fractured |
| 3 | 200 | 1.2 | 0.20 | Buzz-cutter, noisiest |
| 4 | 120 | 1.1 | 0.20 | Low growl, aggressive |
| 5 | 300 | 1.0 | 0.15 | High hiss, driest |
| 6 | 180 | 0.9 | 0.35 | Static, chewing |
| 7 | 160 | 0.85 | 0.60 | Sigh, breathiest |
| 8 | 150 | 0.9 | 0.45 | Moan, warm |
| 9 | 90 | 1.0 | 0.45 | Grunt, lowest pitch |

## Audio Files

All generated files at `~/numogram-voices/`:
- `zone_0-9_*.wav` — pure resonator sounds (3s each)
- `formant_z{N}_*.wav` — formant synthesis sentences
- `oracle_sentence_z{N}_*_convolved.wav` — oracle voice (formant through resonator)
- `oracle_sentence_z{N}_*_sidechain.wav` — oracle voice (sidechain variant)
- `numogram_traversal.wav` — all 10 zones in sequence (20s)

## Mixing Methods (tested, best to worst)

1. **Convolve enhanced** (BEST): Saturated formant voice → convolved through resonator IR → high-frequency boost restored → mixed with original formant for clarity
2. **Ring + convolve**: Ring mod (presence/brightness) + convolve (body), layered
3. **Exciter stack**: Three exciters (saturated, noisy, transient) each convolved separately then stacked
4. **Sidechain**: Resonator swells in speech gaps — good breathing effect but doesn't trigger resonator enough
5. **Vocoder**: TTS spectral envelope shapes resonator — interesting but muffled
6. **Simple amix**: Two layers, no interaction

## Convolution Recipe

```python
def convolve_enhanced(voice, resonator, ir_length=0.25, high_boost=3.5):
    ir = resonator[:int(ir_length * sr)]  # first 250ms as impulse response
    ir /= np.max(np.abs(ir))
    
    convolved = scipy.signal.fftconvolve(voice, ir, mode='full')[:len(voice)]
    
    # Restore highs (convolution muffles)
    b, a = butter(4, 1800 / (sr/2), btype='high')
    highs = filtfilt(b, a, convolved)
    boosted = convolved + highs * high_boost
    
    # Mix with original for intelligibility
    return boosted * 0.6 + voice * 0.4
```

## Exciter Pre-Processing

Before hitting the resonator, dirty the voice:
- **Saturation**: `np.tanh(voice * 2.5)` — adds harmonics
- **Noise layer**: shaped noise following speech envelope — adds texture
- **Transient injection**: impulse at speech onsets — excites resonator attack
- **Harmonic boost**: generate 2nd-4th harmonics via `sin(pi * voice * h)`

## Zone Voice Profiles

Each zone has unique formant parameters:
- **Pitch**: Zone 0=140Hz, Zone 4=120Hz, Zone 5=300Hz, Zone 9=90Hz
- **Formant scale**: Multiplier on F1/F2/F3 (Zone 3=1.2, Zone 0=0.8)
- **Breathiness**: 0.0 (Zone 5) to 0.5 (Zone 7)
- **Phoneme sequence**: Zone-specific sounds (z→sh for Zone 3, g→r→ae for Zone 4)

## Resonator Types

- **Karplus-Strong** (string): delay line + lowpass feedback. Good for Zone 2, 8, 9.
- **Modal membrane**: multiple modes, drum-like. Zone 1, 5.
- **Plate**: inharmonic partials + noise burst. Zone 3 (buzz-cutter).
- **Bar**: stiff metallic modes. Zone 4 (growl).
- **Tube/waveguide**: odd harmonics, breath noise. Zone 6, 7.
- **Self-oscillation**: barely-there modulated sine. Zone 0 (void).

## Files Created

```
~/numogram-voices/
  synthesize.py          — 10 zone resonators + traversal
  formant_voice.py       — formant synthesizer with phoneme control
  oracle_v3.py           — enhanced mixing methods (exciter processing)
  oracle_sentences.py    — full sentences for all 10 zones
  oracle_mixer.py        — original mixing comparison (5 methods)
  zone_*.wav             — 10 pure resonator sounds
  formant_*.wav          — raw formant synthesis
  oracle_sentence_z*_convolved.wav  — final oracle voices
  oracle_sentence_z*_sidechain.wav  — alternate mixing
```

## Dependencies

- numpy, scipy (synthesis, filtering, convolution)
- ffmpeg (format conversion)
- Optional: edge-tts (if using TTS instead of formant), pydub

## Next Steps

- **Rings/Elements mapping**: Each zone → Mutable Instruments patch parameters
- **hermes-genesis integration**: World state → zone → oracle voice
- **Roguelike**: Ambient sound engine per room/zone
- **Controllable phonemes**: Build sentences dynamically from numogram readings
