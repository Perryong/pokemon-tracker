# Market slice verification

Date: 30 October 2026 (Asia/Singapore). Local branch: `feature/market-agent`.

## Authorization and scope

The user approved the design, implementation plan and Native execution. They explicitly answered “Yes—build and test locally under this exception” to a one-time exception naming the AGENTS.md Project/claim gate. Issue #24 exists, but Project access is still missing and the coordination environment is absent. The operator subsequently authorized pushing this feature branch and opening a draft PR on 30 October 2026 in response to the explicit publication-exception request. This extends the exception to draft publication only; no signed claim, merge or deployment approval is asserted.

## Development evidence

Each of six tasks began with its named tests failing before implementation; session/return-accounting regressions were also observed failing and then passing. The final full Python suite passes **117 tests** with controlled model transport. Real Deep Agents 0.7.32 calls the real session and valuation tools; it is not replaced by a graph mock. Harness tests deny outbound socket connections.

Environment: Python 3.12.13, Pydantic 2.14.2, Deep Agents 0.7.32, LangGraph 1.2.18, LangChain 1.4.7, langchain-openai 1.7.3. Full transitive versions are in `requirements.lock`.

Commands already run successfully:

```sh
market_agent/.venv/bin/python -m pytest market_agent/tests -q
market_agent/.venv/bin/python -m pip check
```

Fresh-environment verification passed: locked installation, editable install with `--no-deps --no-build-isolation`, `pip check`, and 117 Python tests. A wheel built using `python -m build --wheel --no-isolation market_agent` installed successfully in that verification environment, replacing the editable installation. All six scenarios then passed from a temporary directory outside the checkout; the package imported from `site-packages`, proving both fixture files ship in the wheel. Scenario output parsed as a single JSON document with empty stderr.

`uvx ruff check --select F market_agent/src market_agent/tests` and `git diff --check` passed. Ruff formatting was applied without adding a project dependency.

## Independent review and fixes

An independent fresh-context reviewer examined product commits `5aa62f7..2f59746` and ran the original 111 tests. All three Important findings were accepted and fixed in one pass. Each regression failed before its fix; the final complete suite passed 117 tests in both environments. No Critical or deferred Minor findings were reported. No second reviewer was dispatched.

| Finding | Regression and resulting behavior |
| --- | --- |
| Reassessment limit retained outdated authority | `test_exhausted_reassessment_revokes_and_blocks_new_authority`: a fourth current change revokes authority, records new facts, releases exposure once, and blocks further assessment/issuance/negotiation for that listing in the session. Stale requests still cannot mutate state. |
| Model could finalize before exposure checks | `test_acquisition_cannot_finalize_pre_exposure_assessment`, both variants: an earlier assessment cannot finish acquisition, even after issuance. Completion requires the mandate-stage result. The low-capital rejection also passes through the real graph. |
| Reserved stock lost inspected valuation | `test_inspected_stock_valuation_independent_of_availability[reserved]`: receipt/inspection/return facts establish trusted condition independently of availability. Valuation remains available; resale preparation remains blocked. |

The rebuilt wheel was reinstalled after the fixes; all six external-directory scenarios passed again. The first earlier wheel verification invocation incorrectly resolved the virtual environment's Python symlink to the base interpreter; keeping the virtual environment executable path corrected that verifier error.

## Execution decisions and reviewer boundaries

- Work in the existing clean feature/market-agent checkout requested by the user — avoids moving their branch or creating a competing branch for a local-only change — concurrent edits would require stopping to reconcile.
- SDK 0.7.32 requires read_file in FilesystemMiddleware — retain only that internal StateBackend tool, hide it via the public harness profile and deny it at dispatch — a future SDK change must pass the forbidden-tool tests before upgrade. No host backend, writes or offloading.
- Use a return-direct FinalReference tool as structured completion instead of model-authored financial output — resolves only service-stored artifacts and rejects extra fields — a model must learn this completion tool rather than return arbitrary JSON.
- Live model behavior, profitability and connector access remain outside offline acceptance — synthetic service behavior is the approved deliverable — live quality, access and trading results remain unverified.
- Durable recovery, cross-process exposure, authenticated A2A and Sales compatibility remain later milestones — this slice has no persistent or peer authority — deploying it as a trading service would lack those safeguards.
- Keep one lifecycle outcome per physical unit — the fixture contract deliberately rejects repeated sale/return cycles — a real stock ledger is required before supporting such cycles.
- Direct graph entry supports assess_opportunity, reassess_opportunity, assess_owned_unit and prepare_resale; standalone issue_mandate and negotiate_acquisition remain session APIs — the graph delivers the planned workflows and mandate issuance is internal to acquisition assessment — callers must not assume every Request operation is a graph entry point.
- Keep process-wide SDK profile configuration and allow an in-flight model request to finish after the response deadline — dedicated application profiles and cancellation checks prevent subsequent tool work — embedding in a shared process may conflict with other profiles and a timed-out provider call may still be billed.
- Preserve the existing frontend baseline rather than change unrelated files — the Market slice touches no frontend code and baseline tests/build passed — its nine existing lint errors and five warnings remain unresolved.

Deferred minors: none.

## Existing tracker baseline (before Market code)

- `NODE_OPTIONS=--no-experimental-webstorage npm test -- --run`: 104 tests passed in 16 files. Existing Vite deprecation warnings and a localhost:3000 connection-refused diagnostic appeared despite exit 0.
- `npm run build`: passed. Existing outdated Browserslist-data warning.
- `npm run lint`: **failed**, 9 errors and 5 warnings. Errors: two empty patterns in `calendar.tsx`; unused `_` in `chart.tsx`; empty interfaces in `command.tsx`, `input.tsx`, `textarea.tsx`; unused `actionTypes` in `use-toast.ts`; explicit `any` in `migration.test.ts` and `migration.ts`. Five shared UI files have existing Fast Refresh warnings. These files were not changed by the Market slice.

## Limitations

No live model API call, Carousell access, peer A2A exchange, database, Langfuse export, migration, operational deployment or profitability validation was performed. Fixed-time synthetic evidence proves only the software behavior described by the first-slice design. Existing lint failures are not presented as passing.
