---
name: source-code-reverse-engineering
description: Extract data models, algorithms, and design patterns from live web applications and GitHub repos. When you can't read rendered JS bundles, go to the source. Systematic approach for analyzing tools, libraries, and frameworks.
version: 1.0.0
author: Etym
tags: [research, reverse-engineering, github, web, data-extraction]
---

# Source Code Reverse Engineering

Use when: you need to understand how a web application or library works internally, especially when the rendered site is a JS bundle you can't easily parse.

## Problem

Modern web apps (Next.js, React, Vite) ship minified JS bundles. Trying to extract data structures from the rendered page gives you CSS variables and framework boilerplate. The actual data model is hidden in compiled code.

## Approach: Go to the Source

### Step 1: Identify the Framework
- Check for `__next_f` (Next.js), `__NUXT__` (Nuxt), `__vite` (Vite)
- Find JS chunk URLs from `<script>` tags
- Check `package.json` if GitHub repo exists

### Step 2: Find the GitHub Repo
- Look for install instructions on the site (`npm install git+https://...`)
- Check for `@org/repo` references in component imports
- GitHub links on the page footer or components page
- Use `github.com/{org}/{repo}` to access raw source files

### Step 3: Read Data Files, Not Bundles
The data model is in TypeScript/JavaScript source files, not in the compiled bundle. Look for:
- `app/data/` or `src/data/` — zone definitions, demon lists, gate tables
- `types.ts` or `interfaces.ts` — the type definitions ARE the schema
- `lib/` or `utils/` — algorithms, geometry, transformations
- `components/` — how data maps to UI

**Key insight:** TypeScript type definitions (`interface`, `type`) tell you exactly what data exists and what fields it has. Read `types.ts` first — it's the schema.

### Step 4: Extract the Algorithm
- Read the generation/rendering code to understand transformations
- Look for loops, conditionals, and mathematical operations
- Note any interesting patterns (classification algorithms, geometric calculations)

## Example: QLIPHOTH Systems

1. Visited `qliphoth.systems/numogram` — got CSS variables and Next.js boilerplate, not data
2. Found GitHub repo from install command: `github.com/lumpenspace/ccru`
3. Read `app/data/types.ts` — ZoneMeta, SyzygyData, CurrentData, GateData, Demon interfaces
4. Read `app/data/demons.ts` — found the 45-demon generation loop with 3-way classification
5. Read `app/data/zones.ts` — zone colors, quasiphonic particles, tic xenotation, planet symbols
6. Read `app/lib/geometry.ts` — quadPath, loopPath, curveAway, syzTrianglePoints
7. Each data file was ~30 lines of clean TypeScript — minutes to understand vs hours of JS bundle analysis

## What to Extract

| Category | Where to Look | What You Get |
|----------|--------------|--------------|
| Data model | `types.ts`, `data/*.ts` | Schema, field names, relationships |
| Algorithms | `lib/*.ts`, `utils/*.ts` | Generation logic, transformations |
| Rendering | `components/*.tsx` | How data maps to visuals |
| Config | `package.json`, `.env.example` | Dependencies, environment setup |
| Tests | `__tests__/`, `*.test.ts` | Expected behavior, edge cases |

## Pitfalls

- **Private repos:** Some sites don't expose their source. Fall back to reading rendered JS chunks (search for data arrays in the minified code).
- **Monorepos:** The data files might be in a subdirectory, not the root. Check `packages/`, `libs/`, `apps/`.
- **Generated data:** Some data is computed at build time. Look for generation scripts or seed files.
- **Auth-gated APIs:** The site might fetch data from an API. Check network tab (browser devtools) for XHR/fetch calls.

## When NOT to Use This

- If the site has good documentation or API docs — read those instead
- If you only need to use the tool, not understand it — just use it
- If the codebase is massive (10K+ lines) — focus on the specific module you need
