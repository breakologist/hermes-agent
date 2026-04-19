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

`/home/etym/.hermes/obsidian/hermetic/wiki/`

## Domain: CCRU Decimal Numogram & Neolemurian Occulture

This wiki covers the Decimal Numogram (10 zones, 5 syzygies, 3 regions), the Pandemonium Matrix (45 demons), Alphanumeric Qabbala, and related CCRU/Neolemurian theory and practice.

## Tag Taxonomy

### Structural
- `zone` — any of the 10 zones (0-9)
- `syzygy` — 9-sum twin pairs
- `current` — primary flows (1, 3, 5, 7, 9)
- `gate` — secondary channels (Gt-06, Gt-21, Gt-36, Gt-45)
- `channel` — paths through gates
- `time-circuit` — central rotor (zones 1,8,2,7,5,4)
- `warp` — upper vortex (zones 3,6)
- `plex` — lower abyss (zones 0,9)

### Entities
- `demon` — any of the 45 Pandemonium entities
- `syzygetic` — Katak, Djynxx, Oddubb, Murrumur, Uttunul (five carrier demons)
- `current-name` — Surge (8→7, Murrumur), Hold (2→5, Oddubb), Sink (4→1, Katak), Warp (6→3, Djynxx), Plex (9→9, Uttunul)
- `amphidemon` — open net-span demons
- `chronodemon` — cyclic demons
- `xenodemon` — Warp/Plex link demons
- `lemur` — synonym for demon

### Arithmetic
- `AQ` — Alphanumeric Qabbala
- `qabbala` — qabbalistic analysis
- `triangular` — triangular numbers and their Numogram behavior
- `digital-root` — mod 9 reduction
- `zygonovism` — 9-sum twinning
- `binodecimal` — 6-cycle from binary powers

### Theory
- `hyperstition` — fiction that makes itself real
- `time-sorcery` — Lemurian temporal practice
- `Barker` — Daniel Charles Barker's work
- `CCRU` — Cybernetic Culture Research Unit
- `Land` — Nick Land's contributions
- `Vexsys` — Gate Zero / Time Sorcery practice
- `geotraumatics` — Barker's geological trauma theory

### Game
- `game-design` — roguelike design principles
- `procedural-generation` — dungeon generation
- `roguelike` — the NUMOGRAM Abyssal Crawler game
- `subdecadence` — CCRU card game (pairs summing to 9, Atlantean Cross)
- `ladder-mode` — alternative vertical map layout for roguelike

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

- Every page must link to at least 2 other pages via [[wikilinks]]
- When creating a new page, check what existing pages should link TO it
- When updating an existing page, check if new content creates links FROM it
- Standard cross-reference sets:
  - Zone pages ↔ syzygy partner ↔ carrier demon ↔ region
  - Demon pages ↔ zone ↔ net-span partner ↔ current
  - Theory pages ↔ practice pages ↔ source texts

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

- Note contradictions explicitly with "> CONTRADICTION:" blocks
- The Pandemonium Matrix has errors (Vexsys). Don't treat it as canonical.
- New sources supersede old ones unless explicitly noted.
- All AQ values should be verified against aq_value() function.

## Pitfalls

- CCRU = 81 (not 69). Common error from early research.
- AQ uses A=10 (not A=1 or A=27).
- LAMA = 63, LLAMA = 84. Different words, different zones.
- The Pandemonium Matrix has errors. Note them, don't silently fix.
- Always update index.md and log.md after creating/updating pages.
- The wiki is at /home/etym/.hermes/obsidian/hermetic/wiki/ (not /root/.hermes/)
