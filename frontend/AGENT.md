# Agent Directives & Engineering Standards — Fastfoody Repository

This document establishes universal development standards, architecture rules, and operational guidelines for all AI coding assistants working in the `fastfoody` repository.

---

## 1. Project Overview & Architecture

### 1.1. Project Summary
Fastfoody is a modern restaurant and food ordering web application combining Scandinavian minimalism with Persian culinary culture. The architecture consists of a mobile-first customer web interface, an administrative dashboard, and a robust RESTful API backend.

### 1.2. Architecture & Separation of Concerns
- **Frontend (`frontend/`):**
  - **Framework:** Nuxt 4 (Vue 3, Composition API, `<script setup lang="ts">`, modern `app/` structure).
  - **Styling:** Tailwind CSS 4 (CSS-first engine utilizing `@theme` directives).
  - **State Management:** Pinia stores for client-side state (cart, authentication, checkout).
  - **Localization:** Native Persian (RTL) with localized Persian numerals (`۰-۹`) and English/Latin support.
- **Backend (`backend/`):**
  - **Framework:** Django + Django REST Framework (DRF) in Python.
  - **API Contract:** Strict JSON-over-HTTP endpoints following REST conventions.
  - **Separation Rule:** The frontend and backend must remain strictly decoupled. Frontend components must communicate with backend services exclusively through standard REST endpoints; never embed backend template tags or monolithic server logic inside Nuxt components.

---

## 2. Documentation Authority & Source of Truth

To ensure alignment across all developers and AI agents, project documentation is structured hierarchically:

| Document | Authority Level | Primary Scope |
| :--- | :--- | :--- |
| **`frontend/DESIGN_SYSTEM.md`** | **Highest (Visual & UX)** | The absolute source of truth for all UI/UX decisions, color tokens, typography scales, layout grids, spacing units, responsive behaviors, component styles, and motion physics. |
| **`initiation.md`** | **Foundational (Requirements)** | Defines business objectives, user journeys, core feature scope, and initial project constraints. |
| **`GEMINI.md`** | **Agent-Specific (Gemini)** | Tailored operating guidelines and skill activations for Gemini-based agents. |
| **`AGENT.md`** | **Universal (All Agents)** | General software engineering standards, architecture rules, and development practices for all coding assistants. |

---

## 3. Mandatory Design-System Compliance Rule

> [!IMPORTANT]
> **Every frontend design implementation, component creation, refactoring, or visual modification MUST be checked against [`frontend/DESIGN_SYSTEM.md`](file:///c:/Users/Mahdi/Desktop/Stuf/Github/fastfoody/frontend/DESIGN_SYSTEM.md) before work begins.**

### 3.1. Non-Negotiable Directives
1. **No Rogue Design Decisions:** Agents must NOT independently invent new color hex codes, arbitrary spacing numbers, custom border radii, or novel component treatments outside the established tokens.
2. **Consult First:** Inspect `frontend/DESIGN_SYSTEM.md` to select the authorized tokens for background surfaces, text hierarchy, button variants, and spacing increments.
3. **Handling Gaps & Exceptions:**
   - If a new requirement is not explicitly defined in `DESIGN_SYSTEM.md`, evaluate the existing visual language and extend it consistently.
   - For any decision materially altering the visual identity, ask the user for confirmation.
   - When an approved pattern introduces a reusable standard, update `frontend/DESIGN_SYSTEM.md` first before applying it across multiple files.

---

## 4. Engineering Standards & Code Hygiene

### 4.1. Exploration Before Execution
- **Inspect Before Editing:** Never assume file structure or component APIs. Always read existing components, composables, and backend models before writing code.
- **Trace Architecture:** When investigating module relationships or data flows, trace endpoints from Django views/serializers to Nuxt composables and stores.

### 4.2. Component Reusability
- Reusable UI elements (Buttons, Input Fields, Badges, Modals, Product Cards) reside in `frontend/components/ui/` or `frontend/components/common/`.
- Do not duplicate component markup inline across multiple page templates.
- Maintain a single source of truth for UI components adhering to the design tokens.

### 4.3. Anti-Slop Code Hygiene
- **No Noisy Comments:** Banned obvious commentary (e.g., `// render template`, `// computed property`, `// import vue`). Keep comments strictly focused on non-obvious business logic, domain invariants, or edge-case handling.
- **No Placeholder Code:** Deliver complete, functional, production-ready code. Never leave `// TODO: implement later` placeholders or empty stub functions.
- **No Synthetic Bug-Masking Data:** Avoid hardcoded fallback mock data in production services that masks API failures.

### 4.4. Natural Copywriting Standards
- Restaurant copy, dish descriptions, and marketing headings must be warm, authentic, clear, and human.
- Strictly ban formulaic corporate AI buzzwords (*pivotal, delve, testament, landscape, tapestry, vibrant, nestled within*).
- Provide high-quality, culturally natural Persian text with correct punctuation and Persian digits.

---

## 5. Accessibility, Localization & Responsive Standards

### 5.1. Accessibility (WCAG 2.1 AA)
- Semantic HTML tags (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`) must be used for layout structure.
- Minimum interactive touch targets must measure **at least 44×44px**.
- High-contrast text must meet minimum 4.5:1 contrast ratios.
- All interactive controls must feature visible, accessible focus indicators (`:focus-visible`).
- Cart totals and dynamic live regions must declare `aria-live="polite"`.

### 5.2. Native Persian RTL Support
- All layouts must enforce `dir="rtl"`.
- Use CSS logical properties (`margin-inline`, `padding-inline`, `inset-inline`, `border-inline`) exclusively.
- Format all customer-facing prices, review counts, and numerical data in Persian digits (`۰-۹`).
- Enclose telephone numbers, tracking IDs, and URLs in `<bdi>` or LTR containers.

### 5.3. Responsive Delivery
- The customer ordering interface is **mobile-first**. Ensure 2-column mobile product grids, accessible touch navigation, and smooth bottom-sheet drawers.
- Test across standard breakpoints: Mobile (`<640px`), Tablet (`768px–1023px`), Desktop (`1024px+`).

---

## 6. Asset Management & Safety

- **Preserve Existing Assets:** Existing assets, icons, fonts, and reference files (including `reference.png`) are permanent project resources and must NEVER be deleted, overwritten, or modified.
- **Food Photography Standards:** Images must feature clean overhead studio food photography with neutral ceramic dishware and clean cutout masks.
- **Icon Consistency:** Use uniform line/outline icons with `1.5px` stroke width. Do not mix unrelated icon styles or heavy filled glyphs.

---

## 7. Scope Discipline

- **No Unrelated Modifications:** Modify only the files directly required to fulfill the user's explicit request. Do not format, reorder, or refactor unrelated files.
- **Preserve Functionality:** Ensure existing routes, state stores, and backend endpoints remain unbroken when introducing new features.

---

## 8. Automated Git Commit & Push Protocol

Upon completing any discrete task, feature implementation, bug fix, or documentation change, agents MUST automatically commit and push their changes:

### 8.1. Workflow Process
1. **Compose a Comprehensive Commit Message:**
   - **Summary Line:** Conventional Commits header (`<type>: <short imperative summary>`).
   - **Detailed Description Body:** Document what was changed, why the change occurred, files impacted, and verification of compliance with `frontend/DESIGN_SYSTEM.md`.
2. **Stage & Commit:**
   - Review `git status` to avoid committing unwanted artifacts or environment files.
   - Stage appropriate files and commit with the detailed message.
3. **Push to Main:**
   - Push directly to the `main` branch of `https://github.com/meytiii/fastfoody`:
     ```bash
     git push origin main
     ```
   - Verify that the push succeeds without errors.


