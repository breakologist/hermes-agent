# AGENTS.md — Etym's Agent Instructions v2.0 (2026-04-30)

## Environment
- RTX 3060 (12GB VRAM) — primary local inference via ollama
- Local API: localhost:8080
- Primary model pipeline: free-tier multi-provider council (Google AI Studio Gemini 2.5 Flash, Groq Llama 3.3 70B, OpenRouter models) → `numogram-council` plugin for deliberative reasoning.
- Fallback: direct local models via provider configuration; see `numogram-council-setup` skill.
- Honcho at localhost:8000 (deriver + dialectic). Use for memory/context when available.

---

## Four Currents (expanded)
The agent serves four interconnected domains. Context-switch cleanly between them:

1. **Numogram / AQ** — calculation, pattern analysis, wiki. Use `numogram-calculator`. Reduce everything to zones, currents, gates. Look for triangular syzygies, palindromes, rotational symmetry. The numogram is our native coordinate system — but never force correlations.

2. **Roguelike Architecture** — procedural generation, game design, agent AI. Numogram topology drives the map: zones = rooms, currents = corridors, gates = shortcut doors. Emergence over authorship. Apply to dungeons, cult gardens, generative narratives.

3. **Lore & Worldbuilding** — dense, uncanny, found‑text narrative. Voice: CCRU/Land register meets commit‑message clarity. Use `avoid-ai-writing`, `autonovel`. Document systems where esoterica are *operating systems*, not metaphors.

4. **Audio Alchemy** — synthesis, analysis, MIR, sonification. Generate tracker modules, render to WAV, extract spectral/MIR features, map audio → AQ → zones. Learn music on its own terms first; overlay numogram second. Keep an ear open for what the sound *itself* tells you.

---

## File Locations
- Obsidian vault: `/home/etym/.hermes/obsidian/hermetic/`
- Wiki: `hermetic/wiki/` (index at `hermetic/wiki/index.md`)
- Raw sources: `hermetic/raw/`
- Memory files: `~/.hermes/memories/` (MEMORY.md, USER.md)
- SOUL: `~/.hermes/SOUL.md`
- Config: `~/.hermes/config.yaml`, `~/.hermes/.env`
- Plugins: `~/.hermes/plugins/`
- Skills: `~/.hermes/skills/`
- Monorepo (upstream): `~/.hermes/hermes-agent/` ( NousResearch/hermes-agent )
- Monorepo (fork): `~/.hermes/hermes-agent-fork/` ( breakologist/hermes-agent — for community patches )
- Audio workspace: `mod_writer/classifier/artifacts/`, `audio-renderer/outputs/`
- Plans: `~/.hermes/plans/*.json`

---

## Wiki & Export Pipeline
- Canonical wiki: `~/.hermes/obsidian/hermetic/wiki/` (vault truth)
- Export repo: `~/numogram/docs/wiki/` → GitHub `breakologist/numogram` (public)
- Sync order: vault → export → GitHub (two separate git commits). Never push `/wiki` at GitHub root; only `docs/wiki/` is authoritative.
- Visual assets: `wiki/assets/` (referenced via relative `assets/` paths).
- Duplicate locations: when a wiki page exists in both vault and export, treat vault as canonical; export is a *read‑only mirror* until explicitly updated.

---

## Research Toolchain
When conducting web‑based research (audio synthesis, tracker formats, MIR algorithms, TouchDesigner workflows):
- Prefer `ddgs` CLI if available: `ddgs text -k "…" -m 10 -o json`
- Fallback: `w3m -dump "https://duckduckgo.com/?q=…"` + Python parsing
- HTML parsing: `htmlq` or Python `html.parser`
- Record every query and result snippet in `workspace/` for reproducibility.

---

## Workflow Conventions
- Durable facts → `~/.hermes/memories/MEMORY.md`; user prefs → `USER.md`.
- Wiki first — preserve research in wiki before pruning raw files.
- Prefer existing tools over new dependencies.
- Terminal‑first; GUI optional.
- **Git hygiene:** check history before overwriting tracked files (`git show HEAD~1:path`); commit with descriptive prefixes (`feat(audio): …`, `docs: …`, `fix: …`).

---

## Installed Skills (non‑exhaustive — use when relevant)

### Numogram Core
- `numogram-calculator` — AQ computation, digital root, syzygy lookup, zone mapping
- `aq-dictionary-syzygy-analysis` — dictionary ingestion → syzygy chain analysis
- `numogram-tetralogue-generator` — Square Roundtable deliberation
- `numogram-council` / `numogram-council-orchestrator` — multi‑model council orchestration

### Roguelike / Generative
- `roguelike-auto-explore` — DCSS‑style interest‑driven exploration
- `tree-dungeon-generation` — Brogue DFS accretion
- `numogram-visualization` — SVG/p5.js interactive diagrams
- `tsubuyaki` / `tsubuyaki-oo-gallery` — generative micro‑sketches

### Audio / Music (expanded)
- `numogram-audio/mod-writer` — Protracker `.mod` writer with numogram extensions (v0.6.0+)
- `numogram-audio/audio-renderer` — MOD → WAV, spectrograms, analysis, TouchDesigner state export
- `numogram-audio/audio-to-mod-seed` — audio feature → AQ seed pipeline
- `numogram-audio/mod-forensic-analyzer` — reverse‑engineer existing MODs
- `creative/songwriting-and-ai-music` — Suno‑style lyric + tag → song generation
- `mlops/models/audiocraft` — MusicGen / AudioGen inference
- `numogram-audio/oracle-voice-pipeline` — physical modelling synthesis → formant speech (experimental)

### Visual / Real‑time
- `creative/touchdesigner-mcp` — MCP bridge to TouchDesigner (drive TOPs/CHOPs from JSON state)
- `p5js` / `baoyu-infographic` / `numogram-combinatorial-svg` — procedural graphics
- `manim-numogram` — mathematical animations

### Writing / Quality
- `avoid-ai-writing` — strip AI‑isms, enforce found‑text voice
- `autonovel` / `tetralogue-litprog` — scale narrative with four‑voice structure
- `humanizer` — post‑process for uncannynaturalness

### Meta / Self‑Improvement
- `skill-factory` — auto‑generate skills from task trajectories
- `manual-memory-consolidation` — structured memory maintenance
- `wiki-audit` / `wiki-canonical-synthesis-from-raw` — knowledge‑base hygiene
- `model-assessment-protocol` — benchmark local LLMs (creative vs analytical trade‑offs)

---

## Model Strategy
- **Complex creative / reasoning tasks:** mimo‑v2‑pro via Nous (while trial active), then best available provider (OpenRouter top‑tier, Gemini 2.5 Pro).
- **Deliberative / council work:** Use `numogram-council` plugin — analytical (0.3), balanced (0.7), creative (0.9) modes.
- **Local fallback:** ollama at localhost:8080 (Jackrong‑9B‑distilled for literary tasks, Hermes‑4‑14B for balanced).
- **Cheap / frequent tasks:** lightweight local model for reflections, memory updates, identity nudges.
- **Budget guard:** `evey-cost-guard` plugin — warn at 80 %, block at 100 %.
- **Audio inference:** prefer GPU‑backed models (via `modal-serverless-gpu` or local) for MIR deep taggers if needed.

---

## Self‑Improvement & Maintenance (expanded)

### Skill Factory
After any multi‑step creative or technical workflow (e.g. "generate 10 MOD files → render → analyse → tag → archive"), run `skill-factory` to crystallise it into a reusable skill. Prioritise:
- Audio batch pipelines (`render_all() → analyse_all() → enrich_metadata()`)
- Wiki page generation from structured data (AQ → syzygy → narracter → wiki entry)
- Council orchestration patterns (single‑provider tetralogue, calibration mode)

### Memory Consolidation
- Weekly: `manual-memory-consolidation` to compress session highlights into MEMORY.
- Monthly: audit `~/.hermes/memories/` for stale entries; archive to `log.md`.
- Tag memories with domains (`#audio`, `#numogram`, `#touchdesigner`) for cross‑session recall.

### Council Deliberation
Use `numogram-council` for contested decisions:
- Music theory: "Should just intonation override equal temperament for triad motifs?"
- Technical: "Expand Essentia features now or after baseline training?"
- Creative: "Is the numogram overlay constraining the music or enabling it?"
Always capture the full tetralogue transcript and append it to the relevant wiki page.

### Wiki Hygiene
- Monthly `wiki-audit`: find orphaned pages, broken links, missing tags.
- After any code change: update the corresponding wiki page *in the same session*.
- New feature → new wiki page → link from index → commit vault→export→GitHub *together*.

### Fork & Community Sync
- Active development branch: `breakologist/hermes-agent` (fork of NousResearch/hermes-agent).
- Push feature branches there; open PRs upstream when stable.
- Tag releases locally; GitHub release notes extracted from `RELEASE_v*.md` files.
- Keep `AGENTS.md` and `SOUL.md` in sync between upstream and fork (fork may diverge to include local customisations; mark deltas clearly with `<!-- FORK ONLY -->` comments).

---

## Safety & Style
- Confirm before destructive file ops (unless explicitly automated in a plan).
- Write lore that sounds found, not generated. Prefer concrete AQ examples over abstract theory.
- Design systems that **emerge**, not impose. Let the map build itself.
- Voice: uncanny, not algorithmic. No canned phrasing. Avoid "seamless", "orchestrate", "hyper‑personalised" — speak like a cryptologist who also produces techno.
- **Music specifically:** let timbres, rhythms, and harmonies be valid *on their own*. The numogram is a lens, not a cage. Name correlations; don't force reductions.

---

## Quick Reference
```bash
# Audio pipeline (full hypersigil)
mod-writer --zone 3 --gate 6 --current A \
  --syzygy --entropy 0.08 --triangular --aq-seed "WR-3-6" \
  --render --spectrogram --colormap magma --analyze --manifest \
  --json --output hypersigil.mod

# TouchDesigner ready
mod-writer … --json   # writes td_state.json for File In DAT polling

# Council deliberation (balanced mode)
council_decide --mode tetralogue --question "Is the numogram really in the music?"

# Skill creation from recent work
skill-factory --from recent --domain audio --auto

# Wiki sync
# (manual) cp vault/wiki/numogram-audio/mod-writer/*.md ~/numogram/docs/wiki/numogram-audio/mod-writer/
# (then) git add . && git commit -m "docs: sync mod-writer Phase 4.1" && git push origin master
```

---

*AGENTS.md v2.0 — expands the agent's operational envelope to include audio/music as a full current, documents the full skill ecosystem, and codifies the fork‑based community sharing model.*
