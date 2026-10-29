# Sales slice implementation plan

Goal: satisfy tracker #9 with an actual offline-runnable Deep Agents graph.
Architecture: validated fixtures → session policy → scoped tools → simulated seller;
structured proposal/reassessment artifacts remain local.
Tech stack: Python 3.13, Deep Agents 0.7.32, Pydantic, pytest.
Spec: ../specs/2026-10-29-sales-slice-design.md

The user explicitly authorized ordinary choices and inline execution. Skill approval,
commit and specialist-dispatch suggestions yield to that instruction and the trial's
single-worker/local-diff boundary. No delegation planned.

## Review focus

- Unknown tool calls cannot reach built-in filesystem or delegation tools.
- Seller injection cannot leak ceilings through outgoing message text.
- Batch calls must respect opt-out and exhausted rounds sequentially.
- New facts invalidate prior proposals and require reassessment.
- Invalid identity/version/currency inputs and cross-conversation calls fail closed.

## Task 1: policy boundary

Files: `sales_agent/src/pokemon_sales/contracts.py`, `session.py`, `tests/test_policy.py`.
Interface: `SalesSession(lead, mandate, current, seller, clock)` with `act(action,
conversation_id, **arguments) -> dict`. Tests supply trusted current state and clock.
- [x] Write failing behavior tests for validation, price/expiry/staleness/round limits,
  opt-out, facts and isolation. Run pytest and observe missing feature failure.
- [x] Implement immutable schemas and deterministic session/connector; rerun green.

## Task 2: real harness and demo

Files: `harness.py`, `controlled.py`, `__main__.py`, `tests/test_harness.py`, fixtures,
`pyproject.toml`, lock file, README and verification report under `sales_agent/`.
Interface: `run_session(session, model) -> dict`; `ControlledModel` returns prescribed
AIMessage calls via the real LangChain model interface, never executes tools itself.
- [x] Write graph integration tests; run red before implementation.
- [x] Use released Deep Agents API, deny non-allowlisted tools and run green.
- [x] Run eligible, out-of-policy, expired and opt-out demos; inspect bounded JSON.
- [x] Review diff and acceptance, record commands/results and remaining limitations.
