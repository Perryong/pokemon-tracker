# Live reference research default Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this one-task change inline, then a fresh reviewer.

**Goal:** Open Market directly on real provider reference prices, with truthful research and fixture labels.

**Architecture:** Reuse MarketView's existing validated lookup and cancellation path for its initial card. Keep the same TCGdex/FX services, backend cache and opt-in private fixture panel.

**Tech Stack:** Existing React/TypeScript, Vite, Vitest and Playwright. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-31-live-reference-default-design.md`

## Global Constraints

- Read-only research; real reference data never becomes completed-sale evidence or mandate authority.
- Existing default card `base1-1`; price cache up to one hour; manual refresh thereafter.
- Preserve cancellation, stale-response guards, error states, source times, original API currency and dated estimated SGD.
- Keep the private fixture worker paused; no marketplace integration, merge or new deployment action.

## Review Focus

- Market must automatically display the requested card without opening private APIs.
- A late initial response cannot overwrite a user-selected card.
- Changing an ID or unmounting aborts the initial lookup.
- Provider/static-host errors must never produce invented data.
- Independent health completion cannot overwrite a settled lookup result; strict effect remount must still work.

### Task 1: Make the existing live research path the default

**Files:** Modify `src/components/MarketView.tsx`, `src/components/__tests__/MarketView.test.tsx`, and affected parent mount assertions in `MarketOperations.test.tsx`; update `docs/market-live-view.md` and this plan's evidence.

**Interfaces:** Consume existing `/api/market/health`, `/api/market/cards/{id}` and MarketCardSchema. Keep the public MarketView component signature and all private API contracts unchanged.

- [ ] Write failing tests for automatic real-reference display and initial-load cancellation/races, with external HTTP mocked at the network boundary.
- [ ] Run focused tests and observe the missing automatic display fail.
- [ ] Reuse the bounded `load(selected: string)` path from the mount effect; identify live reference research and opt-in fixture controls truthfully. Update callers/tests for the new initial request.
- [ ] Run all frontend tests, production build, focused ESLint and whitespace checks. Expect no failures; report existing full lint separately.
- [ ] Use Playwright against the built server to verify automatic actual-provider prices, provenance/SGD, selection, refresh and 390px no overflow. Confirm fixture service remains paused.
- [ ] Fresh review of the change and connected behavior; fix Important findings with regressions. Commit/push the feature branch and append exact issue/PR evidence.
