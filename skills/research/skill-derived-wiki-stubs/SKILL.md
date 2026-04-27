---
name: skill-derived-wiki-stubs
description: Convert skill references into proper wiki stub/redirect pages, ensuring cross-link integrity and index coverage when a methodology hub references skills that lack corresponding wiki documentation.
version: 1.0.0
author: Hermes Agent (Etym)
tags: [wiki, stub, skill-mapping, cross-linking, methodology, tetralogue]
---

# Skill-Derived Wiki Stubs

**Purpose:** Populate wiki pages for skills referenced by a methodology hub when those skills exist in the Hermes skill tree but have no corresponding Obsidian wiki page (or only a terse stub that should become a redirect).

## When to Use

You are building or consolidating a **hub page** (like `tetralogue.md`) that references:
- `skill-name` (Hermes skill)
- `category/skill-name` (qualified skill)

And the wiki lacks a corresponding page at `skill-name.md` (or `category-skill-name.md`). The result is a broken `[[skill-name]]` link.

## Prerequisites

- Hub page drafted with `[[skill-references]]`
- Access to skill inventory via `skills_list()` and `skill_view(name)`
- Vault and export wiki paths configured (defaults: `~/.hermes/obsidian/hermetic/wiki/`, `~/numogram/docs/wiki/`)
- Git access for commits

## Step-by-Step Workflow

### 1. Audit Hub Links

Extract all `[[wikilinks]]` from the hub page. Flag any that:
- Do not have a corresponding `.md` file in the vault
- Are skill names (e.g., `tetralogue-generator`, `numogram-tetralogue-generator`)
- Are qualified paths that need translation (`category/skill-name` → `category-skill-name.md` or descriptive title)

```python
import re
links = set(re.findall(r'\[\[([^|\]]+)\]\]', hub_text))
broken = [l for l in links if not (vault / f'{l}.md').exists()]
```

### 2. Survey Skills

For each broken link:
- Find the skill with `skills_list()` or direct filesystem lookup (`~/.hermes/skills/`)
- Read the skill with `skill_view(name)` to get description, tags, workflow summary
- **Discern intent:**
  - **Redirect** (tiny existing stub, or skill is just a format variant of another) → create redirect page pointing to the hub or parent skill page
  - **Full stub** (substantial skill, unique methodology) → create a proper stub page summarizing the skill and linking back to the hub

### 3. Create Wiki Pages

**Redirect stub template:**
```markdown
---
title: Skill Name (redirect)
created: YYYY-MM-DD
status: stub
redirect: target-page
tags: [skill, methodology]
---

> This material is documented at [[target-page]]. See the **Related Skills** or **Cross-References** section.
```

**Full stub template:**
```markdown
---
title: Skill Name
created: YYYY-MM-DD
status: stub
tags: [skill, domain, methodology]
---

One-sentence summary of what the skill does.

**Purpose:** [2–3 lines]

**When to use:** [trigger conditions]

**Related skills:** [[hub-page]], [[other-skill]]

**Skill location:** `category/skill-name` (Hermes plugin)
```

### 4. Update Hub Cross-References

Structure the hub's **Cross-References** section in tiers:
```
### Core Skills
- [[skill-name]] — one-line description (links to stub/redirect)

### Skills (Hermes plugins)
- `skill-name` — category tag only (for provenance)

### Example Applications (see also index)
- [[example-page-1]] — ...
```

### 5. Update `index.md`

Insert entries in **logical sections**, not just appended:
- Under **"Unleashing the Numogram — Triangle Rotations"**: place `triangle-rotation-writing` after `triangle-rotation`
- Under **"Skills & Tools"** or **"Creative & Generative"**: place `tetralogue-code-review`, `tetralogue-generator`
- Avoid duplicate entries (search first: `grep '\[\[skill-name\]\]' index.md`)

Use `patch()` with 2–3 lines of surrounding context to avoid ambiguous matches.

### 6. Sync & Commit

Copy new/updated pages to export:
```bash
cp vault/wiki/<page>.md export/docs/wiki/
```

Commit **separately** for hub vs stubs:
```bash
git add <hub-page> index.md
git commit -m "docs(wiki): expand hub with skill cross-references"
git add <stub1> <stub2> ...
git commit -m "docs(wiki): add skill-derived stubs (code-review, generator)"
```

Push both repos. Verify no broken links remain.

### 7. Flag Maintenance Issues

If you discover:
- **Duplicate skill copies** (same skill in two directories) → note in commit message; consider creating a `SKILL-maison-DUPLICATE-ALERT.md` tracking file
- **Skills missing SKILL.md** (broken plugin) → create minimal stub or flag for repair
- **Skill names that don't match wiki naming conventions** → suggest rename in commit body

## Pitfalls & Fixes

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Skill path vs wiki page name mismatch | `[[numogram-tetralogue-generator]]` links to nothing (file should be `numogram-tetralogue-generator.md` or a more descriptive title) | Translate: category/skill-name → readable page title; create redirect if needed |
| Duplicate skill directories | Same skill exists in both `skills/numogram/` and `skills/domain/` | Note in commit; do not delete — may be versioned; create single wiki page that documents both locations |
| Existing terse stub should redirect but gets overwritten | 8-line `tetralogue-litprog.md` replaced with full content | Check size first; if <200 bytes or clearly a placeholder, convert to redirect instead of expanding |
| Index section doesn't exist yet | Insertion fails silently or duplicates | Create section header if missing (`## Skills & Tools`); better: place under nearest existing section |
| Broken links after rename | `[[tetralogue-roundtable]]` still missing | Verify link text matches filename exactly; strip slashes, spaces |

## Example: Tetralogue Hub Consolidation

**Hub:** `tetralogue.md` referenced:
- `[[tetralogue-roundtable]]` (skill exists, no wiki page) → **redirect stub**
- `[[tetralogue-code-review]]` (skill exists, no wiki page) → **full stub** (code review specialization)
- `[[tetralogue-generator]]` (skill exists, no wiki page) → **full stub** (pipeline orchestrator)
- `[[triangle-rotation-writing]]` (skill exists, no wiki page) → **redirect stub** (writing variant of triangle-rotation)
- `[[tetralogue-litprog]]` (8-line existing stub) → **converted to redirect** (redundant with hub's Format Variants)

**Result:** 5 stub pages created, index updated in two sections (Unleashing the Numogram, Creative & Generative), all cross-links resolved, committed as two batches (hub expansion, then stub creation + index refinement).

**Additional discovery:** `numogram-tetralogue-generator` skill existed in **two** directories (`numogram/` and `domain/`) — documented as duplicate; single wiki page covers both.

## Related Skills

- `wiki-stub-fulfillment-from-codebase` — **Sibling skill.** The original batch-stub pattern for codebase artifacts (functions, constants, data tables). Used for Batch B arithmetic cluster. This skill (`skill-derived-wiki-stubs`) handles the skill-inventory → wiki case. (functions, constants, data tables) rather than skills; both produce batch stub pages with index integration.
- `wiki-audit` — Finds orphaned/stub pages; use this skill after consolidation to verify no new orphans introduced.
- `triangle-rotation` — One of the skills commonly referenced by methodology hubs; understands the voice definitions used across multiple pages.
- `tetralogue-roundtable` — The hub format itself; this skill's output *is* a tetralogue page.
