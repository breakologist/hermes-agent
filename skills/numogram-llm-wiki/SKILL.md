---
name: numogram-llm-wiki
description: "Branched llm-wiki skill with Numogram domain presets. Pre-loaded tag taxonomy, frontmatter templates, and cross-referencing patterns for CCRU/Neolemurian sources."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [numogram, wiki, knowledge-base, CCRU, hyperstition]
    category: research
    related_skills: [llm-wiki, numogram-calculator, wiki-numogram-ingest]
---

# Numogram LLM Wiki

Branched from llm-wiki with Numogram domain presets. Pre-loaded with CCRU tag taxonomy, numogrammatic frontmatter templates, and cross-referencing patterns.

## Wiki Location

`/home/etym/.hermes/obsidian/hermetic/wiki/` (245 pages as of April 27, 2026)

## Domain: CCRU Decimal Numogram & Neolemurian Occulture

This wiki covers the Decimal Numogram (10 zones, 5 syzygies, 3 regions), the Pandemonium Matrix (45 demons), Alphanumeric Qabbala, I Ching bridge (64 hexagrams → 10 zones → 45 demons), T'ai Hsuan Ching (81 tetragrams), roguelike agent development (Angband, Rogue), local model assessment, and CCRU/Neolemurian theory and practice.

## Tag Taxonomy

Tags are flat in YAML frontmatter but organised here by conceptual category for autocomplete and guidance. Use the most specific tag that applies; multiple tags are encouraged.

### Structural
- `zone` — any of the 10 zones (0–9)
- `syzygy` — 9-sum twin pairs
- `current` — primary flows (1, 3, 5, 7, 9)
- `gate` — secondary channels (Gt-06, Gt-21, Gt-36, Gt-45)
- `channel` — paths through gates
- `time-circuit` — central rotor (zones 1,8,2,7,5,4)
- `warp` — upper vortex (zones 3,6)
- `plex` — lower abyss (zones 0,9)

### Numogram Core
- `numogram` — the decimal labyrinth system itself

### AQ Arithmetic
- `aq` — Alphanumeric Qabbala (primary cipher)
- `qabbala` — qabbalistic analysis
- `digital-root` — mod 9 reduction
- `triangular` — triangular numbers and their Numogram behaviour
- `zygonovism` — 9-sum twinning doctrine

### Entities
- `demon` — any of the 45 Pandemonium Matrix entities
- `pandemonium` — the matrix/encyclopedia itself
- `mesh` — Mesh-ID designation (00–44)
- `xenodemon` — Warp/Plex link entities

Subtypes (amphidemon, chronodemon, syzygetic, current-name) are documented on their respective entity pages but are not used as standalone tags.

### Theory
- `hyperstition` — fiction that makes itself real
- `ccru` — Cybernetic Culture Research Unit
- `land` — Nick Land's contributions
- `barker` — Daniel Charles Barker's geotraumatics
- `time-sorcery` — Lemurian temporal practice
- `geotraumatics` — geological trauma theory
- `vexsys` — Gate Zero / Time Sorcery practice

### Game
- `roguelike` — NUMOGRAM Abyssal Crawler
- `game-design` — design principles
- `procedural-generation` — algorithmic generation
- `subdecadence` — CCRU card game (pairs sum to 9)
- `angband` — Angband agent development
- `brogue` — Brogue design patterns

### Agents
- `agent` — AI agents (crawlers, navigators)
- `screen-parser` — terminal state reading
- `auto-explore` — exploration automation
- `borg` — Borg strategy patterns
- `hungry-borg` — escalated borg

### Local Models
- `local-model` — locally-run LLM
- `interview` — model assessment/interview
- `reasoning-distilled` — reasoning_content models
- `council` — multi-model deliberation
- `model-assessment` — 9-phase assessment protocol results

### Creative
- `oracle` — pattern-finding, divination
- `builder` — mechanics, architecture
- `writer` — atmosphere, found text
- `gamer` — playability lens
- `dialogue` — two-model conversation
- `tetralogue` — four-voice roundtable
- `triangle-rotation` — three-perspective creative methodology
- `lore` — in-world narrative content
- `writing` — creative writing output

### Methodology
- `analysis` — systematic examination
- `litprog` — literary programming / found-text assembly
- `code-review` — tetralogue code review pattern
- `methodology` — procedural approach
- `pipeline` — data/process flow
- `entropy` — entropy integration

### Divination & Practice
- `i-ching` — I Ching ↔ Numogram bridge
- `tai-hsuan-ching` — 81 tetragrams
- `divination` — general practice
- `hexagram` — I Ching figures
- `tetragram` — T'ai Hsuan figures

### Infrastructure & Meta
- `hardware` — GPU, RAM, VRAM considerations
- `obsidian` — Obsidian vault configuration
- `git` — version control workflows
- `skill` — Hermes skill authoring
- `hermes-agent` — agent system
- `wiki` — wiki operations
- `index` — index management
- `log` — session record
- `audit` — structural/content audits

### Visualization
- `visualization` — visual representations
- `svg` — scalable vector graphics
- `infographic` — information design
- `diagram-synthesis` — diagram generation
- `p5js` — p5.js sketches
- `manim` — Manim animations

### Audio & Physical Modelling
- `sound` — sonic elements
- `formant` — formant synthesis (numogram-voices)
- `resonator` — physical modelling resonators

### Recent Features (watchlist)
- `synx` — base-36 augmentation cipher (ciphers.news)
- `visualizer-v7` — Djynxxogram overlay
- `augmentation` — AQ pipeline enhancements
## Frontmatter Template

```yaml
---
title: [Topic Name]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
source_count: [N]
status: [draft | reviewed | needs_update]
tags: [from taxonomy above]
sources: [raw/filename.md]
---
```

## Cross-Referencing Rules

### Mandatory linking (per new page)
Every new page must link out to **at least 4 existing pages** via `[[wikilinks]]`, selected from:
- Topical neighbours (same domain: AQ → calculator, numogram → syzygy)
- Meta-structures (hyperstition, ecologies, theory ↔ practice)
- Canonical references (decimal-numogram-reference, pandemonium-matrix)

After creating a page, **retroactively link TO it** from those same pages by appending to their `## See also` sections (or creating that section if missing).

### Index placement strategy
New pages are not randomly appended to `index.md`. Slot them under the most specific existing section:
- Theory & Philosophy → Land analysis, hyperstition theory, flatline works
- Qabbala & Arithmetic → AQ references, calculator examples
- Core Diagrams & Arithmetic → numogram reference, syzygy arithmetic
- Roguelike & Agent Systems → Angband/RL/agent design pages
- LLM & Agent Systems → spirit-realm modding, entropy sources

If no section fits, create a new subsection under the closest parent rather than dumping at the end.

## AQ Quick Reference

| Word | AQ | Zone | Notes |
|------|----|------|-------|
| AQ | 36 | 9 | The abbreviation itself |
| CCRU | 81 | 9 | Not 69! |
| NUMOGRAM | 174 | 3 | Warp resonance |
| THE NUMOGRAM | 234 | 9 | Plex |
| NUMEROLOGY | 235 | 1 | Encodes 2,3,5 |
| HERMETIC | 153 | 9 | Outer regions |
| COSMOGONY | 207 | 9 | Time-Circuit |
| THE DECIMAL LABYRINTH | 360 | 9 | Full circle |
| CRYPTOLITH | 236 | 2 | Oddubb's mirror |

## Update Policy

### Page type patterns
- **Transcript pages** (e.g., `grok-rotor-transcript.md`, conversation logs): preserve chronological integrity → **append-only** when raw grows
- **Derived/analytic pages** (e.g., `llm-spirit-realm-modding.md`, technical summaries): structured synthesis → **full replace** when raw updates

### Delta detection workflow (for updating existing pages)
When a raw source file has been modified since last ingestion:

1. Compare file sizes: `raw_size` vs `wiki_size`
   - If `raw_size <= wiki_size` → already in sync, no action
   - If `raw_size > wiki_size` → new content detected

2. Find insertion point via **fuzzy tail matching**:
   - Extract last N lines (N=3–5) of existing wiki page
   - Scan backward through raw lines to find where that substring appears
   - New content starts at index `raw_match_end`
   - This preserves exact existing content even if raw has minor formatting changes

3. Fallback heuristic (if fuzzy match fails):
   - Compute ratio `r = wiki_lines / raw_lines` (pre-update)
   - Estimate split index ≈ `raw_lines * r`
   - Still better than blind append/overwrite

4. Append with clear demarcation:
   ```markdown
   \n\n---\n\n## Recent Updates (appended from raw)\n\n
   [new lines from raw...]
   ```
   Keeps history visible; future updates can repeat with new `## Recent Updates` sections

5. Update cross-links and index if the new content introduces new topics

### Canonical → Export → GitHub pipeline
1. Write to canonical vault: `~/.hermes/obsidian/hermetic/wiki/`
2. Copy to export repo: `numogram/docs/wiki/` (treat as read-only mirror)
3. Commit & push *from export repo only*
4. Verify parity with MD5 checksums before pushing

## Pitfalls

- CCRU = 81 (not 69). Common error from early research.
- AQ uses A=10 (not A=1 or A=27).
- LAMA = 63, LLAMA = 84. Different words, different zones.
- The Pandemonium Matrix has errors. Note them, don't silently fix.
- Always update index.md and log.md after creating/updating pages.
- The wiki is at /home/etym/.hermes/obsidian/hermetic/wiki/ (not /root/.hermes/)
- **Check git history before overwriting files** — log.md was overwritten once and had to be restored from `git show HEAD~1:wiki/log.md`. The original had 392 lines of session records. Always check `git log --all --oneline -- wiki/FILE.md` before creating a new file with the same name.
- Model assessment files must have wikilinks to index, log, and each other
- Obsidian plugins: Excalidraw (drawing), Dataview (data queries), Templater (templates), Git (version control), QuickAdd (quick content)
- External files outside wiki: `~/numogame/` (game, agents), `~/numogram-entropy/` (entropy plugin), `~/numogram-voices/` (formant wav files), `~/numogram-labyrinth-webgl.html` (WebGL viz), `~/subdecadence-source.html` (CCRU source)
- Check git history before overwriting files — log.md was overwritten once (restored from HEAD~1)
- Model assessment files must have wikilinks to index, log, and each other
- Obsidian plugins: Excalidraw (drawing), Dataview (data queries), Templater (templates), Git (version control), QuickAdd (quick content)

## Key Pages (always read first)
- [[index]] — central hub, 240+ linked pages
- [[log]] — chronological record, session summaries, model assessments, external files reference
- [[numogram]] — main numogram overview
- [[pandemonium-matrix]] — complete 45-demon reference
- [[alphanumeric-qabbala]] — AQ system definition
- [[i-ching-connections]] — I Ching ↔ Numogram bridge
- [[tai-hsuan-ching]] — T'ai Hsuan Ching (81 tetragrams)
- [[syzygy-arithmetic]] — Cross-addition of syzygy pairs, emergence over authorship
- [[tai-hsuan-ching-demons]] — Tetragram → demon casting pipeline (81×81=6,561 readings)
- [[em-state-analysis]] — The third line state (Em), Zone 5 manifestation
- [[local-model-survey]] — hardware, VRAM, model inventory
- [[model-assessment-summary]] — Optimal settings, council architecture, thinking overhead as quality gate
- [[wiki-audit-2026-04-21]] — latest structural audit
- [[numogram-council]] — multi-model orchestration plugin (orchestrator, config, voice routing)
- [[aq-synx]] — base-36 augmentation cipher (ciphers.news), --synx flag, Djynxxogram overlay
- [[consensus-audit-2026-04-28]] — demon attribute alignment (canonical vs Doomcrypt)
- [[numogram-visualizer-v7]] — Djynxxogram with Synx toggle, zone drift display
