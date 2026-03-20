# Pokemon TCG Collection Tracker

## What This Is

Pokemon TCG Collection Tracker is a personal web app for tracking Pokemon card ownership by set. It provides a sets-centric view with progress visibility and a card album view for fast ownership marking and filtering. The app is built as a polished, offline-friendly React experience with persistent local progress.

## Core Value

Let me reliably track my Pokemon TCG collection progress by set, with fast card-level updates that persist between sessions.

## Requirements

### Validated

- ✓ Existing React + TypeScript + Vite single-page app foundation is in place — existing
- ✓ Existing shadcn/ui + Radix component system and styling pipeline is in place — existing
- ✓ Existing localStorage-backed collection persistence pattern already exists in app architecture — existing
- ✓ Existing set/card browsing and card image rendering patterns already exist in the current app — existing

### Active

- [ ] Build a Sets View that loads all sets, shows official set logos, supports series dropdown filtering, and live name search.
- [ ] Show per-set completion progress bars and a 100% completion indicator based on owned cards in local collection data.
- [ ] Build a Cards Album View for the selected set with responsive grid, real card images, and click-to-toggle ownership with owned state indicator.
- [ ] Add album controls: card size toggle (small/medium), ownership filters (all/owned/missing), and in-set name search.
- [ ] Add a fixed stats footer that updates in real time with owned count, missing count, and completion percentage.
- [ ] Integrate data loading via TCGdex SDK (`@tcgdex/sdk`) using set, set-details-with-cards, and series endpoints.
- [ ] Persist ownership and derived collection statistics in localStorage so progress survives browser restarts.

### Out of Scope

- User accounts, cloud sync, and multi-device syncing — v1 is explicitly personal-use and local-first.
- Social sharing, marketplace, trading flows, and public profiles — not required to deliver core tracking value.
- Advanced import/export, OCR scanning, and collection valuation analytics — defer until core tracking workflow is validated.

## Context

This is a brownfield React codebase with an existing component architecture, collection persistence patterns, and mapped codebase documentation in `.planning/codebase/`. The project will use shadcn/ui primitives and must integrate the official TCGdex JavaScript SDK instead of ad-hoc API wiring for the new tracker behavior. The first release targets a polished personal workflow with offline-friendly persistence and no authentication or backend dependency for core functionality.

## Constraints

- **Tech stack**: React + TypeScript + shadcn/ui in current Vite project — align with established project architecture and component conventions.
- **Data source**: Must use `@tcgdex/sdk` endpoints for sets, set details, and series — ensures consistent domain data and future maintainability.
- **Persistence**: localStorage persistence is required for ownership/progress — user must not lose progress between sessions.
- **Scope**: Personal-use v1 only — avoid account and social features that dilute core tracking delivery.
- **UX quality**: Must feel polished and responsive, including clear progress, filtering, and ownership affordances — this defines "done" for v1.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Prioritize Sets View and Cards Album View as v1 primary surfaces | These two views map directly to collection tracking workflow and user request | — Pending |
| Keep persistence local-only with localStorage for v1 | Personal-use scope favors speed and reliability without backend complexity | — Pending |
| Use TCGdex SDK as canonical data client | User explicitly requested SDK and documented endpoint usage pattern | — Pending |
| Treat polish and responsiveness as release criteria | User-defined done state includes "works offline and feels polished" | — Pending |

---
*Last updated: 2026-03-20 after initialization*
