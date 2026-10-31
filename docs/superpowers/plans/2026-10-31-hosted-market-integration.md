# Integrate hosted Market reference research

> **For agentic workers:** Use superpowers:executing-plans inline. Continue the approved live-reference-first target in the existing Market worktree; do not merge main or modify the other checkout.

**Goal:** Reconcile PR44's reviewed hosted API commit with PR42's newer default research and private operations UI.
**Architecture:** Bring in commit `970ad32` only, preserving current MarketView lifecycle, race/cancellation protections and operations mounting. Public health/search/card/FX reads use the existing hosted API; private operator endpoints remain same-origin. No new provider, dependency or backend.
**Spec:** Operator's live card-price/research-first choice; #43/PR44 published integration contract and #26/#34 acceptance. This is integration of existing approved work, not a new product design.

## Constraints and review focus
- Preserve automatic initial lookup, refresh/selection race protections, collection persistence and optional private UI.
- Never send operator keys/cookies or private paths to the hosted API.
- Reuse hosted FX validation/cache/expiry behavior; preserve focus/sleep recovery and convert native amounts exactly once.
- Respect bounded background fetching and truthful source/freshness labels.
- Static preview must show real reference prices with no local API; private controls must report unavailable there. No merge/deployment action or live trading.

## Task 1: Integrate and verify hosted reference commit

**Files:** PR44's ten changed frontend/test/docs files, one new combined-boundary test, verification document. Backend files unchanged.

- [x] Add and run a failing integration test: initial hosted quote and FX produce SGD, while opt-in login/state remain same-origin; no private request is sent upstream.
- [x] Cherry-pick `970ad32` without committing; resolve overlap by retaining the newer lifecycle/private UI and hosted route/FX changes.
- [x] Adapt existing route assertions and expiry fixtures, retaining all newer regression cases. Run full frontend tests, build, focused lint/whitespace and report full lint baseline.
- [x] Playwright against plain static dist: automatic real quote, hosted search/selection, correct SGD/source, private-unavailable boundary and 390px width; verify private service still mounts controls.
- [x] Fresh scoped integration review, fix Important findings with regressions, publish PR42 and record that PR44's implementation is incorporated. Leave PR44/main disposition to the maintainer.

## Completion evidence

226 frontend tests/build/focused lint/whitespace passed; full lint baseline unchanged. Playwright static-host live-price calculation/search/selection/mobile and local private-auth boundary passed. Fresh review found no actionable issues. Additional CardDetail test fixtures were updated because the shared FX transport changed; runtime behavior is preserved. Existing feature-branch publication authorization applies.
