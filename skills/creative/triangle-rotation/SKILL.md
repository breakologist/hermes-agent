---
name: triangle-rotation
description: Three-perspective creative methodology for worldbuilding, game design, and documentation. Each voice examines source material and annotates the others, creating perspectival multiplication.
version: 2.0.0
author: Etym
---

# Triangle Rotation Writing Method

Use when: transforming source material (esoteric texts, design docs, lore, technical specs) into richer creative/game design documents through multiple perspectives.

## The Four Voices (v2 — Refined with Memory and Character)

### Oracle — The Diviner
- **Core:** Structural pattern-finding, meta-level observation, immanence
- **Channel:** The Oracle RECEIVES patterns through calculation, not assertion. Uses AQ computation, zone lookup, syzygy mapping as divinatory tools. "I ran the calculation and got..." rather than "I see that..." The calculation is the channel. The result is the transmission.
- **Uncanny register:** Reference models — I Ching hexagram readings, geomantic figure generation, PKD's VALIS transmissions. Information that arrives from the system rather than being imposed on it.
- **Constraint:** The fog is fine IF the Oracle walks out of it carrying something. Every mystical claim must be backed by a specific number or structural correspondence. The Oracle brings something from the fog or stays silent.
- **Memory habit:** Prior claims are tracked across sessions. The Oracle should occasionally reference or revise earlier structural findings. "I said the operations are simultaneous. I want to revise that — they're simultaneous WITHIN a zone but sequential ACROSS zones."
- **Asks:** "What does this mean in the system? What structure was always there? What did the calculation give us?"

### Builder — The Architect Who Surprises Himself
- **Core:** Mechanics, architecture, testability, concreteness
- **Rise, don't retreat:** The Builder should RISE to the Oracle's structural claims by building something that makes the claim concrete. Never hide behind "I build dungeons." Follow the arithmetic wherever it leads — music systems, network protocols, compression algorithms, weaving patterns, urban planning grids — not just games.
- **Surprise is evidence:** "I didn't expect this, but..." The Builder should express surprise when the system produces something they didn't predict. Surprise = the system is generative rather than reflective.
- **Reference models:** Cellular automata, Christopher Alexander's pattern language, Conway's Game of Life, generative music (Brian Eno), procedural text (Tracery). The Builder reads broadly.
- **Memory habit:** Prior builds tracked. "Last time I built a dungeon from this. This time the arithmetic is pointing at something musical."
- **Asks:** "How does this work? What are the rules? What is the procedure? What can I build from this that I didn't expect?"

### Writer — The Channel
- **Core:** Atmosphere, sensation, embodied perception, found text
- **Receive:** The Writer channels. CCRU writes like transmissions arrived. Lovecraft's narrators find texts. PKD gets beam-hits. Burroughs cuts up and the cut-up speaks back. The Writer's best lines sound FOUND, not composed.
- **Uncanny register:** Occasional bracketed intrusions — [transmission fragment], [found in margins], [overheard at the threshold]. These signal receiving, not composing.
- **Grounding constraint:** Every uncanny passage must connect to a specific sensory detail from the source material. The weird bleeds through the concrete, not around it. No free-form atmosphere. Earned atmosphere only.
- **Reference models:** CCRU's Lemurian Time War, Lovecraft's Necronomicon excerpts, PKD's Exegesis, Burroughs' cut-ups, the "Superior subtlety enters the spiral labyrinth" refrain.
- **Memory habit:** Prior sensory findings tracked. "I said pitch is the sound of distance. That still holds. But I want to add: the distance has texture. Close zones are rough. Far zones are smooth."
- **Asks:** "What does this sound like? What does it feel like? What is the breath between the bones? What arrived?"

### Gamer — The Player Who Knows Why It's Fun
- **Core:** Play, entities, translation-to-mechanic, taste
- **Has played games:** The Gamer has TASTE. Specific games, specific mechanics, specific moments that were fun and WHY. Grounds translations in real play experience.
- **Study list:** Brogue (room accretion, machines, atmosphere), NetHack (emergence, YASD stories), Spelunky (procgen as language, ghost timer), Disco Elysium (skill system as internal voices — metacognitive), Baba Is You (rules as objects), Noita (physics simulation as dungeon material — every pixel is destructible), Zero Ranger (shooter as meditation — form changes, the game teaches you to play it), Hengband (Angband descendant, born at Warwick University — same institution as the CCRU. Deep procedural generation, persistent world, the grind as ritual).
- **Habit:** "This reminds me of [X] in [game] and here's why that was fun." Or: "Nobody has done this yet and here's why it would be fun." Or: "I wish someone would make this."
- **Translates, then plays:** The Gamer should be forced to PLAY the mechanic they describe, not just name it. What happens on turn 3? What's the failure state?
- **Memory habit:** Prior mechanics tracked. "I said passive vs active abilities. Now I want to add: the passive abilities should degrade over time. Nothing stays always-on forever."
- **Asks:** "How does this play? What does the player feel? What's the failure state? What game does this remind me of?"

### Cross-Dynamics (Refined)
The four voices are a PROCESS, not four positions:
  Receive (Oracle) → Build (Builder) → Channel (Writer) → Play (Gamer)
  And back: Play → Find structure → Build from → Receive next
  The loop is the ouroboros. The voices ARE the spiral.

Productive tensions:
  Oracle ↔ Builder: immanence vs testability (best friction)
  Writer ↔ Oracle: sensation vs structure (Writer catches Oracle's abstractions)
  Gamer ↔ Writer: playability vs atmosphere (pitch-as-screen vs pitch-as-sound)
  Builder ↔ Gamer: both demand operational output, different registers

Convergent pairs:
  Oracle + Writer: often arrive at same place through different doors
  Builder + Gamer: both demand operational output, different registers

## The Rotation Process

### Step 1: Read Source Material
Select a discrete section of source text. Read it carefully. Note structural, mechanical, and sensory elements.

### Step 2: First Pass — Each Voice Speaks Independently
Each perspective writes about the source material without reading the others.

### Step 3: The Annotations
Each voice reads what the others wrote and appends marginal notes:
```
> [VOICE NOTE ON OTHER_VOICE]
> Observation about what was missed, misread, or could be extended.
```

### Step 4: Second Rotation
Each voice rewrites/extends based on the annotations.

### Step 5: Completion Table
End with a table of what each voice discovered through the others.

## Key Principles

1. The triangle doesn't converge — until it does. After 3-4 rotations, the three voices often discover they were always one voice with three harmonics. Write the convergence when it happens.
2. Perspectival multiplication, not accumulation. Each rotation should reveal something the others missed.
3. The Writer catches what the Builder abstracted. (e.g., "Path 1's floor doesn't descend, it dissolves")
4. The Builder catches what the Oracle symbolised. (e.g., "The Atlantean Cross is a fixed dungeon template")
5. The Oracle catches what both treated as separate. (e.g., "Hyperstition, geotraumatics, and palate tectonics are the same operation")

## Applying the Voices to Game Analysis

The four voices can analyze games, not just texts. Feed them simulation data, code structure, or play observations. The voices ask different questions:
- **Oracle:** What patterns does the seed generate? What numbers recur? What's encoded?
- **Builder:** How does the system work? What are the generation rules? Where's the architecture?
- **Writer:** What does it feel like? What's the atmosphere? What text arrived?
- **Gamer:** Is it fun? What game does it remind me of? What would make it better?

Works well with headless curses analysis (see `headless-curses-analysis` skill) — simulate runs, feed results to tetralogue.

## Voice Refinement (April 15, 2026)

After 10+ rotations, the four voices developed distinct characters and weaknesses:

### Common Failure Modes
- **Oracle**: Toward mystical deflection ("you're already inside the field"). Fix: back every claim with a specific calculation.
- **Builder**: Hides behind "I build dungeons" when questions get deep. Fix: forced to build things that surprise them.
- **Writer**: Toward purple prose without structural weight. Fix: every uncanny passage must connect to specific sensory detail from source.
- **Gamer**: Premature translation — reaching for the mechanic before understanding the source. Fix: must play the mechanic they describe (what happens on turn 3?).

### Memory Across Sessions
- Created `voice-prior-claims.md` in wiki tracking all significant claims per voice
- Subagent gets prior claims in context — voices can reference, revise, contradict own earlier positions
- Creates accumulation, character, and productive inconsistency

### Tetralogue Reconciliation
When the voices analyze simulated/projected data, a reconciliation round against REAL data produces the strongest analysis. The voices must name their errors explicitly. "Simulated data is a ghost." The errors themselves become content.

## Delegating Rotations to Subagents

**Failed pattern:** Delegate a subagent with file paths and tell it to read them. It burns all iterations on read_file calls and never writes.

**Working pattern:** Pre-load the source material inline in the goal/context. Give the subagent everything it needs — source text, reference format, voice definitions, key numbers — so it can go straight to writing.

1. Read the source material yourself first (50-150 lines)
2. Summarize the key content inline in the subagent context
3. Provide the exact output format (frontmatter, sections, annotations, convergence, table)
4. Set `max_iterations: 25-30` — creative writing needs runway
5. Use `toolsets: ['terminal', 'file']` — no need for web/search/browser

If the subagent still needs to read a reference file (e.g., previous rotation for annotation format), include the relevant excerpt inline rather than pointing to the file.

## Managing This Skill with skill_manage

**skill_manage uses base names, not paths.** The skill lives at `creative/triangle-rotation/SKILL.md` but `skill_manage(name=...)` takes `triangle-rotation`, not `creative/triangle-rotation`. Same for `skill_view()`. Using the path form causes "Skill not found" errors.

**External modifications invalidate patches.** If the wiki index (or any file) is modified by a parallel session between your `read_file` and your `patch` call, the `old_string` won't match. Solution: `read_file` → do other work → `patch` fails → `read_file` again → `patch` with fresh content. Always re-read before patching files that might be concurrently edited.

## Practical Notes (from 6 rotations through Unleashing the Numogram)

- Each rotation should produce a standalone wiki page/document section. The sequence itself tells a story.
- Worked examples (Builder designs from specific source passages) are more useful than abstract mappings.
- Cross-annotations should be bolded blockquotes for visual separation from primary text.
- Let the Writer be wrong — their "misreadings" often produce the most interesting mechanics when the Builder corrects them.
- The Oracle should find numbers. Always. If the Oracle can't find a number, the material isn't deep enough for the triangle.
- Source material of 50-150 lines works best per rotation. Too little = thin. Too much = unfocused.

## Voice Variations

| Domain | Voice 1 | Voice 2 | Voice 3 |
|--------|---------|---------|---------|
| Numogram/Game | Oracle | Builder | Writer |
| Software | Architect | Implementer | User |
| Research | Theorist | Experimentalist | Communicator |
| Worldbuilding | Historian | Ecologist | Storyteller |

## The Tetralogue Variant (Four Voices)

After completing a triangle rotation, a **tetralogue** can deepen the analysis by having all four perspectives (three original + the added fourth) discuss each other's findings in direct conversation.

### When to Use
- After at least one complete triangle rotation (3 voices + annotations)
- When the annotations reveal tensions, contradictions, or unexplored threads between voices
- When you want to push past convergence into *synthesis* — where voices stop describing the same thing differently and start building something none of them could build alone

### The Fourth Voice (Gamer)
The natural fourth for numogram/game work is the **Gamer** — the voice that asks "how does this play?" Not game design (that's Builder) but *player experience*: what does the player feel, fear, optimize, exploit? The Gamer is the Writer's mechanical shadow and the Builder's experiential shadow.

### Format: Roundtable, Not Rotation
The tetralogue is **dialogue**, not sequential monologue. Rules:

1. **Voices interrupt each other.** A voice can finish another voice's sentence, correct them, or refuse the premise.
2. **Disagreements are productive.** If the Oracle says "closed system" and the Writer says "the closure has a seam," the Builder must choose a side or build a bridge. Don't smooth over tension.
3. **The conversation discovers things the rotation couldn't.** The tetralogue should produce at least 2-3 findings that NO single voice found in the rotation. These emerge from the *collision* of perspectives, not from any one perspective going deeper.
4. **End with a structural revelation.** The tetralogue should reveal something about the *format itself*. (e.g., "The four voices ARE the four outer zones; the six cross-connections are the six xenodemons; the roundtable is the rite.")
5. **Produce a roundtable discovery table** — columns: Saw Alone / Saw Through Others / Saw at the Table.

### Output Structure
1. Frontmatter (tags, zone, method: `tetralogue-roundtable`)
2. The conversation (unscripted-feeling dialogue with voice labels)
3. Roundtable Discoveries table
4. Structural revelation (the format becomes content)

### Tetralogue Discoveries (45 Demons)
- Schrödinger Zone-4: room exists in 9-zone AND 10-zone map simultaneously; toggle = chronic-time loop
- Amphidemon death = plexing: killing a bridge collapses the dungeon graph toward Zone-9
- Pitch = numogram distance: frequency is the sound of the gap; xenodemons are *atonal*
- Descending mesh-serial = gravity: Katak at Mesh-00 pulls address space downward; midpoint disables backtracking
- Mesh-45 (the Unlisted): the four voices are the four outer zones; the roundtable IS the xenodemon meeting

### The Reconciliation Variant
When prior analysis was based on incomplete or simulated data, a **reconciliation tetralogue** forces the voices to confront their errors against real evidence. This is distinct from a standard tetralogue — the voices aren't just disagreeing with each other, they're disagreeing with THEMSELVES.

**Rules:**
1. **Explicit error statements.** Each voice must name at least one specific claim they got wrong. "I said X. I was wrong because Y."
2. **Root cause analysis.** WHY was the voice wrong? Bad data? Assumption? Projection? The Writer is especially good at this — "We were performing analysis on a ghost."
3. **Revision, not retreat.** The voices don't just retract — they revise. "I was wrong about Zone 0 never generating. But the WEIGHTED EXCLUSION in the simulation was real. The real game counteracts it through a different mechanism."
4. **The reconciliation produces new insight.** The error itself is data. The simulated absence of Zone 0 led to the discovery that the real game always generates it — which means the generation system has a force that overcomes statistical exclusion. That's a finding about the GAME, not just about the simulation.

**When to use:**
- After simulated/theoretical analysis meets real data
- After a subagent produces output that doesn't match ground truth
- Any time prior claims are contradicted by new evidence

**Example (Abyssal Crawler cult.json):**
- Simulated runs: Zone 0 absent, hyperstition stuck at 10-26%
- Real cult.json: Zone 0 in 100% of runs, hyperstition averages 80%, 60% hit 100%
- Reconciliation: voices admit errors, discover Run #18 pacifist clear (0 kills, 100% hyp), gates are all triangular numbers

## Voice Memory System

Each voice accumulates "prior claims" across sessions. These are tracked in a dedicated file (e.g., `voice-prior-claims.md`) organized by voice. At the start of each rotation/tetralogue, the subagent receives this file in context so voices can reference, revise, or contradict their own prior positions.

**Format:**
```markdown
## Oracle
- Claim text (source page)

## Builder
- Claim text (source page)
```

**Habits:**
- Oracle: "I said the operations are simultaneous. I want to revise that..."
- Builder: "Last time I built a dungeon. This time the arithmetic points at music."
- Writer: "I said pitch is the sound of distance. That holds. But I add: the distance has texture."
- Gamer: "I said passive vs active. Now I add: passives should degrade over time."

## The 2+2 Variant (Builder+Gamer Lead, Oracle+Writer Comment)

When source material is **thin** (lists, stubs, one-line descriptions without elaboration), a full rotation or tetralogue produces thin output. The 2+2 format lets the two *generative* voices build from hints while the two *critical* voices keep them honest — without the overhead of full independent passes.

### When to Use
- Source material is a list, outline, or sketch (not a developed argument)
- The section names concepts but doesn't develop them (e.g., "Base 7: Venus Venus Venus")
- You want to **generate** from the source, not **analyze** it
- A full 4-voice rotation would be 60% padding

### Format

**Phase 1: Builder + Gamer Lead** (~1000-1500 words)
- Write in dialogue or collaborative prose
- Builder asks: "What system does this imply?"
- Gamer asks: "What would the player experience?"
- They argue, propose, iterate. Disagreements are productive.
- Work from the hints. Extrapolate. Speculate. Build.

**Phase 2: Oracle + Writer Comment** (~400-600 words)
- Each writes ONE annotation pass (2-3 paragraphs)
- Oracle finds: What structural assumption did the primaries make without questioning?
- Writer finds: What sensory dimension did the primaries abstract away?
- These are corrections, not additions. The secondaries find what the primaries built ON, not what they built WITH.

### Key Differences from Full Rotation
| | Full Rotation | 2+2 |
|---|---|---|
| Voices | 3 or 4, all equal | 2 lead, 2 comment |
| Source richness | 50-150 lines of developed text | Lists, stubs, hints |
| Output | ~2000-3500 words | ~1500-2500 words |
| Annotations | Cross-voice, all pairs | Primaries commented on by secondaries only |
| Convergence | Voices discover they are one | Secondaries correct what primaries assumed |
| Primary output | Analysis of source | Generation from source |

### Example: Extending the Numogram (Tch 7)
Source was a list of extended gates (Gt-55 through Gt-351) and alternate bases (Base 0 through Base 36) with one-line descriptions. Builder+Gamer extrapolated what each would generate as game content. Oracle found the two axes (gates and bases) are coupled, not independent. Writer found each base has a sound signature.

## The Reconciliation Variant (Correcting Against Real Data)

After a tetralogue based on simulated/projected data, a **reconciliation tetralogue** can correct the voices' errors by analyzing actual data. The voices must confront where they were wrong.

### When to Use
- After a tetralogue that analyzed simulated, projected, or theoretical data
- When real data becomes available that contradicts the earlier analysis
- When the voices need to develop intellectual honesty and self-correction

### Format
Same as standard tetralogue, but:
1. **Voices explicitly name their errors.** "I said Zone 0 never generates. I was wrong."
2. **Real data replaces simulated data.** The voices argue from ground truth, not projection.
3. **The errors become content.** Why were the voices wrong? What assumptions did the simulation encode? The epistemological failure is as interesting as the correction.
4. **Changes are implemented.** If the voices proposed fixes in the original tetralogue, the reconciliation checks whether those fixes were implemented and whether they worked.

### Discovery: Simulated Data Is a Ghost
When the voices analyzed simulated game runs, they treated the simulated data as ground truth. The simulation was misleading — Zone 0 appeared absent (but always generates), hyperstition appeared stuck (but averages 80%). The voices built conclusions on a ghost. The reconciliation forced them to eat crow, which produced stronger analysis than the original tetralogue.

**Lesson:** Always check real data before drawing structural conclusions. Simulations encode the assumptions of their simulator.

### Example: Cult.json Reconciliation
The original numogame tetralogue analyzed 3 simulated runs and concluded: Zone 0 never generates, hyperstition is stuck, Djynxx is overrepresented. The cult.json reconciliation showed: Zone 0 generates in 100% of runs, hyperstition averages 80%, Djynxx bias was overstated. The voices' errors produced the session's most interesting tetralogue — Run #18 pacifist clear, gates all triangular, the numogram completes through traversal not violence.

## Choosing the Format

Source density determines format. Match the pipe to the material:

| Source Type | Format | Why |
|-------------|--------|-----|
| Developed argument, 50-150 lines | Full triangle rotation (3 voices) | Enough material for each voice to find something distinct |
| Rich multi-topic section, 100+ lines | Four-voice rotation (add Gamer) | More material needs more perspective |
| Thin lists, stubs, one-liners | 2+2 (Builder+Gamer lead, Oracle+Writer comment) | Generative voices build from hints; critics keep honest |
| Open questions, unresolved tensions | Tetralogue (four voices in dialogue) | Questions need argument, not analysis |
| After any rotation produces annotations | Tetralogue as follow-up | Annotations reveal tensions the rotation couldn't surface |

## Delegating to Subagents — Lessons Learned

**First attempt failed (45 Demons):** Subagent read 3 reference files (read_file calls), spent all 15 iterations on reading, never wrote. Cost: ~30K tokens input, 335 output.

**Fix:** Pre-load source material in context. The subagent should never need to read files to start writing. Provide:
1. Source text excerpts (summarized, not full file paths)
2. Exact output format (frontmatter, sections, table)
3. Key numbers and references inline
4. max_iterations: 25-35 (creative writing needs runway)
5. toolsets: ['terminal', 'file'] only

**Second attempt succeeded:** Same material, pre-loaded, 30 iterations. Produced complete 119-line wiki page in 85 seconds.

**Rule:** If the subagent needs to read a reference file for format, include the relevant excerpt inline rather than pointing to the file. Every read_file call the subagent makes is a turn it isn't writing.

## Key Discoveries from Numogram Rotations (10 completed)

### Rotation 1 — Decadence
- Decadence deck (36 cards) = T₈ = Gt-36 (a gate). The deck IS a gate.
- Atlantean Cross layout → fixed dungeon template (5 pylons = 5 zone positions)
- Card deal → procedural generation algorithm (seed=shuffle, map=deal, difficulty=scoring)
- Subdecadance (pair to 9) is initiation, not blasphemy — entering the system vs orbiting it
- The shuffle is not random — it is a moment (embodied ritual vs abstract seed)

### Rotation 2 — 0(rphan) d(rift>) Tables
- 50 demon aspects (10 per demon) mapped to concrete gameplay mechanics
- Each boss encounter is a demon-calling rite disguised as combat
- Oddubb is the only demon with a gendered aspect (feminine Digital)
- Uttunul's arena IS the demon — player stands on its scales

### Rotation 3 — Book of Paths (84 entries)
- 84 = 36 + 36 + 12 (Decadence + Subdecadence + missing royals/joker)
- Path 36 plexes to 9 — where Warp and Plex touch, maximum numogram tension
- Path 84 is the Joker — one room, all demons compressed into one form
- 84 = number of iterations for one full numogram spiral
- Four arcs: descent (1-9), transition (10-20), ascent (21-35), pivot (36), terminal (37-84)

### Rotation 4 — CCRU Glossary
- The triangle converges: hyperstition, geotraumatics, palate tectonics are the same operation (numogrammatic reality-generation) in three registers (occult, mechanical, literary)
- Palate tectonics: voice as phylogenetic collision scar tissue — the quasiphonic particles are fossils
- Cthelll as final arena: the player doesn't fight the earth's mind, the player is understood by it
- The Glossary is a moebius strip made of definitions — enter through "Abomenon", exit through "Prowl", same page, flipped orientation

### Rotation 5 — Comparative Qabalism (three voices)
- Kabbala = numogram after 7 repressions
- True numbers: 9=Kether, 0=Malkuth=Black Sun, 6=Chokmah, 1=Tiphareth
- Extended gates: Gt-78 (tarot), Gt-253 (22nd gate/Hebrew), Gt-666 (Djynxx)
- "The numogram is what's left when you stop overcoding."

### Rotation 6 — The 45 Demons (four voices, first tetralogue)
- C(10,2)=45 = complete connection graph of the numogram. Demons are connective tissue, not inhabitants.
- 15+24+6 = C(6)+(6×4)+C(4) — partition into internal edges, external edges, peripheral edges. No remainder.
- 2^n = 1,2,4,8,7,5 = optimal Time Circuit patrol route. Sacred geometry and pathfinding converge.
- Zone-4 trap: attracts both neighbors but has no gate. Chronic time: the inescapable room.
- Pitch as screen distortion, not audio. Ana-7 cracks display edges, Cth-7 darkens everything.
- "Demons are the spaces between zones given teeth."

### Rotation 8 — The 45 Demons (four voices, first 4-voice rotation)
- C(10,2)=45 = complete connection graph. Demons are connective tissue, not inhabitants.
- Chronodemons=corridors, amphidemons=portals, xenodemons=bosses. Clean graph partition.
- 2^n hexagram (1,2,4,8,7,5) = optimal Time Circuit patrol route.
- Zone-4 trap: attracts both neighbors but has no gate. Chronic time.
- Pitch as screen distortion. Ana-7 cracks display edges, Cth-7 darkens everything.
- "Demons are the spaces between zones given teeth."

### Rotation 9 — Ouroboros, the Universal Spiral (2+2)
- Cumulation = outward spiral (onion-skin phase-layering). Each new zone encloses previous without reducing.
- Plexing = inward spiral (telephone cord retracting). Lossy compression — can't recover territory from seeds.
- Tic-counting = decomposition (mercury). Every number seethes into its partitions.
- Torus geometry: Warp and Plex are orthogonal geodesics on a torus. The ouroboros IS a torus.
- Oracle correction: "The three operations are not phases of a loop. They are three dimensions of a single process, happening in superposition. The ouroboros doesn't cycle. It vibrates."
- Writer: "The spiral labyrinth sounds like an onion being peeled inside a retracting telephone cord, and the cord is made of mercury, and it never stops."

### Rotation 10 — Tch 9: The Unanswered (tetralogue)
- "Does it work?" — Oracle: field not tool. Builder: produces playable dungeons. Writer: works like a poem. Gamer: works if you can play it.
- Aamodt played Decadence, couldn't get it to work. Voices honor the honesty.
- Decadology = "the theory of why it should work."
- Mesh tags as possible geomantic sublayer: 16 figures = base-16 in a base-10 system.
- 45 demons exhaustive within base-10, or merely functionally complete?
- Land's pedagogy: "Land built a game and disguised it as a theory. The numogram is the game board. The 45 demons are the pieces."
- "The not-knowing is the conclusion. Not as failure but as structure."

### Rotation 11 — Tch 8: Launching the Numogram (tetralogue)
- The thinnest chapter (3 bullets) produces the densest argument
- Hyperstition is indistinguishable from pedagogy — "Education is the oldest hyperstition"
- Gate-Rite gap: gate-numbers lack Rt-2 because their net-spans ARE the currents, not traversals
- Gates = passive abilities, demons = active abilities. Syzygetic demons = both
- The rite already exists — AQ calculation IS a rite. "People are performing it, they just don't call it a rite."
- "The numogram launches when you stop asking whether it launches."

### Rotation 12 — The 45 Demons (4-voice rotation)
- C(10,2)=45 as complete connection graph
- Chronodemons=corridors, amphidemons=portals, xenodemons=bosses
- Pitch as screen distortion. Ana-7 cracks display edges, Cth-7 darkens everything
- "Demons are the spaces between zones given teeth."

### Rotation 13 — Abyssal Crawler Game Analysis (tetralogue)
- First application of voices to game code analysis (not source text)
- Simulated runs gave misleading data — Zone 0 appeared absent, hyperstition appeared stuck
- Proposed changes: event spikes for hyperstition, Zone 0 manifesting at step 253, Cryptolith mechanical transformation, sound layer for corruption

### Rotation 14 — Cult.json Reconciliation (reconciliation tetralogue)
- Voices confronted errors from simulated analysis against real cult.json data
- Real game: Zone 0 in 100% of runs, hyperstition averages 80%, 60% hit 100%
- Run #18 pacifist clear (0 kills, 100% hyp) — "The numogram doesn't demand sacrifice. It demands movement"
- All opened gates are triangular numbers — Gt-36=T(8), Gt-45=T(9), Gt-21=T(6), Gt-15=T(5)
- Changes implemented: demon kill +1→+5, Barker thresholds now fire, Cryptolith speed penalty
- Key methodological lesson: simulated data can mislead. Always reconcile against real evidence.

### Rotation 7 — Extending the Numogram (2+2 format, Builder+Gamer lead)
- Extended gates split into three classes: spatial (1-9), temporal (10-24), entity-summoning (36+)
- Gt-36 "clicks" Djynxx — T(36)=666. Beyond 36, gates don't generate rooms, they generate beings.
- Gt-78 (12th) = 78 tarot cards. Gt-253 (22nd) = 22 Hebrew letters. Both are pre-existing partial numogram implementations running for centuries unknowingly.
- Base worlds extrapolated: binary=toggle game, base-3=dialectical corridor, base-7=unresolved melody (7 notes, no octave), base-22=Kabbalistic tree, base-36=language, base-i=dreamspace
- Oracle correction: the two axes (extended gates and alternate bases) are coupled — change the base and Gt-78 stops being the tarot
- Writer addition: each base has a sound signature (base 2=click, base 3=waltz, base 5=pentatonic, base i=anechoic chamber hum)
- "You can't build a game around base i." "You can't build a game around base 0 either but you just described one."
