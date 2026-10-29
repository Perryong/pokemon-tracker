# Issue #9: simulated Sales Agent slice

Accountable contributor: ChouBokYann. Worker: symphony-sales-9-20261029-a1.
Base: 1141231bbf74f8ce6384ac50a57acafec5cdd976. Branch: sales-agent/issue-9-symphony.
Ownership verified against the complete 16-event live timeline and coordinator decision
6501036508; assignment and Project In progress match. Native prerequisites: none.
Active/Blocked views and both repositories' open issues were read; no competing
implementation PR exists. #11 onward describe separate integration deliveries.

## Design decisions (worker choices within the authorized trial)

Use an isolated `sales_agent/` Python package alongside React. Pydantic validates
immutable qualified-lead and mandate fixtures. Amounts use integer currency minor
units, limited here to SGD. A session owns one conversation and a deterministic
simulated seller transport. No global session store, persistence or live messaging.

Build the actual `deepagents.create_deep_agent` graph with an explicitly supplied
LangChain chat model. Hide built-in filesystem/execution/delegation tools through the supported
model-call middleware API, and enforce the exact allowlist again at tool dispatch. Keep
Deep Agents' graph/context scaffolding; never substitute a handwritten agent loop.
A scripted chat-model transport is the default offline demo and test model.
The same graph accepts an injected real tool-calling model; no provider credentials
are read or shipped by this package.

Expose only enumerated enquiry topics, conditional price proposals, and proposal
preparation. Render outgoing messages in deterministic templates; never send model
or seller free text. The model cannot disclose ceilings or make promises via these
tools. Every action rechecks conversation, current policy/state versions, expiry,
rounds, opt-out and reassessment. A material seller fact invalidates price authority
and emits a fixture-labelled Market Agent reassessment request. Final proposals
are exact structured local artifacts awaiting operator approval, with no dispatch.
Untrusted seller text may influence model reasoning but cannot expand capabilities.

Validate live policy changes through a trusted current-state object, separate from
model arguments. Snapshot input fixtures to avoid mutation after validation.
All state is ephemeral: restart safety, authenticated A2A, durable approvals, cash
holds and live connector authorization remain follow-ups. No frontend changes.

## Verification

Write boundary tests first; record red, then green. Exercise the real graph with
controlled AIMessage tool calls and inspect actual connector effects and tool
results. Cover eligible/denied/expired/opt-out/material changes, stale versions,
round exhaustion, hostile content, forged tool names and conversation isolation.
Run only focused Python tests and demo commands, as requested. Supervisor reviews
the local diff; do not push, mutate issue/project state, release or merge.
