---
trigger: always_on
description: Mandatory UI/UX and motion guidelines uniting design-taste-frontend, impeccable, hallmark, ui-ux-pro-max, ux-ui-agent-skills, high-end-visual-design, emil-design-eng, and Emil Kowalski animation skills.
---

# Design, UI/UX & Motion Directives

All frontend work in this project must adhere to the high-craft design and interaction standards established by the installed skill suite and `initiation.md`:

## 1. Visual Craft Floor & Anti-Slop (Hallmark, Taste, High-End Visual Design)
- **Brand Identity & Theme:** Scandinavian minimalism with warm ivory (`#F4EFE3`), white dominant (65–75%), forest green primary (`#183A2D`, 15–25%), and subtle muted gold accents (`#D6A84B`, 5–10%). Text: Main `#292B27`, Secondary `#777A73`, Borders `#E8E5DC`.
- **No AI Clichés:** Ban generic pill badges above headings/heroes (e.g. rounded chips with pulsing dots or icons like "پخت اصیل ناپلی · مواد اولیه ۱۰۰٪ ارگانیک" or "New Feature"), glassmorphism cards-in-cards, harsh 1px borders, thick black drop shadows, saturated purple/blue gradients, and generic 3-card Bootstrap grids. Allow typography and confident headlines to lead the section without decorative pill chips.
- **Structural Variety:** Design pages with rhythm and clear hierarchy. Avoid repetitive cookie-cutter layouts.
- **RTL & Persian:** Native RTL layout support, clean geometric Persian typography (IranSans), proper punctuation, and Persian digits for customer-facing numbers.

## 2. Component Polish & Accessibility (Impeccable, UI-UX Pro Max, UX-UI Agent Skills)
- **Accessibility:** WCAG AA contrast, explicit focus rings, keyboard navigability, semantic tags, and comfortable touch targets (minimum 44x44px).
- **Design Tokens:** Strict 4px spacing scale, consistent border radiuses, unified elevation via ultra-diffused ambient shadows.
- **State Handling:** Design for every edge state: empty states, loading skeletons, network errors, and form validations.

## 3. Motion, UI Polish & Micro-Interactions (`emil-design-eng`, `animate`, `gestures`, `choreograph`, `mobile-native`)
- **Active `emil-design-eng` Craft Standards:** Always apply `.agents/skills/emil-design-eng/SKILL.md`:
  - **Sub-300ms Custom Easing:** Keep standard UI transitions under `300ms` using custom `ease-out` curves (`cubic-bezier(0.23, 1, 0.32, 1)`), never `ease-in` and never `transition: all`.
  - **Natural Entry & Origin:** Never animate elements from `scale(0)`; enter from `scale(0.95)` with `opacity: 0`. Popovers scale from their trigger (`transform-origin`), while centered modals stay anchored to `center`.
  - **Tactile Press & Hover Safety:** Add `:active` `scale(0.97)` feedback on buttons/pressable elements, and gate hover animations behind `@media (hover: hover) and (pointer: fine)` to prevent sticky mobile tap states.
  - **Compositor-Only & Interruptible:** Animate only `transform`, `opacity`, and restrained `clip-path`; use CSS transitions or physical springs (`stiffness`, `damping`, `mass`) rather than keyframes for interruptible UI/drawers; never animate keyboard-initiated shortcuts.
- **Interruptible Gestures:** Drawer sheets, cart panels, and swipe actions must track the finger 1:1 and remain interruptible mid-flight.
- **Restraint:** Only animate with purpose (feedback, spatial continuity, state shifts). Respect `prefers-reduced-motion`.
- **Toasts & Feedback:** Use Sonner patterns for sleek, non-blocking toast notifications.
- **Review Output Format:** When reviewing UI/motion code under `/emil-design-eng`, output fixes in a markdown table with `| Before | After | Why |` columns.

