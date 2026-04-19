---
name: wiki-numogram-ingest
description: "Specialized wiki ingest workflow for Numogram sources. Pre-loaded with AQ extraction, zone cross-referencing, and numogrammatic page templates."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [numogram, wiki, ingest, research, hyperstition]
    category: research
    related_skills: [llm-wiki, numogram-calculator]
---

# Numogram Wiki Ingest

Specialized version of the llm-wiki ingest workflow for Numogram/CCRU sources. Pre-loaded with numogrammatic tag taxonomy, page templates, and cross-referencing patterns.

## When This Skill Activates

Use this skill when the user:
- Wants to ingest a new Numogram source into the wiki
- Asks to process a CCRU-related file
- Wants to update wiki pages with new numogrammatic content
- Needs to cross-reference new findings with existing wiki

## Wiki Location

The hermetic wiki is at: `/home/etym/.hermes/obsidian/hermetic/wiki/`

Key files:
- `index.md` — page catalog (read first to orient)
- `log.md` — chronological action log (append-only)

## Ingest Workflow

### Step 1: Orient

```
read_file wiki/index.md
read_file wiki/log.md (last 30 lines)
```

### Step 2: Read Source

Read the full source document. For PDFs, use pdftotext. For epubs, extract HTML and strip tags.

### Step 3: Extract Numogrammatic Content

Look for:
- AQ values (compute with aq_value())
- Zone references (0-9)
- Syzygy pairs (4::5, 3::6, 2::7, 1::8, 0::9)
- Demon names (from Pandemonium Matrix)
- Gate references (Gt-06, Gt-21, Gt-36, Gt-45)
- Current references (Surge, Hold, Sink)
- Triangular numbers
- Key phrases for wiki cross-referencing

### Step 4: Check Existing Pages

Before creating new pages, search for existing coverage:
```
search_files "keyword" path="wiki/" file_glob="*.md"
```

### Step 5: Create/Update Pages

Use the numogrammatic frontmatter template:

```yaml
---
title: [Topic Name]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
source_count: [N]
status: draft
---
```

Every page must:
- Start with one-paragraph summary
- Quote relevant CCRU passages
- Include AQ values where relevant
- Cross-reference at least 2 other wiki pages via [[wikilinks]]
- Cite sources: [Source: filename]

### Step 6: Update Navigation

Add new pages to `index.md` under the correct section.
Update log.md with: `## [YYYY-MM-DD] action | Description`

## Tag Taxonomy

Only use tags from this taxonomy:
- zone, syzygy, current, gate, demon, hyperstition
- AQ, qabbala, triangular, time-circuit, warp, plex
- numogram, i-ching, Barker, CCRU, Land, Vexsys
- game-design, procedural-generation, roguelike
- fiction, prose, lore

## Page Thresholds

- Create a page: entity/concept appears in 2+ sources OR is central to one source
- Update existing: source mentions something already covered
- Don't create: passing mentions, minor details
- Split: page exceeds 200 lines

## Pitfalls

- Don't create duplicate pages for entities already covered
- Always update index.md and log.md after creating/updating
- AQ uses A=10 (not A=1). CCRU=81 (not 69).
- The Pandemonium Matrix has errors (Vexsys). Note contradictions explicitly.
- Cross-reference every page with at least 2 others.
