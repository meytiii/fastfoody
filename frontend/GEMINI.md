# Gemini Agent Directives — Fastfoody Repository

This document establishes project-specific instructions and operating rules for Gemini-based AI coding agents working on the `fastfoody` codebase.

---

## 1. Project Understanding & Repository Architecture

### 1.1. Project Overview
Fastfoody is a premium Scandinavian-inspired restaurant and online ordering platform featuring a customer-facing web application and an administrative management dashboard. The user experience is calm, warm, and appetizing, emphasizing high-quality food photography, clean typography, and responsive, fluid interactions.

### 1.2. Technology Stack
- **Frontend (`frontend/`):** Nuxt 3 + Vue 3 + TypeScript, Tailwind CSS, Pinia state management.
- **Backend (`backend/`):** Django + Django REST Framework (Python), PostgreSQL / SQLite.
- **Localization:** Native Persian (RTL) interface with localized Persian numerals (`۰-۹`) and English/Latin capability.

### 1.3. Core References
- **`frontend/DESIGN_SYSTEM.md`:** The authoritative, single source of truth for all UI, UX, styling, component design, color, typography, spacing, and interaction rules.
- **`initiation.md`:** Business requirements, feature specifications, brand identity, and project constraints.
- **`reference.png`:** Primary visual reference benchmark for page composition, section rhythms, and layout structures.

---

## 2. Mandatory Design-System Compliance Rule

> [!IMPORTANT]
> **Before implementing, modifying, refactoring, or removing ANY frontend UI/UX element, you MUST consult [`frontend/DESIGN_SYSTEM.md`](file:///c:/Users/Mahdi/Desktop/Stuf/Github/fastfoody/frontend/DESIGN_SYSTEM.md) and ensure that your proposed change strictly complies with its rules.**

This rule is **strictly non-negotiable** and applies unconditionally to:
- Creating new pages, layouts, or routes.
- Modifying or refactoring existing views and components.
- Selecting colors, background surfaces, text treatments, or borders.
- Applying margin, padding, column gaps, and layout grids.
- Choosing font sizes, weights, line heights, and letter spacing.
- Structuring desktop, tablet, and mobile responsive adaptations.
- Configuring animation timings, physics springs, transitions, and hover states.
- Formatting customer-facing prices, numerals, dates, and currency labels.
- Ensuring touch targets, contrast ratios, and keyboard accessibility.

### 2.1. Handling Design Conflicts & Extensions
If a user prompt or task requires a pattern not explicitly covered or seemingly conflicting with `frontend/DESIGN_SYSTEM.md`:
1. **Identify the conflict:** State the specific discrepancy between the request and the design system tokens.
2. **Explain the reason:** Detail why the proposed pattern deviates from established tokens (e.g. contrast, spacing scale, brand color harmony).
3. **Align before proceeding:** Never silently introduce ad-hoc HEX colors, arbitrary spacing pixels, or unapproved visual effects into the codebase.
4. **Extend deliberately:** When an approved architectural change establishes a new reusable design rule, update `frontend/DESIGN_SYSTEM.md` first to preserve single-source-of-truth integrity.

---

## 3. Frontend Development Directives

### 3.1. Code Quality & Architecture
- **Layered Nuxt 3 Structure:**
  - `components/`: Pure, reusable, accessible UI elements adhering strictly to design tokens.
  - `pages/`: Route-level views orchestrating page layouts and data fetching.
  - `composables/`: Reusable reactive business logic and headless API hooks.
  - `stores/`: Pinia state management for cart state, user session, and checkout progress.
- **Read Before Writing:** Always inspect existing components and composables before creating new ones. Never reinvent an existing button, modal, or input component.
- **No Unnecessary Dependencies:** Rely on the established stack. Do not introduce extraneous animation, styling, or icon libraries when existing packages fulfill the requirement.

### 3.2. RTL & Persian Typography Standards
- Always enforce `dir="rtl"` and use CSS logical properties (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`). Hardcoded `left`, `right`, `margin-left`, or `margin-right` in stylesheets are prohibited.
- Use `IranSansX` for Persian text and localized Persian numerals (`۰-۹`) for all prices and quantities.
- Mirror directional icons (progress arrows, forward chevrons) while keeping non-directional icons (search, cart, user, star) un-mirrored.

### 3.3. Motion & Micro-Interactions (Emil Kowalski Philosophy)
- Use physics-based springs (stiffness: 300, damping: 30) for drawer and modal transitions.
- Interactive controls must provide snappy feedback (`active:scale-[0.98]`, card hover `translateY(-3px)`).
- Use Sonner non-blocking toast notifications for cart updates.
- Respect `prefers-reduced-motion` at all times.

---

## 4. Anti-Slop & Professional Craft Standards

### 4.1. Zero-Slop Hygiene (`antislop`, `hallmark`)
- **No Cliché Layouts:** Ban generic 3-card Bootstrap grids, saturated neon gradients, and nested glassmorphism cards.
- **No Obvious Code Comments:** Strip noisy AI commentary (e.g. `// render component`, `// return template`). Document only critical invariants, complex domain calculations, or upstream workarounds.
- **No Synthetic Placeholders:** Write production-ready code with complete implementations. Do not leave placeholder functions, stubbed empty templates, or synthetic mock data masking real logic.

### 4.2. Natural Copywriting (`humanizer`)
- Eliminate formulaic AI corporate buzzwords (*testament, pivotal, delve, landscape, tapestry, vibrant, nestled within*).
- Deliver warm, authentic, concise, and appetizing Persian culinary copy.

### 4.3. Communication Efficiency (`caveman`)
- Provide dense, high-signal technical explanations. Eliminate conversational filler, redundant apologies, and unrequested boilerplate overviews.
