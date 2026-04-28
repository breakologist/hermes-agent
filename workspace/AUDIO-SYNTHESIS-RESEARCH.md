# Audio Synthesis Research Plan — Hermes as Composer

**Context:** Numogram-voices produced WAV examples (44 MB, 85 files) — raw speech synthesis.  
**Pivot:** Expand Hermes' expressive range via **pattern-based music systems** (trackers, live-coding) that suit LLM generation and Numogram topology.

---

## Research Lines

### Line A — Broad Survey (Overview)
**Goal:** Map the landscape of text→music approaches suitable for an LLM agent.  
**Deliverable:** `AUDIO-SYNTHESIS-OPTIONS.md` comparison table (trackers / live-coding / conventional / algorithmic).

**Key questions:**
- What output formats are both LLM-friendly (structured text) and listenable?
- What Python libraries exist to render those formats to audio without heavy DAWs?
- What are the file size / licensing constraints (GitHub-friendly)?
- Which approaches align with Numogram aesthetics (cyclic, gate-based, zone-mapped, syzygy-harmonic)?

**Search queries (10):**
1. Furnace tracker module format specifications
2. Audio tracker pattern sequencing LLM prompt format
3. Pure Data SuperCollider live coding AI integration
4. Text to tracker module neural synthesis
5. Pattern-based music generation LLM
6. Module file format .mod .it .xm specification
7. Real-time audio programming language LLM
8. Tracker music composition automation
9. Visual programming sound synthesis LLM
10. Algorithmic ambient music 2024

---

### Line B — Tracker-First Deep Dive
**Goal:** Determine if tracker modules (Furnace, XM, MOD) can be Hermes' primary music format.  
**Deliverable:** `TRACKER-ANALYSIS.md` with specific library recommendations and file format proposals.

**Why trackers:**
- Grid-based = LLM-friendly (rows × channels × effects)
- Tiny file sizes (kilobytes)
- Built-in limits enforce aesthetic coherence (like poetic forms)
- Can be generated purely with Python (no GUI needed)
- Retromodern / CCRU vibe aligns with Numogram's terminal aesthetic

**Investigations:**
- Furnace: format spec, Python lib (`furnace`?), channel count, effect columns
- MilkyTracker / OpenMPT: .mod / .xm support, sample count limits
- libopenmpt: can we write modules directly?
- Existing tracker generators (e.g., `pytecon`, `echom` — may be defunct)
- Pattern vs pattern → could map Numogram zones to pitches, currents to tempo, gates to effects

---

### Line C — MIDI / Algorithmic Prototype (Proof of Concept)
**Goal:** Fastest path to "music from zones" — not final format, but validation that numogram→music mapping works.  
**Approach:** Generate MIDI files from zone/gate data using `mido` or `python-rtmidi`.

**Concept:**
- Zone (1–9) → pentatonic scale degree (1/2/3/5/6)
- Gate (cumulative) → note velocity or effect (arpeggio direction)
- Syzygy partner → harmonic interval (3rd, 5th, 7th)
- Duration: 2 bars per zone, loop gates as rhythmic pattern

**Output:** `numogram-midi-prototype.py` → `test-zone-5.mid`

**Why:** Tests musical mapping before committing to tracker format complexity.

---

## Additional Lines (post-survey)

### D — Live-Coding Environments (PD / SuperCollider)
- Textual patch generation (Pd [scheme] or SuperCollider [sclang])
- Could Hermes write a `.pd` file or `.scd` file that a human runs live?
- File size: small; but requires runtime (Pd/SC) — acceptable as "score"

### E — Chiptune / Synth Chip Libraries
- `pygame.mixer` / `pygame.sndarray` for simple FM
- `pyfluidsynth` for SoundFont rendering (but SF2 files are large)
- `torch` audio models (latent space traversal) — out of scope (too heavy)

---

## Execution Order

1. **Week 1 (A):** Run web searches, compile `AUDIO-SYNTHESIS-OPTIONS.md`
2. **Week 2 (B):** Based on survey results, deep-dive tracker ecosystem, prototype `tracker-module-generator.py` stub
3. **Week 3 (C):** Build MIDI prototype (parallel with B)
4. **Week 4+:** Evaluate findings, choose primary/secondary formats, integrate with numogram-council or oracle voices

---

## Integration Points

| Format | Wiki location | Skill location | Output path |
|---|---|---|---|
| Tracker modules | `wiki/audio/tracker-modules.md` | `skills/numogram-audio/tracker-generator/` | `wiki/assets/audio/*.mod|.xm` |
| MIDI prototypes | `wiki/audio/midi-prototypes.md` | `skills/numogram-audio/midi-mapper/` | `wiki/assets/audio/*.mid` |
| Live-coding scores | `wiki/audio/live-coding-scores.md` | `skills/numogram-audio/pd-sc/` | `wiki/assets/audio/*.pd|.scd` |
| WAV (compressed) | `wiki/assets/audio/` | (managed by file_coordinator) | `wiki/assets/audio/*.opus` |

---

## Success Criteria

- [ ] Survey doc identifies at least 2 viable Python-native pipelines (one tracker, one algorithmic)
- [ ] Tracker analysis confirms ability to generate playable modules without GUI
- [ ] MIDI prototype demonstrates numogram→melody mapping is listenable
- [ ] All artifacts stay under 100KB per file (GitHub safe)
- [ ] Outputs carry clear Numogram signature (zone-tagged, gate-indexed)

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM generates invalid module binaries | Use high-level Python lib that handles encoding; validate with `openmpt` test |
| Audio quality too poor | Start with simple melodic patterns; avoid complex synthesis |
| File coordination overhead | Extend file_coordinator to handle `.mod|.xm|.mid|.opus` after Phase 2 |
| Scope creep (too many formats) | Pick ONE primary format per research line; defer integration until after survey |

