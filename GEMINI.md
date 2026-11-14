# Gemini Agent Directives — Fastfoody Repository

Operating rules and directives for Gemini-based agents working in `fastfoody`.

---

## 1. Absolute "NO COMMENT" Rule

- **Zero Comments in Code:** Under no circumstances should any comments be written or left in any code file across the codebase (no `//`, `/* */`, `/** */`, `<!-- -->`, `#`).
- **Self-Documenting Standard:** All logic, intent, and constraints must be expressed through explicit naming, modular architecture, and TypeScript typing.
- **No Placeholders:** Complete implementations only. Never leave TODOs, stubs, or comments.

---

## 2. Core Architectural & Design Directives

- **Design System Authority:** Always consult `frontend/DESIGN_SYSTEM.md` for tokens, spacing, typography, and color harmony.
- **Modern Nuxt 4 Architecture:** Nuxt 4 Composition API, Tailwind CSS 4 `@theme`, Pinia state management.
- **RTL & Persian Typography:** Native RTL layouts with logical CSS properties and Persian numerals (`۰-۹`).
- **Automated Commit & Push:** Commit with Conventional Commits format and push directly to `main`.
