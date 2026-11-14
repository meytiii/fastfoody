---
trigger: always_on
description: Mandatory and absolute NO COMMENT rule across all code in the repository.
---

# Absolute "NO COMMENT" Rule

Agents and developers must NEVER write, generate, or leave comments in any code under any circumstances.

## Mandatory Directives

### 1. Zero Comments in Code
- **No Single-Line Comments:** Absolutely no `//` comments anywhere in code.
- **No Multi-Line Comments:** Absolutely no `/* ... */` comments in code or stylesheets.
- **No JSDoc / TSDoc:** Absolutely no `/** ... */` annotations in code.
- **No HTML / Template Comments:** Absolutely no `<!-- ... -->` in templates, markup, or SVG.
- **No CSS / Preprocessor Comments:** Absolutely no comments in stylesheets or style blocks.
- **No Script Comments:** Absolutely no `# ...` comments in code or scripts.

### 2. Self-Documenting Code
- Express intent, invariants, and business logic through clear, descriptive naming of functions, variables, and components.
- Rely on explicit TypeScript types, interfaces, and enums instead of comment explanations.
- If code feels complex or ambiguous, refactor and simplify the implementation rather than writing explanatory comments.

### 3. No Placeholders or TODOs
- Never write `TODO`, `FIXME`, `NOTE`, `HACK`, `REVIEW`, or stub comments.
- Code delivered must be complete, tested, functional, and production-ready.

### 4. Continuous Enforcement
- Any comment introduced during coding or refactoring must be stripped before staging and committing.
- All future code written in this repository must remain completely comment-free.
