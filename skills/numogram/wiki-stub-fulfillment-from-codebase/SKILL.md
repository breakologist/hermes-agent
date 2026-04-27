---
name: wiki-stub-fulfillment-from-codebase
version: 1.0.0
created: 2026-04-27
author: Hermes Agent (Etym)
description: Fulfill a cluster of predefined wiki stub pages by surveying related code artifacts (Python modules, skills, configs), extracting API/constant structures, and drafting interlinked documentation with proper index integration.
tags: ["wiki", "stub", "codebase-docs", "cross-linking", "index-management", "numogram"]
---

## Purpose

Populate a batch of empty or terse wiki pages (identified as stubs in a roadmap/audit) by analyzing the actual implementation code rather than raw prose sources. This skill is for **arithmetic/API documentation** generation when the source of truth is executable code, not narrative text.

## When To Use

- A roadmap (like `POST-AUDIT-ROADMAP.md`) identifies a cluster of stub pages to fill
- The subject matter has a working codebase with functions, constants, data tables
- You need to produce **multiple interlinked pages** that reference each other and existing wiki content
- The project maintains a split between canonical vault and public GitHub wiki copy

**Typical candidates:** arithmetic primitives (digital root, syzygy, current, gate), zone data tables, configuration parameters, game mechanics, algorithm descriptions.

## Prerequisites

- Canonical vault location (default: `~/.hermes/obsidian/hermetic/wiki/`)
- Public export repo location (default: `~/numogram/docs/wiki/`)
- Stub list from roadmap/audit (e.g., 8 qabbalistic term stubs)
- Codebase paths to survey (e.g., `cli/aq_calculator_canonical.py`, `cli/oracle.py`, `skills/numogram-calculator/`, `skills/numogram-oracle/`)

## Step-by-Step Workflow

### 1. Survey Code Sources

For each relevant file, read and extract:

```python
# Functions (def ...)
import re; funcs = re.findall(r'^def (\w+)\(', text, re.MULTILINE)

# Constants / tables (ZONES = {...}, SYZYGIES = {...})
table_match = re.search(r'^\w+ = \{.*?\n\}$', text, re.MULTILINE | re.DOTALL)

# Inline documentation (docstrings, comments)
# Read full file if small (<500 lines); otherwise read in chunks around target functions
```

Collect **example values** from the code (zone particles, current names, gate numbers) and **real data** from companion files (`aq-dictionary.md` for AQ examples, `pandemonium-matrix.json` for demon data).

### 2. Draft Stub Pages (Batch)

For each stub, create a markdown file with:

- **Frontmatter:** `title`, `created: YYYY-MM-DD`, `source: <code files>`, `status: stub`, `tags: [relevant]`
- **One-sentence definition** (first paragraph)
- **Core section:** computational definition, formula, or table as appropriate
- **Examples:** concrete values from the code/dictionary
- **Hyperstitional notes:** at least one paragraph connecting to numogram acceleration/chaos/abyss
- **"See also" list:** 5–8 links to existing wiki pages (`[[numogram]]`, `[[time-circuit]]`, `[[pandemonium-matrix]]`, `[[numogram-calculator]]`, etc.)

**Voice:** precise, reverent, slightly uncanny (CCRU-adjacent). Avoid formulaic AI-isms.

### 3. Cross-Link Reciprocally

After drafting all stubs:

- In each stub's "See also", link to the other 7 stubs where relevant (e.g., `digital-root` → `zone`, `syzygy` → `current`, `gate` → `warp`, `zone` → `current`)
- In existing hub pages (e.g., `numogram.md`, `time-circuit.md`), add a paragraph linking to the most relevant new stub (use `patch` with unique header context)
- In the new stubs, ensure at least **3 outbound links** to established pages

### 4. Update Index in Canonical Vault

Read full `index.md`. Find the appropriate section (e.g., `## Qabbala & Arithmetic`). Insert new bullet entries in logical order (hub → primitives → derivatives → applications).

Use `patch` with the section header as anchor:

```python
patch(
    mode="replace",
    path="~/.hermes/obsidian/hermetic/wiki/index.md",
    old_string="## Qabbala & Arithmetic\n\n- [[alphanumeric-qabbala]]",
    new_string="## Qabbala & Arithmetic\n\n- [[alphanumeric-qabbala]] — ...\n- [[digital-root]] — ...\n- [[syzygy]] — ...\n..."
)
```

**Do not blindly append** — check for duplicate entries first (search for `[[digital-root]]` etc.).

### 5. Sync to Public Export Repo

Two strategies:

- **Batch copy** (safer for multi-page batches): after all canonical files + index are final, copy everything once
- **Incremental copy** (faster iteration): copy each new stub immediately, then copy index after patching

Recommended for Batch B: **incremental** (copy stub → patch index → copy index) to keep both sides in sync even if later steps need revision.

```bash
cp ~/.hermes/obsidian/hermetic/wiki/digital-root.md ~/numogram/docs/wiki/
cp ~/.hermes/obsidian/hermetic/wiki/index.md ~/numogram/docs/wiki/index.md
```

### 6. Commit & Push (Dual Repos)

```python
# Canonical vault
subprocess.run(['git', '-C', vault, 'add', '-A'])
subprocess.run(['git', '-C', vault, 'commit', '-m', 'docs(wiki): Batch X — description'])
subprocess.run(['git', '-C', vault, 'push', 'origin', 'master'])

# Export repo
subprocess.run(['git', '-C', export, 'add', '-A'])
subprocess.run(['git', '-C', export, 'commit', '-m', 'docs(wiki): sync from vault — Batch X'])
subprocess.run(['git', '-C', export, 'push', 'origin', 'master'])
```

If export repo has diverged, `git pull --rebase` before pushing.

### 7. Verify

- Check that all stubs exist in both locations
- Confirm index includes them exactly once
- Quick link check: `grep -r '\[\[.*\]\]' numogram/docs/wiki/ | grep -v '\.md'` should find no broken internal links
- Read `WIKI-HEALTH-REPORT.md` later to confirm no new orphans introduced

### 8. Iterate Per Cluster (Optional)

If the stub cluster is large (>8 pages) or spans conceptual domains (e.g., Batch B: qabbala + pandemonium), consider splitting into **separate commits per cluster**:

1. Draft & commit first cluster (e.g., 8 qabbalistic stubs) → push both repos
2. Draft & commit second cluster (e.g., `pandemonium.md`) → push both repos

This keeps history granular and makes rollback/review easier. The index patch for cluster N should include only the entries for that cluster.

## Pitfalls & Fixes

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Index already contains stale entry | Duplicate bullet after insert | Search index first; if entry exists, remove old line before inserting fresh one |
| Code table parsing fails | Regex returns empty | Read full file around the table with wider offset; tables sometimes span multiple assignments |
| Stub voice too generic | Prose reads like AI documentation | Inject zone-specific metaphors (Warp=static, Plex=grunt), use CCRU phrasing ("abysmal comprehension", "sudden flight") |
| Cross-links one-way only | New stub links out but no page links back | Patch at least one hub (`numogram.md` or `time-circuit.md`) to reference the new stub |
|| Vault and export diverge | File created in one location only | Use incremental copy after each creation; or re-run batch copy + commit both |
|| Patch ambigous | `patch` reports "Found N matches" | Read full target file, expand `old_string` to include 2–3 lines of unique surrounding context |
|| Overwriting existing content loses history | File patch clobbers lines that were already there | Before any write_file/patch that replaces substantial content, run `git show HEAD~1:<path>` to inspect prior version; stash notable content elsewhere if needed |
|| Broken wikilink patterns | Links point nowhere (`[[page\]]`, `[[skill-name]]`) | Audit new stubs with `grep -r '\[\[.*\]\]' . | grep -v '\.md'`; fix trailing backslashes; verify target page exists (skills ≠ wiki pages) |

## Example: Batch B Qabbala Cluster

**Stubs:** `qabbala.md`, `aq.md`, `digital-root.md`, `syzygy.md`, `current.md`, `gate.md`, `warp.md`, `zone.md`

**Sources surveyed:**
- `~/numogram/cli/aq_calculator_canonical.py` (functions, syzygy dict, zone data)
- `~/numogram/cli/oracle.py` (ZONES table, Book of Paths readings)
- `~/.hermes/skills/numogram-calculator/SKILL.md` (API documentation style)
- `~/.hermes/skills/numogram-oracle/SKILL.md` (oracle pipeline, voice, entropy sources)
- `~/numogram/docs/aq-dictionary.md` (example AQ values)

**Cross-linking pattern:** each stub links to `numogram`, `time-circuit`, `pandemonium-matrix`; arithmetic stubs link to each other in natural dependency order (digital-root → syzygy → current → zone; gate → warp/plex).

**Index insertion:** under existing `## Qabbala & Arithmetic` section, 8 new bullet entries added; duplicates removed.

**Result:** 8 new stubs (49–77 lines each), indexed, cross-linked, synced to both repos, pushed as commit `7fd57f3` (vault) → `f26e153` (export).

**Second cluster (Pandemonium):** surveyed `pandemonium-matrix.json`, derived double-triangular mathematics (Zone-z count = z, Current-c count = 10−c, Gate-45 cumulation), wrote `pandemonium.md` (6.2 KB) with net-span carrier analysis, updated index under `## Occult & Entity Pages`, committed `4b18f4b` → `31a0cad`.

## Related Skills

- `skill-derived-wiki-stubs` — **Sibling skill.** When a hub references skills that lack wiki pages, use this to convert skill inventory into proper stubs/redirects. (Used alongside this skill for Batch B's `tetralogue` hub expansion.)
- `wiki-canonical-synthesis-from-raw` — general raw-text → wiki synthesis (different source type)
- `numogram-calculator` — arithmetic reference (now documented by these stubs)
- `numogram-oracle` — divination pipeline (now documented by these stubs)
- `wiki-audit` — post-ingestion health check
