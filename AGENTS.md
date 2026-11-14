# Fastfoody Agent Directives & Active Skills

This document establishes universal operating guidelines, skills suite configuration, and mandatory development standards across the `fastfoody` repository.

---

## 1. Absolute "NO COMMENT" Rule

> [!IMPORTANT]
> **Under NO circumstances may any agent or developer write, generate, or leave comments in any code in this repository.**

- **Zero Comments in Code:**
  - No single-line comments (`//`)
  - No multi-line comments (`/* ... */`)
  - No documentation or JSDoc comments (`/** ... */`)
  - No template or markup comments (`<!-- ... -->`)
  - No stylesheet or preprocessor comments
  - No script or configuration comments (`# ...` in code)
- **Self-Documenting Code:** Code must be completely self-documenting through clean naming, modular structure, and strict TypeScript types.
- **No Placeholders:** Never write `// TODO`, `// FIXME`, or placeholder comments.

---

## 2. Project Tech Stack & Architecture

- **Frontend (`frontend/`):** Nuxt 4 + Vue 3 + TypeScript + Tailwind CSS 4 + Pinia
- **Design System:** Scandinavian minimalism, warm ivory (`#F4EFE3`), white dominant (`#FFFFFF`), forest green (`#183A2D`), muted gold (`#D6A84B`).
- **Typography & Localization:** Native RTL support, clean modern Persian typography (IranSansX), Persian digits for customer-facing numbers.
- **Authoritative Source of Truth:** Consult `frontend/DESIGN_SYSTEM.md` before making any visual, styling, or component modifications.

---

## 3. Automated Git Commit & Push Protocol

Upon completing any discrete task, feature implementation, bug fix, or refactoring:
1. Compose a Conventional Commits message (`<type>: <summary>` and detailed body).
2. Stage and commit changes.
3. Push directly to `main` branch (`git push origin main`).
