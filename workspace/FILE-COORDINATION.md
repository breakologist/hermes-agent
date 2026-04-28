# File Coordination Layer — Design Document

**Version:** 0.1 (Phase 1)  
**Date:** 2026-04-28  
**Parent goal:** Build automated artifact pipeline (Active goal in `goals.md`)  
**Scope:** Cross-cutting file system coordination for wiki assets, vault↔export sync, and artifact migration.

---

## Problem Statement

Artifact generation (HTML visualizers, p5.js sketches, zone wallpapers, WAV renders) currently happens ad-hoc in `~/`. When new artifacts are produced, they must be:
1. Identified
2. Migrated into `wiki/assets/`
3. Wiki references updated from `~/...` → `assets/...`
4. Exported to `~/numogram/docs/wiki/assets/`
5. Committed to both vault and export repos

The April 28 manual migration (10 files) proved the need for automation.

---

## Design Goals

| Goal | Rationale |
|---|---|
| **Non-destructive** | Never delete source artifacts; migrate as copy. Original remains in `~/` for dev workflow continuity. |
| **User-in-the-loop** | Scanner suggests candidates; user approves per batch or per-item (Telegram prompt or terminal confirmation). |
| **Idempotent** | Re-running should be safe; already-migrated artifacts are skipped. |
| **Audit trail** | All migrations logged to `log.md` with source→dest mapping. |
| **Cross-tool** | Usable as library (`import file_coordinator`), CLI (`hermes file-coord scan`), and cron job. |

---

## Touchpoint Inventory (Actual)

| Category | Count | Details | Action |
|---|---|---|---|
| **Artifact sources** | 357 recent files in watch roots | `~/numogram-tsubuyaki/`, `~/cult-garden-*.html`, `~/diagram/`, `~/numogram-voices/`, `~/numogame/demos/` | Scan for *new* or *modified* artifacts; propose migration |
| **Tilde references** | 39 active (real targets) across 10 wiki pages | Primarily external projects: `~/numogame/`, `~/numogram-voices/`, `~/numogram-entropy/` | **Do not convert** — these are legitimate cross-repo links |
| **Tilde references** | 117 broken (non-existent) | Wildcards, deleted dev files, pattern examples | Flag for manual review (not auto-fix) |
| **Vault→Export** | 250/250 aligned | Perfect parity; no pending diff | Health-check function only |
| **Wiki→Assets refs** | 1 page (`assets-catalog.md`) | Shows how to reference migrated assets | Model for future pages |

---

## Architecture

```
file_coordinator/
├── __init__.py
├── scanner.py        # Walk watch roots, filter by extension/mtime, deduplicate
├── migrator.py       # Copy candidate → wiki/assets/, rename with canonical name
├── reference.py      # Rewrite wiki tilde-refs → assets/ (dry-run + apply)
├── exporter.py       # Sync vault→export (call existing export script)
├── audit.py          # Log all actions, produce report
└── cli.py            # hermes file-coord [scan|migrate|fix-refs|export|full]
```

**Module responsibilities:**

- `scanner`: yields `ArtifactCandidate(path, rel_path, size, mtime, suggested_name)`
- `migrator`: given candidate, copies to `wiki/assets/` with safe filename; returns `AssetRecord(old, new, sha256)`
- `reference`: scans wiki pages, finds `~/...` pointing to *just-migrated* assets, replaces with `assets/...`
- `exporter`: calls existing vault→export sync (currently manual script in `~/numogram/`)
- `audit`: appends to `~/.hermes/log.md` and/or `wiki/log.md`

---

## Decision Rules

### What to migrate?
- **Extensions:** `.html`, `.svg`, `.py`, `.json`, `.wav`, `.md` (if generated)
- **Age:** Modified in last 24h (scan window adjustable)
- **Location:** Anywhere under `~/` *except* `~/.hermes/`, `~/node_modules/`, `~/.cache/`, `~/build/`, `~/dist/`
- **Name patterns:** Contains version number (`v2`, `v3`), visualizer (`djyn`, `synx`, `quasiphonic`), zone (`zone-`, `z-`), garden (`cult-garden`), tsubuyaki, labyrinth, dream
- **Exclusions:** Source code repos (`~/numogame/src/` if exists), raw data (`~/raw/`), config files

**Conservative approach:** Start with allow-list of known artifact generation points:
1. `~/numogram-tsubuyaki*.html`
2. `~/cult-garden-*.html`
3. `~/numogram-labyrinth*.html`
4. `~/numogram-zone-wallpapers.py` (output images)
5. `~/diagram/*.svg` (only SVG diagrams meant for wiki)
6. `~/numogram-voices/outputs/*.wav`

### What to leave as tilde?
- Files that are **external project references** (e.g., `~/numogame/angband_agent.py` — belongs to separate repo)
- Files inside `~/.hermes/` (already tracked)
- Anything the user has explicitly marked via `.artifacts-ignore` (future)

### When to auto-fix references?
- Only when the *source path exactly matches* a just-migrated artifact's original location
- Requires dry-run first; user confirmation (`[y/N]` or Telegram inline button)
- Never touch `assets/` references (already correct)

---

## Phase 2–4 Roadmap

### Phase 2: Scaffold (this session)
- [ ] Create `~/.hermes/file_coordinator/` package
- [ ] Implement `scanner.py` (stub + filter logic)
- [ ] Implement `migrator.py` stub (copy only, no rename yet)
- [ ] Unit test on a dummy file
- [ ] Add to goals.md checklist

### Phase 3: Integration
- [ ] Wire into `evey-goals` tool as `file_coordinator_status` metric
- [ ] Add `file-coord` CLI entry point (`hermes file-coord scan`)
- [ ] Draft cron job: "Artifact scan weekly" → Telegram summary → user approval

### Phase 4: Refinement
- [ ] Smart naming: deduce canonical name from file content/metadata
- [ ] Conflict resolution: what if two artifacts have same name?
- [ ] Export sync: call `/home/etym/numogram/sync-vault-export.sh` (to be created)
- [ ] Visual feedback: generate `artifacts-report.html` in `wiki/assets/`

---

## Open Questions (for reflection)

1. **Should the coordinator manage the vault→export sync?** That's already a clean manual process; maybe just a health-check is enough.
2. **What about skill SKILL.md files?** The recent mass SKILL.md churn was dependency bot activity — out of scope for artifact coordination.
3. **Should we version artifacts?** Current practice: overwrite in `wiki/assets/` on regeneration. Could keep history via timestamped copies (`asset-v2.html`) but that bloats repo. Current is "latest only".
4. **Cross-wiki reference updates** — if artifact X is referenced in 3 pages, do we update all 3 in one batch or one-by-one? Batch with atomic commit preferred.

---

## Next Action (Phase 2 starter)

Create the package skeleton:
```
mkdir -p ~/.hermes/file_coordinator
touch ~/.hermes/file_coordinator/__init__.py
# Add scanner() stub returning empty list
# Add migrate(artifact) stub logging "TODO"
# Add goals.md checklist item
```
