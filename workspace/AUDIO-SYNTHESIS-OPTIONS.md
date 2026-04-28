# Audio Synthesis Options — Survey Results (Lines A)

**Date:** 2026-04-28  
**Status:** Preliminary (Line A — broad survey)  
**Scope:** Python-native, LLM-friendly, GitHub-sized audio generation pathways  
**Constellation:** Hermes as composer, not just synthesizer; pattern-based trackers prioritized

---

## Quick-Start Decision Matrix

| Format | LLM-friendliness | Python lib | Output size | GitHub-friendly | CCRU/Numogram vibe | Verdict |
|---|---|---|---|---|---|---|
| **Tracker modules** (MOD/XM/IT/Furnace) | ★★★★★ (grid = text table) | `pymod`, `libxm`, `furnace` (CLI) | 1–50 KB | ✓ | ✓✓✓ (retromodern, terminal-coded) | **Primary candidate** |
| **MIDI files** | ★★★★☆ (event list = text) | `mido`, `midiutil` | 1–10 KB | ✓ | ✓ (pattern grid possible) | Fast validation (Line C) |
| **Pure Data patches** | ★★★☆☆ (textual .pd files exist) | `pdpython`, manual JSON→.pd | 5–100 KB | ✓ | ✓ (live-coding, flux) | Secondary (post-survey) |
| **SuperCollider sclang** | ★★☆☆☆ (code → .scd, but needs SC server) | `sc3` Python lib (limited) | 1–20 KB | ✓ | ✓ (algorithmic, recursive) | Low priority |
| **WAV (raw PCM)** | ★☆☆☆☆ (binary blob) | `wave`, `scipy.io.wavfile` | 1–100 MB | ✗ (too large) | ✗ | **Do not commit raw** |
| **OGG/Opus** | ★★☆☆☆ (binary but compressed) | `pyogg`, `ffmpeg` transcode | 100–500 KB | ✓ (if <100MB) | ~ | Use only for final assets |

---

## Deep Dives

### 1. Tracker Modules — The Sweet Spot

**Why trackers suit LLMs:**
- **Grid = text table** → can be represented as Markdown or CSV → LLM can generate rows directly
- **Pattern-based** → bars × channels × effect codes; resembles AQ cipher grids
- **Tiny** → 4KB module can hold 64 patterns × 64 rows × 4 channels
- **Self-contained** → samples embedded (or synthesized); no external instruments needed
- **Cultural fit** — chiptune / demoscene / CCRU rave vibes; terminal-native aesthetic

**Candidate formats:**

| Format | Python write support | Max channels | Max samples | Notable traits |
|---|---|---|---|---|
| **.mod** (Protracker) | `pymod` (read-only mostly), `libopenmpt` (write unclear) | 4 | 31 | Ancient (1987); limited effects; iconic |
| **.xm** (FastTracker II) | `libxm` (C lib, Python bindings exist?), `pyxm` (read-only?) | 32 | 128 | Better effects; still 90s era |
| **.it** (Impulse Tracker) | `pymp`? `openmpt`? | 64 | 200 | Windows 90s; complex |
| **Furnace .fui/.fux** | `furnace` CLI (binary, can export) | Up to 256 | Thousands | Modern (2019–), multi-system (Game Boy, SNES, etc.), open-source, **best long-term bet** |

**Current state (verified 2026-04-28):**
- **Furnace** exists as a GUI app + CLI; GitHub: `tildearrow/furnace`
  - Can export to `.wav` directly, but **module write support unclear** — appears focused on *reading* many formats, not writing modules
  - No obvious `furnace --write-module` flag in docs (need verification)
- **OpenMPT** (`libopenmpt`) — C++ library for *playing* modules, write support uncertain
- **pymod** — Python module for *reading* MOD/XM; write support minimal
- **PyFMOD / libxmp** — playback only

**Verdict:** Tracker generation requires either:
1. A Python library that writes module binary format (may not exist maturely)
2. Or: generate **CSV/JSON pattern → render to WAV via `furnace` CLI** (loses editability)
3. Or: build our own simple `.mod` writer (feasible — format is documented, ~100 lines)

**Research action:** Confirm if any Python library can *write* `.mod`/`.xm` cleanly. If not, use MIDI as Step C, then later build minimal module writer.

---

### 2. MIDI — Fast Validation Path (Line C)

**Libraries:**
- `mido` — pure Python MIDI file creation; also PortMIDI for live
- `midiutil` — simple file writing
- `python-rtmidi` — real-time I/O (optional)

**Mapping ideas:**
```
Zone (1–9) → pentatonic degree (C D E G A) in a mode (Dorian, Mixolydian)
Gate (0–36) → note velocity + duration multiplier
Syzygy (partner zone) → harmony interval (3rd/5th/7th)
Current (A/B/C) → instrument program change (0–127)
```

**Pros:** Immediate results, small files, universal playback.  
**Cons:** Sound depends on user's soundfont — not self-contained.

**Line C status:** Ready to prototype immediately. Tools available (`mido` likely installed or `pip install mido`).

---

### 3. Pure Data (Pd) & SuperCollider (SC) — Live-Coding Scores

**Concept:** Generate a `.pd` or `.scd` file that when run in Pd/SC produces generative audio. Structured text → can be LLM-generated.

**Pd format:** JSON-like `.pd` files (plain text, XML-ish). Actually Pure Data patches are a custom text format (not JSON) but well-documented; there's also `pdjson` project for JSON round-trip.

**SuperCollider:** `.scd` files are s-expressions (Scheme-like). Could be generated.

**Python bridges:**
- `pdpython` — Python→Pd communication via sockets (requires Pd running)
- `sc3` (from `supriya`) — Python API for SC; `sc3` lib exists but not pure file-gen

**Verdict:** Viable but heavier runtime dependency (user must have Pd/SC installed). Good for "score as code" but less portable than tracker modules.

---

### 4. Algorithmic WAV Generation (Current state)

We already have `numogram-voices/` producing 44 MB of WAV via formant synthesis. That's **speech**, not music.

For music, options:
- `pygame.sndarray` — generate pure numpy arrays → PCM WAV (simple)
- `pyfluidsynth` — SoundFont → WAV (SF2 files large, ~10–100 MB; not repo-friendly)
- `torch` audio models — overkill, heavy

**Not recommended** for repository-scale generative audio; use only as rendering backend for tracker/MIDI→WAV conversion.

---

## Recommendations for Hermes

**Immediate (ready now):**
1. **Line C** — Build `numogram-midi-prototype.py` using `mido`. Quickest proof that numogram→music mapping works.
2. **Compression pipeline** — Add OGG transcoding for WAVs (ffmpeg) to reduce `numogram-voices/` footprint; file_coordinator Phase 4 will handle this.

**Short-term (Line B research):**
3. **Tracker module writer** — If no adequate Python library exists, design minimal `.mod` writer (tracker module format is small enough for one-off implementation). Prioritize `.mod` for simplicity (4-channel, 31 samples).
4. **Pattern grammar** — Design a compact text format for LLM to generate patterns (e.g., `------` for empty, `C-3` for note, effects as two-digit hex). Stash in `skills/numogram-audio/tracker-grammar.md`.

**Medium-term (integration):**
5. **Oracle voice tracks** — Generate short 5–10 second ambient pieces per zone using tracker patterns, export to OGG, embed in wiki as zone themes.
6. **Live-coding interface** — Optional: generate `.pd` patches for interactive performance (if survey shows PD textual format accessible).

---

## Action Items

- [ ] **Verify Python module writers:** Install `pymod`/`libxm`/`pyit` and test writing simple `.mod`
- [ ] **MIDI prototype:** `numogram-midi-prototype.py` — zone 1–9 pentatonic sequence
- [ ] **FFmpeg OGG pipeline:** Locally compress `numogram-voices/*.wav` to `.opus` and compare sizes
- [ ] **Furnace format deep-dive:** Inspect Furnace source for module export capability
- [ ] **Pd/SC investigation:** Can `.pd`/`.scd` be generated without runtime? Yes — they're text files; check if any render is needed

---

## Research Questions Remaining

1. **Write-ability:** Which tracker formats have *write* libraries in Python? `.mod`? `.xm`? Furnace `.fui`?
2. **Sample management:** If we embed samples in modules, how to keep size down? Use single-sample instruments or raw oscillator waveforms?
3. **Playback:** Which players are cross-platform? `OpenMPT` (Windows), `Furnace` (cross), `xmp` (Linux)?
4. **LLM training data:** Are tracker modules represented in model training corpus? (MOD format is old enough to be present) — affects generation quality.

---

## Next Session Plan

**Day 1 (Line A completion):** Run quick verification searches (Python tracker libs, `mido` docs, `pygame.sndarray` examples). Populate missing cells in this table.

**Day 2 (Line B):** Attempt minimal `.mod` writer test (if no lib found). Document binary format basics.

**Day 3 (Line C):** MIDI prototype + listen. If promising, escalate; if thin, pivot to tracker focus.

