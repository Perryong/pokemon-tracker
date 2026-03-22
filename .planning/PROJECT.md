# Pokemon TCG Collection Tracker

## What This Is

Pokemon TCG Collection Tracker is a shipped personal web app for tracking Pokemon card ownership by set. It provides a sets-centric browsing view with filtering/search/progress and a card album view for fast ownership toggling, filtering, and real-time stats.

## Core Value

Let me reliably track my Pokemon TCG collection progress by set, with fast card-level updates that persist between sessions.

## Current State

- ✅ **Shipped milestone**: v1.0 (2026-03-21)
- ✅ **Shipped milestone**: v1.1 Quantity Tracking (2026-03-22)
- ✅ **Feature scope complete**: 20/20 v1 requirements
- ✅ **Hardening complete**: 6/6 hardening requirements
- ✅ **v1.1 quality gates**: strict `npm run test` + `npm run build` passing
- ✅ **Architecture**: React + TypeScript + Vite + shadcn/ui + TCGdex SDK + localStorage persistence

## Current Milestone: v1.2 (TBD)

**Goal:** Define and prioritize the next set of collection workflow improvements after quantity tracking.

**Target features:**
- Prioritize deferred quantity UX (manual input, keyboard shortcuts, duplicates filter)
- Evaluate next highest-impact collection workflows (wishlist, import/export, analytics)
- Preserve local-first reliability and regression safety bar established in v1.1

## Next Milestone Goals (v1.2 candidate scope)

- Define and prioritize next milestone requirements via `/gsd-new-milestone`
- Evaluate deferred/advanced features:
  - Card quantity (duplicates)
  - Wishlist tracking
  - Rarity filtering/sorting
  - Import/export and expanded analytics
- Preserve local-first reliability while expanding collection workflows

## Requirements

### Validated

- ✓ v1.0 shipped and validated via archived requirements (`.planning/milestones/v1.0-REQUIREMENTS.md`)
- ✓ v1.1 quantity tracking shipped and validated via archived requirements (`.planning/milestones/v1.1-REQUIREMENTS.md`)
- ✓ Existing React + TypeScript + Vite single-page app foundation is in place
- ✓ Existing shadcn/ui + Radix component system and styling pipeline is in place
- ✓ Existing localStorage-backed collection persistence pattern remains core architecture

### Active

- [ ] Define v1.2 scope and requirements based on deferred backlog and user priority

### Out of Scope

- User accounts, cloud sync, and multi-device syncing (until explicitly planned)
- Social sharing, marketplace, trading flows, and public profiles (unless added to milestone scope)
- OCR/card scanning workflows (unless explicitly prioritized in future roadmap)

## Context

This is a brownfield React codebase with established component architecture and persisted planning history in `.planning/`. v1.0 and v1.1 execution artifacts are archived for traceability; next milestone should start with fresh requirements and roadmap definition.

## Constraints

- **Tech stack**: Maintain React + TypeScript + shadcn/ui + Vite conventions
- **Data source**: Continue using `@tcgdex/sdk` as canonical card/set source unless milestone redefines it
- **Persistence**: Preserve localStorage reliability for core ownership/progress flows
- **Scope discipline**: Keep milestone boundaries explicit to avoid scope creep

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep local-first persistence for v1.0 | Personal-use scope prioritized speed/reliability without backend | ✓ Good |
| Use TCGdex SDK as canonical data client | Consistent domain model and maintainability | ✓ Good |
| Ship hardening as inserted Phase 02.1 | Reduced release risk with explicit regression/build/smoke gates | ✓ Good |
| Enforce zero blocker/critical defects at release gate | Raised confidence in v1.0 production readiness | ✓ Good |
| Adopt quantity-as-source-of-truth model in v1.1 | Prevent ownership/quantity divergence and simplify stats semantics | ✓ Good |
| Enforce strict automated release gate in v1.1 (`test + build`) | Protect v1.0 behavior while expanding model/UI complexity | ✓ Good |

---
*Last updated: 2026-03-22 after shipping v1.1 Quantity Tracking*
