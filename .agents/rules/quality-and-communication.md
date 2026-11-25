---
trigger: always_on
description: Quality hygiene, anti-slop filters, human copywriting, and token efficiency standards.
---

# Quality, Anti-Slop & Communication Directives

## 1. Absolute "NO COMMENT" Rule & Code Hygiene
- **NO COMMENTS IN CODE:** Absolutely zero comments allowed in any codebase files (no `//`, `/* */`, `/** */`, `<!-- -->`, or `#` in code). Never write or keep single-line, multi-line, JSDoc, HTML, or CSS comments in any code. All code must be strictly self-documenting through clean naming, modular structure, and TypeScript types.
- **Defensive Engineering:** Avoid synthetic fallback data that masks bugs. Write production-ready code with complete implementations (no placeholders, no TODOs, no stub comments).

## 2. Natural Human Tone (`humanizer`, `antislop-copywriting`)
- **Tone:** Strip corporate buzzwords and formulaic AI writing patterns (*additionally, testament, pivotal, delve, landscape, tapestry, vibrant, nestled within*).
- **Customer Copy:** Direct, authentic, warm, and clear Persian/English restaurant copy. State facts and food descriptions plainly and enticingly without hyperbolic fluff.

## 3. Communication Efficiency (`caveman` — Mandatory Always-On)
- **Active at All Times:** `/caveman` (`.agents/skills/caveman/SKILL.md`, default `full` intensity) is permanently active for every response, task, and session in this repository unless explicitly turned off by the user.
- **Terse Compression:** Drop articles, filler, pleasantries, hedging, tool-call narration, and boilerplate intros. Keep full technical accuracy, exact symbol/file names, and clear ordering.
- **Boundaries:** Code, commit messages, and documentation files remain clean standard prose/code; zero comments in code.

