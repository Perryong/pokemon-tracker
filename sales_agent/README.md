# Sales Agent simulated slice — tracker #9

This runs the released **Deep Agents 0.7.32** harness, not a replacement agent
loop. Deep Agents executes three scoped tools through LangGraph. The default
model transport is a scripted offline fixture; the seller connector is an
in-memory simulation. No model or marketplace credentials are needed.

From the repository root (Python **3.13**):

```bash
cd sales_agent
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python -m pokemon_sales --scenario eligible
.venv/bin/python -m pokemon_sales --scenario out-of-policy
.venv/bin/python -m pokemon_sales --scenario expired
.venv/bin/python -m pokemon_sales --scenario opt-out
.venv/bin/python -m pokemon_sales --scenario material-facts
```

Windows: use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.
The lock pins the resolved runtime/test dependencies; the build dependency is
pinned in `pyproject.toml`. Python 3.13 is the supported/tested slice environment.

Every demo uses the explicitly reported fixed clock **2026-10-29 12:00 UTC**,
with a fixture expiring one hour later. `expired` sets expiry to the fixed current
time. Exit zero means the scenario ran; inspect `tool_results` for denials.
These commands never claim a live negotiation or purchase took place.

Expected outcomes:

| Scenario | Simulated outbound messages | Result |
| --- | ---: | --- |
| eligible | 2 | Exact SGD 45.00 proposal awaiting operator approval |
| out-of-policy | 1 enquiry | SGD 50.01 rejected against the SGD 50 fixture ceiling |
| expired | 0 | Every tool request rejected |
| opt-out | 1 enquiry | All further contact/proposals rejected |
| material-facts | 1 enquiry | Local reassessment request; pricing stops |

## Inputs and policy

The packaged `src/pokemon_sales/fixtures/qualified_lead.json` identifies the lead,
seller/listing/conversation, exact card set/number/language/printing, condition and
evidence references, SGD currency, mandate limits, policy/state versions and
aware expiry. `--fixture path.json` accepts a replacement **local fixture** with
`lead`, `mandate`, `current` and `seller_replies`; demo price and clock stay fixed.
This is a temporary integration contract, not authenticated A2A.

Money uses integer SGD cents (no floats, numeric strings or boolean amounts).
A null `ceiling_minor` means questions-only authority. A trusted caller supplies
current policy/state versions separately; the model cannot set them. Inputs are
snapshotted and frozen. Dispatch rechecks scope, versions, expiry, round budget,
opt-out and reassessment. Final artifacts are revalidated after the last model
turn. No matching conditional price means no final proposal.

`facts_reviewed: true` is a **trusted simulation fixture annotation**, not a seller
assertion or live classifier. It means the fixture author has classified that
reply and found no new material facts. Explicit `material_facts` always require
reassessment. Nonempty unclassified text also pauses pricing. Explicit opt-out or
conservative stop-language recognition ends the session. The keyword recognizer
is not a multilingual production opt-out classifier; unclassified text fails
closed for further pricing/contact anyway.

## Capabilities and outputs

The model sees only `ask_question`, `propose_price`, and `prepare_proposal`.
Middleware also denies forged built-in filesystem, shell and delegation calls at
dispatch. Deep Agents' default ephemeral context scaffolding remains installed;
no host filesystem backend, external MCP, persistent memory or skills are loaded.
Tool execution is serial, including a model response containing several calls.

Questions select from fixed topics. Conditional prices use a fixed template that
requires final operator approval. There is no free-form outbound message field,
so hostile seller/model prose cannot send promises or disclose internal ceilings.
Model final prose is discarded. No tool accepts offers, promises payment, confirms
meetups, dispatches commitments or accesses a database.

`proposal` is a structured **local review artifact**, with exact card, seller,
listing, amount/currency, condition/evidence, versions, expiry and commitment draft.
It has `status: awaiting_operator_approval` and `dispatchable: false`. Delivery,
fees and logistics remain explicitly unresolved. This slice has no approval or
purchase execution endpoint. A proposal is not an approved or complete purchase.

`reassessment` includes changed facts and IDs/versions, is labelled
`local_fixture_unauthenticated`, and requires a replacement mandate. No Market
Agent is invoked. Unknown facts are retained as unclassified input for review.

## Real model boundary and remaining work

`run_session(session, model)` accepts an explicitly constructed LangChain
`BaseChatModel` supporting tool calling. `SalesSession` uses the real UTC clock
unless a trusted caller supplies a demo/test clock. Provider credentials belong
only in that private server-side caller; this package does not read/export them,
and no frontend bundle imports it. External LangSmith tracing is disabled for
this slice. No live-model run was performed in this trial.

Tests replace only model transport. They exercise actual Deep Agents tool calls,
connector effects and authorization outcomes, including hostile input, forged
tools, batched opt-out, cross-conversation isolation, stale policy and late expiry.

All state is ephemeral and one session represents one isolated fixture run.
Restart recovery, durable seller suppression/round counters, multi-worker leases,
authenticated A2A, valuation, exact approval/budget services, approved live
marketplace access, production opt-out classification, persistence and deployment
remain separate follow-ups under #8. Do not reuse this demo as a live connector.

Implementation references checked on 2026-10-29:
[official customization docs](https://docs.langchain.com/oss/python/deepagents/customization),
[model interface](https://docs.langchain.com/oss/python/langchain/models),
[released package metadata](https://pypi.org/project/deepagents/0.7.32/).
See `VERIFICATION.md` for this trial's actual results.
