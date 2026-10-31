# Market live view verification — 30 October 2026

Scope: issue #26, `codex/market-live-view`; implementation base `c8db3d5`. The operator approved local implementation/tests and private Tailscale setup. Project/claim gates remain unavailable; this record preserves the explicit exception and does not assert ownership acceptance. No push/merge/deployment of this branch.

## Results

- Baseline: 104 frontend tests passed before changes.
- API tests first failed for the missing module, then 24 passed. Covers fixed-origin requests, path/method rejection, matching identity, numeric/currency filtering, missing card/quotes, invalid/future timestamps, shared in-flight requests, cache TTL/capacity and freshness across 48 hours, rate limiting, timeout, safe errors and oversized bodies.
- UI tests first failed for the absent view/navigation. Tests cover provenance, simulation label, ID rejection, HTML/static backend absence, retained failed-refresh values, empty quotes, stale/unknown timestamps, racing selections, unmount abort, mismatched identity and existing collection navigation/persistence. A late-health regression failed before cancellation was added, then passed.
- Full frontend suite: **142 passed across 18 files** using `NODE_OPTIONS=--no-experimental-webstorage npx vitest run`.
- `npm run build`: passed TypeScript and production bundle. Existing outdated Browserslist warning remains.
- ESLint on all changed TS/TSX/config files: passed, zero warnings. Full `npm run lint` still reports the same **9 pre-existing errors and 5 warnings** in unrelated shared UI/hooks/migration files.
- Built assets checked for the configured provider key and private Tailscale hostname: absent. No new dependencies.
- Built preview listens only on `127.0.0.1:5184`. Live health endpoint returned the reference-only capability contract. Two real TCGdex requests returned matching IDs and Cardmarket EUR values: Alakazam (`base1-1`, avg 48.30 EUR), Ninetales (`sv03-199`, avg 26.20 EUR). Fetch time approximately `2026-10-30T01:29:41Z`; provider update `2026-10-29T10:28:27.986Z`. These are observed reference values, not a guarantee of market value.
- Browser: Market navigation, real prices and missing-card failure verified in the built app. A temporary 390px iframe verified phone-width layout without clipping; local screenshot `/tmp/pokemon-market-mobile-prices.png`. The temporary QA page is removed from the build before handoff.
- Existing Python Market package was not changed; its previously recorded 117-pass result was not rerun for this UI/API-only change.

## Private access — incomplete external acceptance

Existing Tailscale connection is now Running/online, with health clear. Preferences were preserved, including the existing accept-routes setting. An initial Serve attempt failed while the connection initialized; retry reached the explicit Serve enablement requirement. The tailnet currently requires operator sign-in to enable Serve/HTTPS; the CLI's private link was given directly to the operator, not committed. No Serve route or public Funnel was created. Actual phone access remains unverified. After enablement, rerun the documented Serve command, check local private HTTPS and verify from the enrolled phone. The preview process is running for this handoff; sleep/restart will interrupt it.

## Decisions carried from execution

- Ruling: Reuse the clean dedicated branch in the established project checkout — preserves the operator's selected location and local service — concurrent edits would need reconciliation.
- Ruling: Continue Native execution after the explicit build approval without another plan checkpoint — preserves the previously selected execution method and current instruction to proceed — implementation choices must remain inside the approved design.

The narrow adapter uses existing provider field conventions instead of the broader card normalizer, as allowed by the plan, so unknown fields and ambiguous printings cannot become qualified prices.

## Independent review

Independent fresh-context review of `c8db3d5..bf93396` found no Critical issues, one Important compatibility defect and one Minor status-display issue. The Important defect rejected real dotted set IDs. Three regression cases first failed, then passed after changing the shared ID schema. The final full suite passed 142 tests; build, changed-file lint and whitespace checks passed. Restarted built preview returned real matching Charizard ex `sv03.5-199` and Pikachu `swsh12.5-160` with EUR quotes at approximately `2026-10-30T01:36:37Z`. No second review was used.

Deferred minor: Submitting before health finishes, then editing before the first price request completes, can leave the label “Checking backend…” until another lookup or navigation. No stale result overwrites the selection; this is a status-display limitation.

The reviewer explicitly set aside these behaviors; execution rulings:

- Ruling: Leave private HTTPS and phone verification pending operator sign-in — external account action is needed — phone access remains unavailable until enabled and tested.
- Ruling: Keep freshness as a manually refreshed snapshot — this matches the documented on-demand view — an idle screen can age past its displayed freshness label until refreshed.
- Ruling: Leave the existing keyed Card Detail provider unchanged — it is outside this Market endpoint — its existing trial-expiry failures remain on that separate path.
- Ruling: Keep cache and rate limiting process-local — the approved deployment is one personal Mac process — multiple processes or restarts can exceed the combined upstream budget.

The waiting Serve CLI was stopped after confirming no route exists. Tailscale itself remains connected; only this app's preview process was restarted. No private hostname or sign-in token was committed.
