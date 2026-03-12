# K2 Dashboard — Design Audit (Impeccable)

## Current Sins (against Impeccable guidelines)

### Typography
- ❌ Uses `-apple-system, BlinkMacSystemFont, 'SF Pro', 'Inter', sans-serif` — system defaults + Inter
- ❌ No modular type scale — ad-hoc font sizes (11px, 12px, 13px, 14px, 15px, 16px, 18px)
- ❌ No fluid typography (no clamp())
- ❌ No font-variant-numeric: tabular-nums on data/scores

### Color
- ❌ Pure `#0a0a0f` background — essentially pure black
- ❌ Untinted neutrals: `#12121a`, `#1a1a26`, `#2a2a3a` — dead grays with minimal tinting
- ❌ Cyan-on-dark accent (`#4a9eff`) — classic AI color palette
- ❌ Purple accent (`#7c5cff`) — AI purple gradient territory
- ❌ Heavy use of `rgba()` transparency everywhere instead of explicit palette
- ❌ `--text-dim: #8888a0` — gray text on colored surfaces

### Layout & Space
- ❌ Everything wrapped in cards — cards-in-cards in project views
- ❌ Same padding everywhere (16px, 20px, 24px used interchangeably)
- ❌ No spacing scale/system — arbitrary values
- ❌ Identical card grids (same-sized cards repeated)

### Visual Details
- ❌ Rounded rectangles with generic shadows everywhere
- ❌ `border-radius: 12px` on everything
- ❌ `border-left: 3px solid var(--accent)` colored borders (lazy accent)
- ❌ Glassmorphism-adjacent: `backdrop-filter` / blur effects

### Motion
- ❌ `transition: all 0.15s` / `transition: all 0.2s` everywhere
- ❌ No easing curves specified (using default `ease`)
- ❌ No staggered entrance animations
- ❌ No reduced-motion support

### Interaction
- ❌ Every button looks the same weight
- ❌ Modals for everything (task modal, doc modal)
- ❌ No progressive disclosure

## Design Direction

**Tone**: Editorial / utilitarian — like a Bloomberg terminal meets Notion
- Not flashy, not generic
- Information-dense but readable
- Warm dark theme (not cold blue/purple)
- Typography-driven hierarchy (less reliance on color boxing)

## Proposed Changes

### Phase 1: Foundation (CSS vars + typography)
- New font: **Plus Jakarta Sans** (Google Fonts, distinctive but readable)
- OKLCH color palette with warm-tinted neutrals (amber/sand hue)
- 4pt spacing scale as CSS custom properties
- Modular type scale (1.25 ratio)
- `font-variant-numeric: tabular-nums` on data

### Phase 2: Color & Surfaces
- Warm dark background: `oklch(12% 0.01 60)` instead of `#0a0a0f`
- Tinted neutrals: warm undertone instead of blue/purple dead grays
- New accent: warm amber/gold (`oklch(75% 0.15 70)`) — NOT blue or purple
- Semantic colors (success/error/warning) with proper contrast
- Remove all `rgba()` in favor of explicit palette tokens

### Phase 3: Layout & Cards
- Remove card nesting — use spacing + typography for hierarchy
- Consistent spacing using the 4pt scale
- Asymmetric layouts where appropriate
- Container queries for responsive components

### Phase 4: Motion & Polish
- Proper easing curves (`ease-out-quart`)
- Staggered entrance animations on page load
- `prefers-reduced-motion` support
- Transition only `transform` and `opacity`

## Constraints
- Single HTML file — all CSS inline in `<style>`
- Must not break existing JS functionality
- Mobile nav (4-tab + drawer) must still work
- TipTap editors must remain functional
- Google Fonts loaded via `<link>` in `<head>`
