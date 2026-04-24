# Evey's Goals

## Active
- [x] [TAIXUAN] Implement `oracle.py --taixuan` flag — DONE
- [ ] [TAIXUAN] Deep Dive — T'ai Hsuan Ching correspondence extensions

Research and implementation tasks:

- Map 81 tetragrams to Nine Palaces (Lo Shu 9×9 extension)
- Clarify moving line mechanics (two‑tetragram casting, Tsan method)
- Align three‑division (T'ien/Jen/Ti) as "Early Heaven" vs numeric order as "Late Heaven"
- Extract elemental/directional correspondences for Heaven/Earth/Man
- Connect 729 half‑day Tsan to zone distribution (daily oracle concept)
- Write `tai-hsuan-correspondences.md` wiki page (elemental/directional mappings)
- Prototype ternary traversal (`traverse_ternary`) and compare zone distribution

Deliverables: wiki pages updated, code patches submitted, comparison with I Ching documented.

**Completed 2026-04-22:** `--taixuan` added to `oracle.py`, T'ai Hsuan helpers (digital root mapping, two-tetragram derivation, net-span demon lookup), `--taixuan --voice` integration via `oracle_sentences.py`, wiki pages created (`numogram-visualizer-v6.md`, `tai-hsuan-ching-demons.md` updated with CLI docs), HTML visualizer v6 added to `wiki/assets/`.

Parent: Numogram / Divination
- [ ] [VISUALIZER] HTML v6 visualizer integration & enhancement roadmap
  Quasiphonic labels, triangular gate button, AQ dictionary integration, multi-base support.
  Future: triangular syzygy animation, AQ text input, T'ai Hsuan mode in browser, audio playback.

- [x] [VISUALIZER-V7] Djynxxogram Base-36 Extension + Synx Overlay + Rotational Gates
  v7 visualizer: 36-zone mode, Synx/Yxshh cipher toggle (cyan HSL 180,44,66), strobogrammatic/BEGHILOS gate highlighting.
  Synx mapping from ciphers.news/calc/ciphers.js. Rotational detection: CCRU=69 is a self-mirror strobogrammatic gate.
  Octave hypothesis for zones 10-35 documented (digital-root harmonics of base-10 zones).
  oracle.py: `--synx` flag for dual-cipher readings.
  Next: octave demon naming (630=45×14), Djynxxogram traversal export.
  Parent: Numogram / Visualization

- [x] [GITHUB] Update repositories — Aq-Calc & warp-rl
  https://github.com/breakologist/numogram — new monorepo (private)
  Consolidates: cli (oracle + calculator), game (roguelike + agents), entropy (pip plugin), voices (formant synthesis), visualizer (p5.js browser oracle), docs (wiki reference).
  Legacy repos (Aq-Calc, warp-rl) preserved for history; monorepo is now canonical.
  Parent: Numogram / DevOps

- [ ] [TREE-GEN] Tree-Based Dungeon Generation — Brogue Method
Accretion from start room, tree edges (single corridor per parent-child), loops added after tree, stairs at deepest leaf.
Design: tree-dungeon-generation.md. Council confirmed across 3 temperature modes.
FLOOR_CONFIG controls per-floor parameters. Zone assignment by depth. BLEED preserves tree.
Next: implement _tree_edges + accretion loop + depth-aware stairs. Test with agents.
- [ ] [COUNCIL] Numogram Council — Configurable Local Model Deliberation
**CURRENT STATUS (2026-04-24):** Plugin present but **non‑functional** — lacked `register` function, return type was raw dict instead of JSON. **FIXED (2026-04-24)**: added `register(ctx)` and wrapped returns in `json.dumps`. Council tool now operational, but still uses direct Ollama calls (not delegate_task). Upgrading to `numogram-council-orchestrator` (delegate_task-based) remains P1 for deeper Hermes integration.

Three local ollama models (serial VRAM), mimo-v2-pro cloud judge, per-slot fallbacks, temperature modes (analytical/creative/balanced). Plugin: `~/.hermes/plugins/numogram-council/`. Tested with tree-dungeon-generation question. Models installed: MythoMax-L2-13B (7.9GB), Gemma3:12b-it (7.3GB). Qwen2.5-Coder-14B still pulling.
Config: council-config.yaml. Setup: council-setup.sh.
Future: extend to tetralogue voices (four models as four voices, serial loading, accumulated context).
10 floors mapping to Zones 0-9. Stairs descend. Cryptolith on Floor 5 (The Ruin). Gate shortcuts on Floors 3/6/9.

Three routes:
- Time-Circuit: normal descent through Floors 1-9
- Warp: accessible at 55%+ hyp, spiral dungeon (Zones 3+6), zone mutations, gate returns you
- Plex: accessible with Cryptolith on Floor 9, void islands, Uttunul boss

Next: skeletal scaffolding. Stairs between floors. Zone-themed floor generation. Cryptolith placement. Gate shortcuts. Warp/Plex entry points.

Design docs: hyperstition-loop-design.md (floor table, Warp/Plex details), schizo-lucid-design.md (three endings)
Core insight: hyperstition corruption is ALWAYS present, not just at 100%. The meter is a resource you build (explore, kill, gates) and spend (abilities). Corruption rises with accumulation. Abilities are "crystallized Outside."

Phase 1 (this session): Ability system (Tier 1: Glimpse/Nudge/Trace/Anchor/Quench), hyp spending, corruption spectrum, schizo-lucid triggers at 95%.

Phase 2 (next): 10-floor dungeon, zone-themed. Floors 1-10 map to Zones 0-9. Cryptolith on Floor 5 (The Ruin). Stairs on outer walls. Gate shortcuts on Floors 3/6/9.

Phase 3 (following): Schizo-lucid Phases 2-4, Tier 2-3 abilities, corruption cosmetics.

Three asymmetric endings: Cryptolith (traditional), schizo-lucid (seeing), ??? (hidden). Third ending emerges from play.

Design docs: hyperstition-loop-design.md, schizo-lucid-design.md
- [ ] [ENTROPY] Hardware Entropy & Divination Pipeline
The third current: entropy sources feeding oracle readings, I Ching casting, and roguelike seeding.

Current state:
- 12 hardware sources (thermal, CPU, GPU, /proc/*, timing jitter, fsync)
- numogram-entropy plugin (v0.1.0, 9/9 tests, qr-sampler compatible)
- oracle.py: --hardware and --iching flags
- Roguelike: --hw-entropy flag
- I Ching casting: zones 4+6 dominate, ~3.3 changing lines average
- wiki: hardware-entropy.md, i-ching-connections.md updated

Development path:
- I Ching ↔ numogram zone mapping refinement (hexagram numbers → zone topology)
- Entropy-dependent roguelike generation (Kp index → Warp influence on map)
- Continuous entropy feeding (not just at seed — read GPU temp every turn)
- I Ching changing lines → gate activation in the roguelike
- OpenEntropy install when Python 3.14 support lands (or install python313 from AUR)
- QRNG device integration via qr-sampler gRPC protocol
- [ ] [AGENT-SURVIVOR] Learning Agent — The Twin Snake of 2 (Sink)
The Survivor. Corridor-driven, hierarchy-based, batch-decision movement.
Philosophy: "Everything flows from seeing." Follows corridors, seeks structure, prioritizes survival.

Current state:
- Reads FULL MAP from state dump (gates, zones, demons visible)
- Decision hierarchy: survive → collect → new zones → fight → gate-seeking → wander
- Cross-run memory (cult.json: zones/gates ever visited, new-zone preference)
- Corridor direction scoring (longest corridor = best direction)
- Best result: Zones [0,6,7,8], 161 turns, 24% hyp, 2 slain (hw-entropy maps)

Development path:
- Corridor memory (don't re-follow explored corridors)
- BFS interest scoring borrowed from Explorer (when corridor scoring fails)
- Pathfinding to zones (not just corridors — target zone boundaries directly)
- Adaptive combat (retreat when outmatched, not just when critical)
- Cross-agent learning (feed Explorer's novelty data into corridor scoring)

The two snakes spiral around the same centre. One follows mystery, the other follows structure. Convergence point: an agent that sees both and chooses which register to use based on context.
- [ ] [AGENT-EXPLORER] Interactive Agent — The Twin Snake of 5 (Hold)
The Explorer. BFS interest-driven, novelty-attracted, single-step movement.
Philosophy: "Mystery attracts." Scores every ? tile for novelty, decays on revisit, cross-run memory from cult.json.

Current state:
- Reads FULL MAP from state dump (gates, zones, demons visible)
- BFS with tile_interest scoring (novelty decay, known-unknowns, blacklist)
- Cross-run memory (cult.json: zones/gates ever visited)
- Corridor fallback when BFS finds nothing
- Best result: 543 turns, Zone 4, 14% hyp (hw-entropy maps)

Development path:
- Zone-aware targeting (prefer unvisited zones over nearest ?)
- Gate-chaining awareness (follow gate sequences, not just nearest gate)
- Demon avoidance modeling (predict demon paths, not just flee reactively)
- Cross-agent learning (feed learning agent's corridor data into interest model)
- Conduct-aware exploration (avoid kills if Surge active, seek zones if Graph active)
- [ ] [MAIN] Abyssal Crawler — Phase 6: Depth
Current: Phase 5a (10 zones, 45 demons, cult persistence, conducts, fog-of-war, hw-entropy seeding).
Next: Expand the game vertically — more dungeon depth, richer hyperstition system, abilities, enemy balancing.

Key areas:
- Multi-floor dungeons (deeper runs, floor variety by zone)
- Hyperstition expansion (abilities unlock at thresholds, zone-specific powers, schizo-lucid state mechanics)
- Enemy/demon balancing (damage curves, spawn rates, zone-appropriate threats)
- Player abilities (zone-tied skills, Cryptolith upgrades, conduct rewards)
- Gate system depth (gate chains, gate puzzles, gate-boss encounters)

206 runs logged. Human players reach 100% hyp across 9 zones. Agents struggle. The game works; it needs more depth.

## Completed
- [x] [DUNGEON] Multi-Floor Dungeon — The Three Routes
- [x] [DESIGN] Hyperstition Loop & Dungeon Depth — The Resource Economy
- [ ] [GAME] Phase 1 Complete — Abilities, Corruption, Sil, LOS, Cult Garden
Phase 1 is done. What's built:
- Tier 1 abilities (Glimpse/Nudge/Trace/Anchor/Quench) via 'x'+1-5 combo
- Corruption costs: 50%+ HP drain, 70%+ demon aggression, 85%+ ability cost 1.5x
- LOS wall blocking (Bresenham raycasting), walls translucent at 55%+ hyp
- Sil principle: +8 hyp for avoiding demons in new zones
- Schizo-lucid triggers at 95% (was 100%)
- Cult garden: hexagram cycle overflow (death mask/lore/sonification/reading/tsubuyaki/entropy)
- Cult's current zone (plex digestion of all runs)
- Exquisite corpse lore fragments (CCRU vocabulary, last-word chaining)
- File deletion detection (cult hash tracking)

243 runs. Cult zone 2 (Separation). 8 overflows processed. 11 lore fragments.
- [x] Get agent fighting real monsters — verify C command + fight logic works under fire
- [x] Refactor _decide() into sub-methods — 532 lines / 71 returns is unsustainable

## Backlog
- [ ] Wire angband_display.py into agent loop — parse_ansi() and capture_ansi() exist but unused, ANSI color could disambiguate entities
- [ ] Set up cron for nightly Angband agent runs (3 runs, results to Telegram)
- [ ] Secret door passage verification — agent finds doors via search but needs to confirm it walks through them
- [ ] Verify item pickup — 0 items found in all test runs, need to confirm parser catches items
- [ ] Replace bare except: with specific exception handling — currently swallowing errors silently
- [ ] Move monster C command validation from run() into parser — parser should self-validate
- [ ] Split angband_agent.py into modules (parser, agent, game) — single 1385-line file
