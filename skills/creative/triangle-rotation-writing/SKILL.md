---
name: triangle-rotation-writing
version: 1.0.0
description: Three-perspective creative writing method — rotating voices examine the same source material and annotate each other, producing richer output than single-perspective analysis.
author: Etym
agentskills_spec: "1.0"
---

# Triangle Rotation Writing Method

A creative methodology for producing multi-perspectival analysis of source material. Three voices rotate through the same content, each reading and annotating the others. The result is richer than any single perspective — each voice catches what the others missed.

## The Three Voices (Default Configuration)

### 1. The Oracle
Reads for **structure, pattern, and hidden connections**. Sees the numogram, the arithmetic, the system. Answers: "What does this mean in the deeper pattern?"

### 2. The Builder
Reads for **mechanics, systems, and functional design**. Sees the algorithm, the procedural generation, the gameplay. Answers: "How would this work as a system?"

### 3. The Writer
Reads for **atmosphere, voice, and sensory detail**. Sees the sound, the feeling, the prose. Answers: "What does this feel like?"

## How It Works

### Round Structure
Each round (rotation) processes ONE piece of source material through all three voices:

1. **Oracle speaks first** — reads the source, finds the pattern
2. **Builder reads Oracle** — finds mechanics in the pattern, responds
3. **Writer reads both** — finds atmosphere in the mechanics, responds

### Cross-Annotation
Each voice includes marginal notes directed at the others:
```
> **[ORACLE NOTE ON BUILDER]**
> The Builder mapped X to Y. But the source says Z. 
> The structure reveals that...
```

These notes are the key — they're where the three perspectives *collide* and produce insights none would reach alone.

### Accumulation
Each rotation builds on the previous. The output of rotation N becomes context for rotation N+1. The method is fractal — each pass reveals one more turn of the spiral.

## Output Format

A single markdown file per rotation:
```
# [Source Material] Triangle — [Nth] Rotation

Source: [citation]

## I. [First Voice]
[analysis with cross-annotations]

## II. [Second Voice]  
[analysis with cross-annotations]

## III. [Third Voice]
[analysis with cross-annotations]

## The [Nth] Rotation Completes

| Voice | Saw what others missed |
|-------|----------------------|
| A → B | [key insight] |
| B → C | [key insight] |
| C → A | [key insight] |
```

## Variations

The three voices can be adapted to any domain:
- **Game design**: Designer (mechanics), Artist (aesthetics), Player (experience)
- **Code review**: Architect (structure), Implementer (details), User (API surface)
- **Research**: Theorist (framework), Experimentalist (data), Communicator (narrative)
- **Music**: Composer (structure), Sound Designer (timbre), Performer (expression)

## Tips

- Let each voice have a distinct *register* — not just different topics, different prose styles
- The Oracle should be terse and structural. The Builder should be practical and specific. The Writer should be sensory and evocative.
- The best cross-annotations are *corrections* — when one voice says "you're right about X but wrong about Y because..."
- Don't force consensus. The triangle doesn't converge. It *rotates*.
- After 3-4 rotations, the voices start to merge. That's the signal that the material has been fully explored.

## Key Discoveries (from 4 rotations on Unleashing the Numogram)

### Rotation 1 (Decadence): the perspectives reveal hidden structure
- Oracle saw Decadence as ritual disguised as play (36 cards = T₈ = Gt-36)
- Builder saw procedural generation in the card deal (seed = shuffle, map = deal)
- Writer saw Subdecadance as initiation not blasphemy ("the difference between orbiting and entering")
- **Key insight**: the Atlantean Cross layout IS a dungeon template (5 pylons = 5 zone positions)

### Rotation 2 (0(rphan) d(rift>) tables): mechanics ARE rites
- Builder mapped all 50 demon aspects to gameplay mechanics
- Writer gave each demon a voice register (Katak = heat shimmer, Djynxx = strobe, Oddubb = mirror, Murmer = tide, Uttunul = end of sound)
- Oracle discovered each boss encounter IS the demon-calling rite that summons it
- **Key insight**: the player doesn't fight demons, the player PERFORMS them

### Rotation 3 (Book of Paths): the hidden numogram inside the sequence
- 84 paths form a numogram traversal: descent (1-9), transition (10-20), ascent (21-35), pivot at Path 36 (Warp/Plex contact), terminal sinking (51-84)
- Path 84 = the Joker. 84 = 36 + 36 + 12 (Decadence + Subdecadence + missing cards)
- **Key insight**: 84 is the number of iterations for one full numogram spiral

### Rotation 4 (Glossary): the voices converge
- Hyperstition, geotraumatics, and palate tectonics are the same operation in three registers
- The triangle doesn't rotate anymore — it stippled (three points become one surface)
- **Key insight**: the Glossary entries cross-reference each other — it's a moebius strip of definitions

### Scaling observation
4 rotations on a 4410-line document produced 30+ wiki pages of original design material. Each rotation added approximately 8-10 pages. The method is productive but diminishing — rotation 5+ would likely produce less unless new source material is introduced.

## Example (Numogram Roguelike)

Source: Decadence card game rules
- Oracle: "The 36-card deck = T₈ = Gt-36. The deck IS a gate."
- Builder: "Set-1 is fixed topology, Set-2 is exploration. The deal generates the map."
- Writer: "Subdecadance isn't blasphemy. It's initiation. The difference between orbiting and entering."

Each perspective reveals a layer the others can't see.
