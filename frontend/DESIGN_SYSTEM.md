# Fastfoody UI/UX Design System & Visual Specification

> **Version:** 1.0.0  
> **Status:** Authoritative / Implementation-Ready  
> **Framework:** Nuxt 3 + Vue 3 + TypeScript  
> **Backend Integration:** Django REST Framework  
> **Target Platforms:** Mobile Web (Primary / Mobile-First), Tablet, Desktop  
> **Localization:** Native Persian (RTL) with localized Persian numerals (`۰-۹`) and English/Latin compatibility  
> **Primary References:** `reference.png` (Visual Architecture), `initiation.md` (Project Directives & Constraints)  

---

## 1. Design Philosophy & Visual Identity

### 1.1. Core Identity: Scandinavian Warmth Meets Persian Hospitality
The Fastfoody digital experience balances the clean functional elegance of **Scandinavian minimalism** with the warm, generous hospitality of Persian culinary culture. It rejects the hyperactive, saturated, neon-lit clichés of standard fast-food platforms in favor of a calm, curated, and appetizing digital environment.

- **White-Dominant Clarity (65–75%):** Spacious, uncrowded canvases with generous whitespace that elevate food photography into art.
- **Organic Earthiness (15–25%):** Deep Forest Green (`#183A2D`) grounds the brand in natural quality, freshness, and quiet sophistication.
- **Tactile Warmth:** Warm Ivory (`#F4EFE3`) provides comfortable section alternating, making long browsing sessions easy on the eyes.
- **Refined Accents (5–10%):** Muted Gold (`#D6A84B`) provides subtle luxury on ratings, badges, and review stars without ever becoming gaudy or overwhelming.

### 1.2. Visual Personality
- **Appetizing & Fresh:** Real, unpretentious food photography featuring studio lighting, clean circular ceramic plates, and natural ingredients.
- **Calm & Orderly:** Strict 4px spacing rhythm, uniform card elevations, and predictable layout structures.
- **Accessible & Inclusive:** Native right-to-left (RTL) layout from the ground up, WCAG AA color contrast, explicit keyboard focus rings, and touch targets exceeding 44×44px.
- **Tactile & Fluid:** Physical spring transitions (stiffness: 300, damping: 30) on interactive sheets, non-blocking Sonner toast feedback, and crisp micro-interactions.

### 1.3. Relationship to `reference.png`
`reference.png` serves as the primary visual benchmark for layout sequencing, composition, and component architecture:
1. **Preserved from Reference:**
   - The organic curved hero mask transitioning into food dish display.
   - High-contrast hero section with dark green brand background and light food presentation.
   - Category navigation pills with circular icon containers.
   - Product cards featuring circular overhead food photography, clean typography, 5-star rating, price, and CTA.
   - Two-row / 4-column product grid with category filter tabs.
   - Mobile application promo banner with floating device perspectives.
   - Table reservation form block paired with address and contact details.
   - Customer review cards and carousel presentation.
   - Editorial blog article layout.
   - Multi-column dark green footer with newsletter subscription and social links.
2. **Adapted for Fastfoody (`initiation.md` Directives):**
   - **Color Shift:** The loud orange primary buttons (`#FF6B00`) from the reference are replaced with the authoritative brand **Forest Green (`#183A2D`)** on light backgrounds, with **Muted Gold (`#D6A84B`)** used exclusively for ratings, badges, and delicate highlights.
   - **Navigation Architecture:** Replaced the full-width edge-to-edge navbar with a modern **Floating Island Navigation** container (dock style) on desktop, and a streamlined top bar paired with a floating cart pill on mobile.
   - **Typography & Localization:** Replaced English Latin display serifs with **IranSansX** — an elegant, geometric modern Persian typeface — supporting native RTL alignment, Persian numerals (`۰-۹`), and Tomans (`تومان`) currency formatting.
   - **Interactive E-Commerce Flows:** Extended beyond the reference's static landing display to define the full interactive e-commerce suite: Slide-out Cart Drawer, Single-Page Checkout, and Product Detail Modals.

### 1.4. Absolute Anti-Patterns (Banned AI Slop & Outdated Clichés)
- **NO Glassmorphism Cards-in-Cards:** No semi-transparent layered frosted glass boxes stacked upon frosted glass.
- **NO Harsh Black Drop Shadows:** Banned `rgba(0,0,0,0.25)` or `shadow-xl` default styles. Only ultra-diffused ambient shadows are permitted.
- **NO Saturated Blue/Purple Gradients:** No AI-generated neon gradients or high-tech glows.
- **NO Generic 3-Card Bootstrap Grids:** Layouts must follow the responsive 4-column desktop / 2-column mobile system with asymmetrical accents where appropriate.
- **NO Obtrusive Decorative Noise:** No decorative blob vectors, floating geometric confetti, or synthetic AI clutter.

---

## 2. Color System

### 2.1. Primary Palette Specifications

| Token Name | Hex Code | RGB | Purpose & Usage Guidelines |
| :--- | :--- | :--- | :--- |
| `--color-brand-forest` | `#183A2D` | `rgb(24, 58, 45)` | **Primary brand color**. Used for dark hero sections, primary buttons on light surfaces, active indicators, and major headers. |
| `--color-brand-forest-deep` | `#12251D` | `rgb(18, 37, 29)` | Deep forest tone for footer background, high-contrast badges, and dark card hover states. |
| `--color-brand-forest-light` | `#224E3D` | `rgb(34, 78, 61)` | Hover state for Forest Green buttons, secondary dark accents. |
| `--color-accent-gold` | `#D6A84B` | `rgb(214, 168, 75)` | **Accent color (5–10%)**. Review stars, promotional badges, selected tab indicator dots, subtle dividers. Never used as massive background fills. |
| `--color-accent-gold-hover` | `#C4963A` | `rgb(196, 150, 58)` | Hover/pressed state for gold elements and interactive badges. |
| `--color-accent-gold-soft` | `#F8F3E8` | `rgb(248, 243, 232)` | Soft gold tint for badge backgrounds, highlight pill containers. |
| `--color-surface-ivory` | `#F4EFE3` | `rgb(244, 239, 227)` | **Warm background sections**. App promo section, reservation background, alternating section fills. |
| `--color-surface-cream` | `#FAF7F2` | `rgb(250, 247, 242)` | Subtle tinted card background, secondary input backgrounds. |
| `--color-surface-white` | `#FFFFFF` | `rgb(255, 255, 255)` | **Primary canvas background (65–75%)**. Main page fill, product cards, dialogs, forms. |

### 2.2. Neutral & Text Colors

| Token Name | Hex Code | Purpose |
| :--- | :--- | :--- |
| `--color-text-primary` | `#292B27` | Headings, dish names, primary body copy, price tags. High contrast (14.2:1 against white). |
| `--color-text-secondary` | `#777A73` | Supporting descriptions, ingredients list, category subtitle, metadata. Contrast (4.8:1 against white). |
| `--color-text-muted` | `#9EA199` | Input placeholders, disabled text, breadcrumb separators. |
| `--color-text-inverse` | `#FFFFFF` | Text on Forest Green backgrounds, hero section typography. |
| `--color-border-subtle` | `#E8E5DC` | Primary card borders, table dividers, input boundaries, category pill outlines. |
| `--color-border-focus` | `#183A2D` | Form input focus ring, selected state borders. |

### 2.3. Semantic & Feedback Colors

| Token Name | Hex Code | Purpose |
| :--- | :--- | :--- |
| `--color-success` | `#2E7D32` | Order confirmed badge, item added confirmation, in-stock indicators. |
| `--color-success-bg` | `#EDF7ED` | Success toast and alert background container. |
| `--color-warning` | `#ED6C02` | Low stock notices, dietary alerts, pending payment status. |
| `--color-warning-bg` | `#FFF4E5` | Warning alert container. |
| `--color-danger` | `#D32F2F` | Form validation errors, remove-from-cart actions, out-of-stock badge. |
| `--color-danger-bg` | `#FDE8E8` | Error toast and validation message background. |
| `--color-info` | `#0288D1` | Delivery radius notices, operational info badges. |
| `--color-info-bg` | `#E1F5FE` | Informational callout background. |

### 2.4. Elevation & Ambient Shadow Tokens
To prevent heavy, dirty shadows, all elevations utilize ultra-diffused multi-stop shadows with subtle forest-tinted ambient occlusion:

```css
/* Zero-elevation: Flat borders */
--shadow-flat: none;

/* Low-elevation: Product cards, category pills, buttons */
--shadow-sm: 0 1px 3px rgba(24, 58, 45, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);

/* Default-elevation: Card hover, floating island header, quick cart pill */
--shadow-md: 0 4px 16px rgba(24, 58, 45, 0.06), 0 2px 6px rgba(0, 0, 0, 0.03);

/* High-elevation: Slide-out cart drawer, product details modal, reservation form */
--shadow-lg: 0 12px 32px rgba(24, 58, 45, 0.08), 0 4px 12px rgba(0, 0, 0, 0.04);

/* Deep-elevation: Dropdown menus, tooltips, popovers */
--shadow-dropdown: 0 8px 24px rgba(24, 58, 45, 0.10);
```

---

## 3. Typography System

### 3.1. Font Families & Loading
1. **Primary Persian Font:** `IranSansX` (or `IRANSans`)
   - Fallbacks: `Vazirmatn, system-ui, -apple-system, Segoe UI, Tahoma, sans-serif`
   - Characteristics: Clean, geometric, contemporary legibility, open counters, optimized for digital displays and menus.
2. **Secondary / Latin Companion Font:** `Plus Jakarta Sans`
   - Fallbacks: `Inter, system-ui, sans-serif`
   - Characteristics: Geometric proportions that seamlessly pair with IranSansX for English words, URLs, and brand marks.
3. **Numerals:** Localized Persian numerals (`۰-۹`) must be rendered for customer-facing prices, preparation times, calorie counts, and phone numbers via `font-feature-settings: "ss01"` or explicit Persian number formatting utilities.

### 3.2. Typographic Hierarchy Scale

| Level | Size (Desktop) | Size (Mobile) | Line Height | Weight | Letter Spacing | Purpose & Usage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Display Hero** | `48px` (`3.0rem`) | `32px` (`2.0rem`) | `1.25` | `700` (Bold) | `-0.02em` | Hero section main headline (`تجربه طعم‌های اصیل...`) |
| **Heading 1** | `36px` (`2.25rem`) | `26px` (`1.625rem`) | `1.3` | `700` (Bold) | `-0.015em` | Major section headers ("منوی غذاها", "رزرو میز") |
| **Heading 2** | `28px` (`1.75rem`) | `22px` (`1.375rem`) | `1.35` | `600` (SemiBold) | `-0.01em` | Category section titles, modal headers, card group titles |
| **Heading 3** | `20px` (`1.25rem`) | `18px` (`1.125rem`) | `1.4` | `600` (SemiBold) | `0` | Product card titles, blog card headlines, drawer headers |
| **Heading 4** | `17px` (`1.0625rem`) | `16px` (`1.0rem`) | `1.4` | `500` (Medium) | `0` | Subsection titles, form group headings |
| **Body Large** | `18px` (`1.125rem`) | `16px` (`1.0rem`) | `1.6` | `400` (Regular) | `0` | Hero intro paragraphs, blog excerpt intros |
| **Body Default** | `15px` (`0.9375rem`) | `14px` (`0.875rem`) | `1.6` | `400` (Regular) | `0` | Standard body text, product descriptions, reviews |
| **Body Small** | `13px` (`0.8125rem`) | `12px` (`0.75rem`) | `1.5` | `400` (Regular) | `0` | Nutritional notes, helper text, input hints |
| **Caption / Badge** | `12px` (`0.75rem`) | `11px` (`0.6875rem`) | `1.4` | `500` (Medium) | `+0.01em` | Star rating text, category tags, timestamps |
| **Price Display** | `20px` (`1.25rem`) | `17px` (`1.0625rem`) | `1.2` | `700` (Bold) | `0` | Product pricing (`۱۲۵٬۰۰۰ تومان`) |
| **Button Text** | `15px` (`0.9375rem`) | `14px` (`0.875rem`) | `1.0` | `600` (SemiBold) | `0` | CTA buttons, pill buttons, filter tabs |

---

## 4. Layout & Spacing System

### 4.1. 4px Baseline Spacing Scale
All margins, paddings, and component dimensions derive strictly from an increment-of-4 scale:

| Token | Pixels | Rem Value | Example Usage |
| :--- | :--- | :--- | :--- |
| `--space-1` | `4px` | `0.25rem` | Badge padding, micro gap between star icon & rating text |
| `--space-2` | `8px` | `0.5rem` | Icon-to-label spacing, compact button padding, item gaps |
| `--space-3` | `12px` | `0.75rem` | Card internal content gaps, mobile grid column gap |
| `--space-4` | `16px` | `1.0rem` | Default component padding, input field padding, mobile margins |
| `--space-5` | `20px` | `1.25rem` | Card body padding, navigation item spacing |
| `--space-6` | `24px` | `1.5rem` | Desktop grid gutters, drawer padding, card header margin |
| `--space-8` | `32px` | `2.0rem` | Section subtitle bottom margin, form row gaps |
| `--space-10` | `40px` | `2.5rem` | Medium section block spacing |
| `--space-12` | `48px` | `3.0rem` | Mobile section vertical spacing |
| `--space-16` | `64px` | `4.0rem` | Tablet section vertical spacing |
| `--space-20` | `80px` | `5.0rem` | Standard desktop section padding |
| `--space-24` | `96px` | `6.0rem` | Major desktop landing section padding (Hero to Menu) |

### 4.2. Container & Grid Specifications
- **Maximum Content Width:** `1280px` (`max-w-7xl`), centered with `margin-inline: auto`.
- **Desktop Page Margins:** `32px` (`px-8`) on viewports `1024px+`.
- **Tablet Page Margins:** `24px` (`px-6`) on viewports `768px - 1023px`.
- **Mobile Page Margins:** `16px` (`px-4`) on viewports `<768px`.
- **Desktop Grid (Product Menu):** 4 equal columns with `24px` gutter (`grid-cols-4 gap-6`).
- **Tablet Grid (Product Menu):** 3 equal columns (`grid-cols-3 gap-5`) or 2 columns (`grid-cols-2 gap-4`).
- **Mobile Grid (Product Menu):** 2 balanced columns with `12px` gutter (`grid-cols-2 gap-3`).

---

## 5. Responsive Strategy & Breakpoints

### 5.1. Standard Breakpoints

```css
--breakpoint-sm: 640px;   /* Large phones / mini tablets */
--breakpoint-md: 768px;   /* Standard tablets (iPad portrait) */
--breakpoint-lg: 1024px;  /* Laptops / desktop displays */
--breakpoint-xl: 1280px;  /* Full desktop standard container */
--breakpoint-2xl: 1536px; /* Ultra-wide monitors */
```

### 5.2. Viewport-Specific Behavior Matrix

| Surface | Desktop (≥ 1024px) | Tablet (768px – 1023px) | Mobile (< 768px) |
| :--- | :--- | :--- | :--- |
| **Navigation** | Floating centered island header with full link list, search, cart, and "سفارش آنلاین" CTA. | Condensed floating island header; navigation links collapse into drawer menu. | Fixed minimal top bar (logo + menu toggle) + Floating quick-cart pill (bottom-left in RTL). |
| **Hero Section** | Split layout: Right side headline & CTAs, left side organic curved mound with cutout plate. | Vertical stack: Headline on top, centered dish plate underneath. | Compact stack: Tight headline, food plate centered with scaled dimensions (max `280px`). |
| **Category Bar** | Horizontal carousel with next/prev arrows showing 6–8 visible category pills. | Touch-scrollable horizontal carousel with subtle fade indicators. | Native horizontal swipe carousel without visible scrollbars (`scrollbar-none`). |
| **Special Dishes** | 4-item horizontal card row on dark green background with dot pagination. | 2-item row with pagination. | Horizontal swipe cards with partial peek of the next card (`w-[82vw]`). |
| **Menu Grid** | 4 columns (`grid-cols-4`), spacious card layout. | 3 or 2 columns. | Strict 2-column balanced grid (`grid-cols-2 gap-3`). |
| **Product Detail** | Centered modal dialog or dedicated page view with dual-column layout. | Centered modal with adjusted image ratio. | Bottom sheet drawer opening to `90vh` height with swipe-down dismissal. |
| **Cart Experience**| Slide-out right-side (in RTL: left-side) drawer (`420px` width) with backdrop dim. | Slide-out drawer (`380px` width). | Full-screen or bottom sheet drawer (`100%` width). |

---

## 6. Component Design Guidelines

### 6.1. Header & Navigation

#### A. Desktop Floating Island Header
- **Container:** Centered floating container (`max-w-5xl`), placed `16px` below top viewport edge (`top-4`).
- **Styling:** Background `rgba(255, 255, 255, 0.92)` with `backdrop-filter: blur(12px)`.
- **Border & Radius:** `border: 1px solid var(--color-border-subtle)` (`#E8E5DC`), `border-radius: 9999px` (full pill shape).
- **Shadow:** `var(--shadow-md)` (soft ambient elevation).
- **Height & Padding:** Height `64px`, horizontal padding `24px` (`px-6`).
- **Elements (RTL Order):**
  1. *Right:* Brand Logo (Forest green leaf/plate emblem + "فست‌فودی" in IranSansX Bold).
  2. *Center:* Navigation items ("صفحه اصلی", "منوی غذا", "درباره ما", "رزرو میز", "تماس"). Neutral text `#292B27`, hover color `#183A2D` with subtle dot indicator.
  3. *Left:* Search trigger icon button + Cart button with gold badge (`#D6A84B`) + Primary "سفارش آنلاین" pill button.

#### B. Mobile Top Bar & Floating Cart Pill
- **Top Bar:** Fixed top bar, height `56px`, white background with subtle border-b `#E8E5DC`. Contains Hamburger Menu trigger, centered brand logo, and search icon.
- **Floating Cart Pill:** Fixed at bottom-start (bottom-left in RTL) `16px` above screen bottom.
  - Height: `52px`, Pill radius `9999px`.
  - Color: Forest Green `#183A2D`, text White `#FFFFFF`.
  - Content: Cart Icon + Persian item count badge in Gold (`#D6A84B`) + Total price in Tomans.
  - Shadow: Deep elevation `0 8px 24px rgba(24, 58, 45, 0.25)`.

### 6.2. Hero Section
- **Background:** Split layout. Right side (RTL start) features a dark Forest Green curved container (`border-radius: 0 0 64px 0` in RTL, inverted from reference), flowing into crisp White canvas on the left.
- **Customer Social Proof Badge:** Rounded pill with overlapping customer avatars, 5 Muted Gold stars, and bold counter ("+۳٬۵۰۰ نظر رضایت‌بخش").
- **Headline:** IranSansX Bold, `48px`, White `#FFFFFF`, with line-height `1.25`.
- **Action Buttons:**
  - Primary CTA: "سفارش آنلاین" (Pill shape, Muted Gold accent or Crisp White on dark surface, bold text).
  - Secondary CTA: "مشاهده ویدیو" (Circular outlined play icon + regular text).
- **Food Display Visual:** Clean cutout ceramic dish with fresh spring rolls / healthy bowl resting on a soft organic ivory mound with subtle shadow.

### 6.3. Category Navigation Carousel
- **Container:** White section with horizontal scroll / carousel controls.
- **Category Pill:**
  - Container: Rounded-2xl (`16px`), background `#FAF7F2`, border `1px solid #E8E5DC`.
  - Content: Top circular icon/illustration container (`48×48px`), bottom category title (e.g. "برگرها", "پاستا", "ساندویچ", "سالادها", "نوشیدنی").
  - Hover state: Background `#F4EFE3`, subtle border color change.
  - Active state: Background `#183A2D`, icon background `#FFFFFF`, text `#FFFFFF`.
  - Carousel Controls: Circular buttons (`40×40px`) with Forest Green outline or fill.

### 6.4. Product Cards (Main Menu Grid)
- **Container Dimensions:** Minimum width `100%`, flex column layout, `border-radius: 16px`.
- **Surface & Border:** Pure White background (`#FFFFFF`), border `1px solid var(--color-border-subtle)` (`#E8E5DC`).
- **Padding:** `16px` (`p-4`) on desktop; `12px` (`p-3`) on mobile.
- **Image Treatment:**
  - Aspect ratio: `1:1` square container.
  - Presentation: High-resolution overhead circular food photography on neutral/transparent plate.
  - Hover micro-interaction: Image smoothly scales up `scale(1.04)` over `200ms` with `overflow: hidden`.
- **Content Hierarchy:**
  1. *Category / Diet Tag:* Small muted text (e.g. "غذای ارگانیک" / "تند").
  2. *Product Title:* IranSansX SemiBold `16px` (`14px` mobile), color `#292B27`, single line with ellipsis.
  3. *Rating:* 5 stars in Muted Gold (`#D6A84B`) + average score in Persian digits (`۴.۸`).
  4. *Price & Action Row:*
     - Price: IranSansX Bold `17px`, Forest Green `#183A2D` or Main Text `#292B27`, followed by "تومان".
     - Action Button: Compact pill button "افزودن" (Add) with plus icon, or full-width button.
     - On desktop: Secondary button transforms to Forest Green on hover.
     - On mobile: Circular `36×36px` quick-add button with `+` icon for effortless one-tap ordering.

### 6.5. Product Details Modal / Bottom Sheet
- **Presentation:** Centered modal dialog (`max-w-2xl`) on desktop; full bottom sheet (`90vh`) on mobile.
- **Header:** Sticky top bar with product name, close `×` button, and dietary badges.
- **Media:** Large hero food dish photography with ingredient highlights.
- **Customization Options:**
  - Radio options for size / portion (Single, Double, Combo).
  - Checkboxes for add-ons (extra cheese, special sauce, extra avocado).
  - Special instructions textarea (`border: 1px solid #E8E5DC`, focus `#183A2D`).
- **Sticky Footer Action:** Stepper quantity counter (`- 1 +`) + "افزودن به سبد خرید" CTA button displaying total calculated price in Persian digits.

### 6.6. Slide-Out Cart Drawer
- **Placement:** Opens from the start edge (left side in RTL, right side in LTR).
- **Width:** `420px` on desktop; `100%` on mobile.
- **Backdrop:** Semi-transparent dark overlay `rgba(18, 37, 29, 0.45)` with `backdrop-filter: blur(4px)`.
- **Sections:**
  1. *Drawer Header:* "سبد خرید شما" (Your Cart) + item count badge + close icon.
  2. *Item List (Scrollable):*
     - Thumbnail image (`64×64px` rounded-xl).
     - Title, selected modifiers, and unit price.
     - Quantity stepper (`- 1 +`) with minimum touch size `32×32px`.
     - Delete action icon with confirmation.
  3. *Drawer Footer (Sticky):*
     - Subtotal row.
     - Delivery fee / Tax row (or "محاسبه در مرحله بعد").
     - Total payable row in bold `20px` typography.
     - Primary Action Button: "تکمیل و پرداخت" (Checkout) in Forest Green `#183A2D`.

### 6.7. Single-Page Checkout Form
- **Layout:** 2-column on desktop (`2/3` form details, `1/3` sticky order summary); 1-column stack on mobile.
- **Steps / Accordion Panels:**
  1. *Customer Information:* Full name, mobile phone number (with SMS verification support).
  2. *Delivery Address:* Map selector / address input, apartment, postal code, delivery notes.
  3. *Delivery Time:* "سریع‌ترین زمان ممکن" (ASAP) or scheduled delivery slot picker.
  4. *Payment Method:* Online payment gateways (Saman, Mellat, ZarinPal), cash on delivery.
- **Form Input Design:**
  - Height `48px`, border-radius `12px`, border `1px solid #E8E5DC`.
  - Background `#FFFFFF` (or `#FAF7F2` in inactive state).
  - Focus state: `border-color: #183A2D`, box-shadow `0 0 0 3px rgba(24, 58, 45, 0.12)`.
  - Error state: `border-color: #D32F2F`, error text `12px` below input.

### 6.8. Table Reservation Section
Directly adapting the reservation card from `reference.png`:
- **Card Background:** Crisp White (`#FFFFFF`) with subtle border `#E8E5DC` and high ambient shadow `var(--shadow-lg)`.
- **Form Fields:** 2-column grid for Name, Email, Phone, Date, Time, Party Size, and Notes textarea.
- **Submit Button:** Full-width Forest Green `#183A2D` pill button "ثبت درخواست رزرو".
- **Companion Column:** Restaurant physical address, phone numbers, working hours, and appetizing roasted food platter photograph.

### 6.9. Customer Testimonials & Reviews
- **Section Rhythm:** Warm Ivory background (`#F4EFE3`).
- **Cards:** Asymmetrical cards — 1 active card in dark Forest Green (`#183A2D` with white text) and companion cards in White (`#FFFFFF`).
- **Content:** Patron avatar (`48×48px`), decorative quote icon in Muted Gold, review text, patron name, and verified diner badge.
- **Navigation:** Next / Previous circular arrow buttons.

### 6.10. Footer
- **Background:** Deep Forest Charcoal (`#12251D`).
- **Typography:** Headings in Muted Gold `#D6A84B` or White `#FFFFFF`; links and body in `#A0A59C`.
- **Columns (4 Columns on Desktop, 1 on Mobile):**
  1. *Brand Info:* Logo + mission statement + address, email, phone.
  2. *Quick Links:* Menu, About, Table Reservation, FAQ, Terms.
  3. *Opening Hours:* Weekdays and weekends schedule.
  4. *Newsletter:* Email input field + "عضویت" button + Social icons (Instagram, Telegram, LinkedIn).
- **Bottom Bar:** Copyright notice and legal licensing info with border-t `rgba(255, 255, 255, 0.08)`.

---

## 7. Interaction & Motion Design

### 7.1. Motion Principles (Emil Kowalski Philosophy)
Animations must never be decorative fluff; they exist to provide **spatial orientation**, **tactile feedback**, and **state continuity**.

1. **Physical Springs over Easing:** Transitions for drawers, modals, and sheets use spring dynamics rather than rigid `cubic-bezier`:
   ```javascript
   // Recommended Spring Token
   const springConfig = {
     stiffness: 300,
     damping: 30,
     mass: 1.0
   };
   ```
2. **Interruptible Gestures:** Drawer sheets and modals must track the user's touch 1:1. Swiping down on a mobile bottom sheet or dragging the cart drawer must allow interrupting, reversing, or releasing mid-flight without snapping glitches.
3. **Restraint:** Only animate interactive states and layout shifts. Do not animate text continuously or use distracting scroll-triggered parallax on body copy.

### 7.2. Micro-Interaction Specifications

| Interaction | Target Element | Transformation / Transition | Timing / Physics |
| :--- | :--- | :--- | :--- |
| **Button Active** | All buttons | `scale(0.98)` on active press | `100ms ease-out` |
| **Card Hover** | Product cards, Blog cards | `translateY(-3px)`, shadow `var(--shadow-md)` | `200ms cubic-bezier(0.16, 1, 0.3, 1)` |
| **Dish Image Hover**| Product card thumbnail | `scale(1.04)` inside overflow hidden | `250ms ease-out` |
| **Pill Filter Tab** | Category tabs | Background color shift + subtle scale | `150ms ease-in-out` |
| **Drawer Slide** | Cart Drawer / Mobile Nav | `translateX(0)` from off-screen | `Spring (stiffness: 320, damping: 32)` |
| **Modal Scale** | Product modal / Dialog | `opacity: 0 -> 1`, `scale: 0.95 -> 1.0` | `200ms cubic-bezier(0.16, 1, 0.3, 1)` |
| **Toast Entrance** | Sonner notifications | Slide up `16px` + fade in | `Spring (stiffness: 400, damping: 28)` |

### 7.3. Reduced Motion Support
When `prefers-reduced-motion: reduce` is detected:
- All transform movements are disabled (`transform: none !important;`).
- Transitions collapse to simple opacity fades (`duration: 150ms`).
- Sheet gestures snap immediately to target state.

---

## 8. Iconography & Visual Assets

### 8.1. Icon Style Guidelines
- **Family:** Consistent outline icons with geometric rounded terminals (e.g., Phosphor Light or Lucide Light).
- **Stroke Width:** Uniform `1.5px` (or `1.75px` on small 16px icons). Never mix thick filled icons with thin line icons.
- **Sizing Tokens:**
  - `--icon-xs`: `14px` (inline rating stars, badge icons)
  - `--icon-sm`: `18px` (button icons, input field icons)
  - `--icon-md`: `24px` (navigation actions, drawer controls)
  - `--icon-lg`: `32px` (category highlights, feature icons)
- **Color:** Default icons inherit text color (`currentColor`) or brand Forest Green (`#183A2D`); rating stars use Muted Gold (`#D6A84B`).

### 8.2. Food Photography Directives
Food imagery is the cornerstone of the entire application:
- **Clean Studio Lighting:** Soft, diffused natural light from a 45-degree angle; no harsh digital flashes or heavy post-processing filters.
- **Neutral / White Ceramic Plates:** Food must be presented on clean ceramic or stoneware dishes that contrast cleanly with the food itself.
- **Overhead Angle (Top-Down 90° or 75°):** Standardizes all dish images, making visual comparison in the menu grid effortless.
- **Transparent / Clean Cutouts:** Menu thumbnails must feature precise circular or transparent cutouts to seamlessly blend with card backgrounds.

---

## 9. Accessibility (a11y) & UX Standards

### 9.1. WCAG 2.1 AA Compliance Requirements
- **Color Contrast Ratios:**
  - Normal text (`#292B27` on `#FFFFFF`): **14.2:1** (Exceeds AAA).
  - Secondary text (`#777A73` on `#FFFFFF`): **4.8:1** (Meets AA).
  - Forest Green text (`#183A2D` on `#FFFFFF`): **10.5:1** (Exceeds AAA).
  - Muted Gold accents (`#D6A84B`): Strictly reserved for decorative graphics, stars, and badges paired with dark text; never used for light text on white backgrounds.
- **Touch Target Sizes:**
  - All interactive elements (buttons, quantity toggles, category pills, form checkboxes) must measure **at least 44×44px** of clickable/tappable area.
- **Keyboard Navigation & Focus Indicators:**
  - Logical tab order matching visual RTL reading direction (right to left, top to bottom).
  - Explicit high-visibility focus ring:
    ```css
    :focus-visible {
      outline: 2px solid var(--color-brand-forest);
      outline-offset: 2px;
    }
    ```
- **Semantic HTML & Screen Reader Support:**
  - Landmark elements used throughout: `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`.
  - Cart counter and dynamic price updates must declare `aria-live="polite"`.
  - Icon-only buttons must declare descriptive `aria-label` attributes in Persian (e.g. `aria-label="افزودن به سبد خرید"`).

---

## 10. RTL & Localization Guidelines

### 10.1. Global Document Configuration
```html
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>فست‌فودی | طعم اصیل و باکیفیت</title>
</head>
```

### 10.2. Logical CSS Properties
Never use hardcoded directional CSS properties. Always use CSS logical properties:

| Deprecated Physical Property | Required Logical Property |
| :--- | :--- |
| `margin-left` / `margin-right` | `margin-inline-start` / `margin-inline-end` |
| `padding-left` / `padding-right` | `padding-inline-start` / `padding-inline-end` |
| `left` / `right` | `inset-inline-start` / `inset-inline-end` |
| `border-left` / `border-right` | `border-inline-start` / `border-inline-end` |
| `text-align: right` / `text-align: left` | `text-align: start` / `text-align: end` |

### 10.3. Icon Mirroring Rules
- **Mirror in RTL:** Directional arrow icons that indicate progression, back, next, or sequential flow (`arrow-left`, `arrow-right`, `chevron-right`, `chevron-left`) must automatically mirror across the horizontal axis:
  ```css
  [dir="rtl"] .icon-directional {
    transform: scaleX(-1);
  }
  ```
- **Do NOT Mirror in RTL:** Non-directional icons (search, cart, user, heart, star, phone, clock, checkmark, camera) must remain un-mirrored.

### 10.4. Mixed Text & Number Formatting
- **Persian Numbers Utility:** Use the `Intl.NumberFormat('fa-IR')` API for currency formatting and order numbers.
- **LTR Isolation:** Phone numbers (e.g. `+98 21 8888 7777`), URLs, email addresses, and payment tracking codes must be enclosed in `<bdi>` or styled with `direction: ltr; display: inline-block;` to avoid punctuation reversal bugs.

---

## 11. Design Tokens Reference (CSS Custom Properties)

```css
:root {
  /* Brand Colors */
  --color-brand-forest: #183A2D;
  --color-brand-forest-deep: #12251D;
  --color-brand-forest-light: #224E3D;
  --color-accent-gold: #D6A84B;
  --color-accent-gold-hover: #C4963A;
  --color-accent-gold-soft: #F8F3E8;

  /* Surfaces & Backgrounds */
  --color-surface-white: #FFFFFF;
  --color-surface-ivory: #F4EFE3;
  --color-surface-cream: #FAF7F2;

  /* Neutrals & Text */
  --color-text-primary: #292B27;
  --color-text-secondary: #777A73;
  --color-text-muted: #9EA199;
  --color-text-inverse: #FFFFFF;
  --color-border-subtle: #E8E5DC;
  --color-border-focus: #183A2D;

  /* Feedback */
  --color-success: #2E7D32;
  --color-warning: #ED6C02;
  --color-danger: #D32F2F;
  --color-info: #0288D1;

  /* Spacing Scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;

  /* Border Radii */
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-2xl: 32px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(24, 58, 45, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  --shadow-md: 0 4px 16px rgba(24, 58, 45, 0.06), 0 2px 6px rgba(0, 0, 0, 0.03);
  --shadow-lg: 0 12px 32px rgba(24, 58, 45, 0.08), 0 4px 12px rgba(0, 0, 0, 0.04);
  --shadow-dropdown: 0 8px 24px rgba(24, 58, 45, 0.10);

  /* Typography */
  --font-family-persian: 'IranSansX', 'IRANSans', 'Vazirmatn', system-ui, sans-serif;
  --font-family-latin: 'Plus Jakarta Sans', system-ui, sans-serif;

  /* Animation & Physics */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
  --transition-fast: 150ms ease-out;
  --transition-normal: 250ms ease-out;
  --transition-sheet: 320ms cubic-bezier(0.16, 1, 0.3, 1);

  /* Z-Index Hierarchy */
  --z-base: 0;
  --z-card: 1;
  --z-sticky-nav: 50;
  --z-floating-cart: 60;
  --z-drawer-backdrop: 80;
  --z-drawer-content: 90;
  --z-modal-backdrop: 100;
  --z-modal-content: 110;
  --z-toast: 150;
}
```

---

## 12. Do's & Don'ts

### 12.1. Approved Practices (DO)
- **DO** maintain 65–75% pure white backgrounds to allow the food photography to stand out vibrantly.
- **DO** use Forest Green (`#183A2D`) for primary calls-to-action on light sections.
- **DO** use Muted Gold (`#D6A84B`) with discipline — exclusively on review stars, badges, and subtle highlights.
- **DO** use localized Persian numerals (`۰-۹`) for all customer-facing prices and counters.
- **DO** use CSS logical properties (`margin-inline`, `padding-inline`, `inset-inline`) throughout all stylesheets.
- **DO** ensure all clickable and tappable elements meet the minimum 44×44px touch target requirement.
- **DO** use non-blocking Sonner toasts with clear feedback when items are added to the cart.
- **DO** maintain a balanced 2-column grid on mobile with consistent 12px gaps.

### 12.2. Prohibited Practices (DON'T)
- **DON'T** introduce colors outside the established palette (no random purples, blues, or neon greens).
- **DON'T** use loud orange buttons from the reference image — the brand color is Forest Green (`#183A2D`).
- **DON'T** use glassmorphism with heavy backdrop blurs on nested cards.
- **DON'T** use thick, dark black drop shadows (`shadow-xl` or `rgba(0,0,0,0.3)`).
- **DON'T** use hardcoded `left`, `right`, `margin-left`, or `margin-right` in any CSS rule.
- **DON'T** mix icon sets or use heavy filled icons next to delicate outline icons.
- **DON'T** allow English or Latin digits in customer-facing menu prices.
- **DON'T** use abrupt linear animations or disorienting page transitions.

---

## 13. Design Compliance Checklist

Before committing any frontend code or component modification, verify compliance against this checklist:

- [ ] **Color Palette:** Does the component strictly use established color tokens (`#183A2D`, `#D6A84B`, `#F4EFE3`, `#FFFFFF`, `#292B27`)?
- [ ] **Whitespace & Scale:** Are all margins, paddings, and heights multiples of 4px from the spacing scale?
- [ ] **Typography:** Is IranSansX used with appropriate weight (400, 500, 600, 700)?
- [ ] **Numeral Localization:** Are all prices, review counts, and quantities formatted using Persian digits?
- [ ] **RTL Direction:** Does the layout flow naturally from right to left? Are logical properties (`inline-start`/`inline-end`) used?
- [ ] **Icon Mirroring:** Are directional arrows mirrored correctly, while non-directional icons remain un-mirrored?
- [ ] **Touch Targets:** Are all mobile buttons and interactive controls at least 44×44px in size?
- [ ] **Focus Rings:** Does keyboard navigation reveal a clean `2px solid #183A2D` focus ring?
- [ ] **Contrast:** Does text meet or exceed the 4.5:1 WCAG AA contrast threshold against its background?
- [ ] **Motion & Feedback:** Are state changes accompanied by crisp, purposeful spring micro-interactions without violating `prefers-reduced-motion`?
- [ ] **Empty & Error States:** Are error messages, empty cart states, and loading skeletons accounted for?

