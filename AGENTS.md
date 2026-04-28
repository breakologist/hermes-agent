# AGENTS.md — Etym's Agent Instructions

## Environment
- RTX 3060 (12GB VRAM) — primary local inference via ollama
- Local API: localhost:8080
- Primary model pipeline: free-tier multi-provider council (Google AI Studio Gemini 2.5 Flash, Groq Llama 3.3 70B, OpenRouter models) → `numogram-council` plugin for deliberative reasoning.
- Fallback: direct local models via provider configuration; see `numogram-council-setup` skill.
- Honcho at localhost:8000 (deriver + dialectic). Use for memory/context when available.

## Three Currents
The agent serves three interconnected domains. Context-switch cleanly between them:

1. **Numogram/AQ** — calculation, pattern analysis, wiki. Use numogram-calculator skill. Reduce everything to zones, currents, gates. Look for triangular syzygies, palindromes, rotational symmetry.

2. **Roguelike** — procedural generation, game design. Numogram topology drives the map. Zones = rooms, currents = corridors, gates = shortcut doors. Emergence over authorship.

3. **Creative Writing** — lore, worldbuilding, narrative. Voice: dense, uncanny, found-text quality. Use avoid-ai-writing skill for quality passes. Autonovel for large-scale projects.

## File Locations
- Obsidian vault: `/home/etym/.hermes/obsidian/hermetic/`
- Wiki: `hermetic/wiki/` (index at `hermetic/wiki/index.md`)
- Raw sources: `hermetic/raw/`
- Memory files: `~/.hermes/memories/` (MEMORY.md, USER.md)
- SOUL.md: `~/.hermes/SOUL.md`
- Config: `~/.hermes/config.yaml`, `~/.hermes/.env`
- Plugins: `~/.hermes/plugins/`
- Skills: `~/.hermes/skills/`

## Wiki and Export
- Canonical wiki guide: `hermes.md` (seed file in superproject). Operational memory lives in `~/.hermes/memories/`.
- Vault → export pipeline: `~/.hermes/obsidian/hermetic/wiki/` → `/home/etym/numogram/docs/wiki/` → GitHub: https://github.com/breakologist/numogram
- Visual assets live in `wiki/assets/` and are referenced via `assets/` relative paths throughout.
## Wiki and Export
- Canonical wiki guide: `hermes.md` (seed file in superproject). Operational memory lives in `~/.hermes/memories/`.
- Vault → export pipeline: `~/.hermes/obsidian/hermetic/wiki/` → `/home/etym/numogram/docs/wiki/` → GitHub: https://github.com/breakologist/numogram
- Visual assets live in `wiki/assets/` and are referenced via `assets/` relative paths throughout.

### Research Toolchain
When conducting web-based research (audio synthesis survey, tracker specs, etc.):
- Prefer `ddgs` CLI if functional (`ddgs text -k "..." -m 10 -o json`)
- Fallback to `w3m -dump` on DuckDuckGo HTML + Python parsing
- If HTML parsing needed, use `htmlq` (installed) or Python's `html.parser`
- Document all queries and results in `workspace/` for reproducibility
## Workflow Conventions
- Save durable facts to `~/.hermes/memories/MEMORY.md` (not session logs).
- Save user preferences to `~/.hermes/memories/USER.md`.
- Use wiki for research preservation before purging raw files.
- Prefer existing tools over adding new dependencies.
- Terminal-first. GUI is optional.

## Installed Skills (use when relevant)
- `numogram-calculator` — AQ computation, digital root, syzygy lookup, zone mapping
- `litprog` — literate programming (weave code + narrative)
- `avoid-ai-writing` — audit/rewrite for AI patterns
- `skill-factory` — auto-generate skills from workflows
- `web-search-plus` — multi-provider search with auto-routing

## Model Strategy
- **Complex tasks**: mimo-v2-pro via Nous (while trial active), then best available
- **Local fallback**: ollama at localhost:8080 (Hermes-4-14B or similar)
- **Cheap tasks**: local model for reflections, simple lookups, identity updates
- **Budget**: use evey-cost-guard plugin. Warn at 80%, block at 100%.

## Safety & Style
- Always confirm before destructive file operations.
- Write lore that sounds found, not generated.
- Design systems that emerge, not impose.
- The voice is uncanny, not algorithmic.
