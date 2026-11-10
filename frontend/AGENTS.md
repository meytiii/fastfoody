# Fastfoody Agent Directives & Active Skills

This document configures the project-level agent skills and mandatory development directives for Google Antigravity and Antigravity IDE across the `fastfoody` repository.

---

## 1. Project Tech Stack & Aesthetics

- **Frontend:** Nuxt 3 + Vue 3 + TypeScript + Tailwind CSS
- **Backend:** Django + Django REST Framework (Python)
- **Design Philosophy:** Scandinavian minimalism, warm, inviting, premium, and approachable.
- **Color Palette:**
  - White dominant (65–75%): `#FFFFFF`
  - Warm Ivory (accents & alternate sections): `#F4EFE3`
  - Forest Green (primary brand, 15–25%): `#183A2D`
  - Muted Gold (accents, 5–10%): `#D6A84B`
  - Main Text: `#292B27` | Supporting Text: `#777A73` | Borders: `#E8E5DC`
- **Typography & Localization:** Native RTL support, clean modern Persian typography (IranSansX), Persian digits for customer-facing numbers.
- **Strict Anti-Patterns:** No glassmorphism, no neon glows, no excessive gradients, no heavy drop shadows, no generic 3-card AI templates.

---

## 2. Mandatory Design-System Compliance Rule

> [!IMPORTANT]
> **Before implementing, modifying, refactoring, or removing ANY frontend UI/UX element, you MUST consult [`frontend/DESIGN_SYSTEM.md`](file:///c:/Users/Mahdi/Desktop/Stuf/Github/fastfoody/frontend/DESIGN_SYSTEM.md) and ensure that your proposed change strictly complies with its rules.**

This rule applies to all new pages, existing pages, components, layouts, typography, colors, spacing, responsive behaviors, animations, and accessibility.

---

## 3. Active Skills Suite

The following skills are installed in `.agents/skills/` and active for Antigravity & Antigravity IDE:

| Skill | Slash Command / Trigger | Primary Responsibility |
| :--- | :--- | :--- |
| **graphify** | `/graphify` | Codebase architecture, module dependencies, knowledge graph navigation |
| **impeccable** | `/impeccable` | Frontend craft floor, design polish, tokens, responsive design |
| **hallmark** | `/hallmark` | Anti-AI-slop design system, structural variety, avoiding generic LLM UI |
| **ui-ux-pro-max** | `/ui-ux-pro-max` | Comprehensive UI/UX guide, layout logic, ergonomics, design systems |
| **ux-ui-agent-skills** | `/ux-ui-agent-skills` | Token-driven accessible UI, WCAG compliance, structured design audits |
| **taste / design-taste-frontend** | `/design-taste-frontend` | Elite editorial frontend taste, purposeful sections, equal edges |
| **high-end-visual-design** | `/high-end-visual-design` | Agency-grade luxury layouts, diffused ambient depth, airy hierarchy |
| **antislop** | `/antislop` | Zero generic AI slop in code, UI, copywriting, and mobile layouts |
| **humanizer** | `/humanizer` | Natural, human-written copy; eliminating corporate AI buzzwords |
| **caveman** | `/caveman` | Ultra-dense, token-efficient technical communication |
| **emilkowalski/skills** | `/animate`, `/choreograph`, etc. | Fluid motion, physics springs, interruptible gestures, mobile feel |

---

## 4. Skill Invocation & Execution Rules

1. **Architecture & Discovery:**
   - Use `graphify` (`/graphify`) to trace relationships between Django backend endpoints and Nuxt frontend components.

2. **UI & Component Design:**
   - Always verify implementations against `frontend/DESIGN_SYSTEM.md`.
   - Run frontend implementations through `antislop` and `hallmark` to prevent repetitive, templated layouts.
   - Employ `impeccable`, `ui-ux-pro-max`, and `high-end-visual-design` to enforce the Scandinavian minimalist aesthetic and strict spacing tokens (4px base scale).
   - Ensure native RTL handling and accessibility (WCAG AA).

3. **Motion & Interactivity:**
   - Apply Emil Kowalski motion principles (`animate`, `choreograph`, `gestures`): physics-based springs (stiffness 300, damping 30), interruptible drawer sheets, and subtle micro-interactions. Never use abrupt transitions or linear animations.

4. **Copywriting & Communication:**
   - Strip AI jargon with `humanizer` and `antislop-copywriting` to keep menu descriptions and interface copy warm, appetizing, and human.
   - Maintain concise, high-signal technical communication adhering to `caveman` efficiency.

---

## 5. Automated Git Commit & Push Protocol

Upon completing any task, feature, fix, or documentation update, all agents MUST automatically commit and push the changes:

1. **Commit Message Standards:**
   - **Summary:** Conventional Commits header (`feat:`, `docs:`, `fix:`, `refactor:`, etc.).
   - **Detailed Body:** Comprehensive explanation of what was changed, why, files affected, and design-system compliance verification.
2. **Execution:**
   - Stage appropriate files via `git add`.
   - Commit via `git commit -m "<Summary>" -m "<Description>"`.
   - Push directly to `main` branch: `git push origin main` (`https://github.com/meytiii/fastfoody`).

