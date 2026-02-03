# Homepage UI Experiment – Product Requirements Document

Site: theproductwheel.com  
Scope: Homepage only  
Status: Experimental (non-destructive)  
Execution: Implement on `ux-experiment` branch (safe to commit)

---

## Objective

Design and implement an **alternative homepage layout** to test improved clarity, trust, and editorial hierarchy.

This is an **experiment**, not a replacement:
- The current homepage layout must remain intact
- The new layout must be implemented side-by-side
- Reverting must be trivial (delete file / toggle route)

The goal is to evaluate whether an editorial-first, hierarchy-driven layout performs better visually and experientially.

---

## Critical Constraints (Non-Negotiable)

- **Homepage-only** changes (do not modify `/posts` or post templates)
- Keep changes easy to revert (single component + isolated homepage wiring)
- No schema, content, or data model changes

---

## Implementation Strategy

### Required
- Implement changes on the `ux-experiment` branch.
- Keep changes isolated to:
  - homepage wiring (`site/src/pages/index.astro`)
  - a dedicated component for the modal
  - minimal styling adjustments for the disclosure banner

### Forbidden
- Changing content schemas/models
- Introducing cross-site behavior changes unrelated to the experiment

---

## 1. Affiliate Disclaimer Banner

### Requirement
The affiliate disclaimer **must retain its exact current wording**.

### Behavior
- Keep disclaimer at the top (site header).
- Make it visually quieter:
  - smaller font
  - lighter background
  - reduced contrast
  - visually subordinate to hero

### Acceptance Criteria
- Wording is unchanged
- Disclaimer is always visible
- Disclaimer is visually quieter than hero

---

## 2. Header & Brand Treatment

### Requirement
Simplify header to focus on brand recognition.

### Changes (Experimental Layout Only)
- Keep: **Logo + tagline**
- Remove: **Guides**
- Remove:
  - Subheadline duplication
  - Brand repetition at bottom of page

### Acceptance Criteria
- Header contains only logo + tagline
- Header is visually lighter than current version
- No repeated brand messaging below hero

---

## 3. Hero Section

### Requirement
Hero establishes purpose and flows directly into content.

### Changes
- Remove any **“Latest”** button
- No primary CTA required
- Minimal editorial text only

### Layout
- Hero spans **full width**
- Text constrained to readable max width
- No boxed hero container

### Acceptance Criteria
- No CTA buttons in hero
- Hero visually leads into content grid

---

## 4. Categories Interaction

### Requirement
Replace category pills with a single intentional entry point.

### Changes
- Remove category pills entirely
- Introduce **“View Categories”** button

### Behavior
- Button opens a lightweight modal
- Categories listed **with counts** formatted like `(7)`
- Modal has an explicit **X** close button
- No filtering UI visible by default

### Acceptance Criteria
- No category pills visible
- Exactly one category entry control exists
- Categories are discoverable but not dominant
- Counts are shown as `(N)`
- Close affordance includes a clear X button

---

## 5. Latest Content Representation

### Requirement
Avoid duplicate representations of posts.

### Changes
- Remove text-only lists of links
- Each post must appear **once** in the layout

### Acceptance Criteria
- No duplicated content blocks
- All posts represented via cards/grid only

---

## 6. Card CTA & Typography Simplification

### Requirement
Cards should feel editorial, not transactional.

### Changes
- Remove **“Read Guide”** buttons
- Entire card is clickable
- Reduce font sizes for:
  - Titles
  - Meta (date, category)

### Acceptance Criteria
- No explicit CTA buttons on cards
- Typography feels calmer and denser
- Cards rely on hierarchy, not buttons

---

## 7. Featured + Grid Layout

### Requirement
Introduce hierarchy via layout, not labels.

### Layout Specification
- Desktop: **3-column grid**
- First row:
  - Center column = **Featured Guide**
  - Featured card is visually larger
  - Must always be the **most recent post**
- Left and right columns:
  - Smaller cards
- Second row onward:
  - Uniform smaller cards

### Labeling
- Featured card labeled **“Featured Guide”**
- Label must be subtle (not badge-heavy)

### Acceptance Criteria
- Featured guide is always latest by date
- Hierarchy is visually obvious
- Layout collapses cleanly on tablet and mobile

---

## 8. Vertical Rhythm & Spacing

### Requirement
Homepage should feel continuous and editorial.

### Changes
- Remove decorative dividers (e.g. `* * *`)
- Use spacing and typography instead of lines
- Reduce excessive vertical padding

### Acceptance Criteria
- No heavy separators
- Scroll feels magazine-like
- Content density slightly increased

---

## 9. Cookie Banner

### Decision
No changes required.

---

## 10. Visual Direction

### Directional Guidance
- Structure: **Wirecutter**
- Spacing: **Oliver Bonas**
- Visual accents: **Pinterest-lite**

### Constraints
- No masonry layout
- No image-heavy dominance
- Images, if used, must support scanning

### Acceptance Criteria
- Homepage feels editorial, not blog-index
- Visual elements never overpower text
- Consistent card treatment throughout

---

## Definition of Done

- Experimental homepage renders locally
- Existing homepage untouched
- Experimental layout can be removed cleanly
- No git commit performed
- No regressions to production layout
- Visual hierarchy clearly communicates:
  1. What this site is
  2. What to read first
  3. How to explore further

---

## Explicit Reminder to Agent

This is an **experiment**.

If the result is not approved:
- Delete the experimental route/layout
- No rollback work should be required

Design for **reversibility first**, elegance second.
