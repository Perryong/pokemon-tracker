# Market-to-Sales contract compatibility proposal

Status: **Operator-selected fixture development contract; real peer agreement pending.** References:
[#32](https://github.com/Perryong/pokemon-tracker/issues/32),
[shared contract #11](https://github.com/Perryong/pokemon-tracker/issues/11),
and [Sales PR #23](https://github.com/Perryong/pokemon-tracker/pull/23).

Market baseline: `5720d200a8b449ed97c22f4772ed5cf7cf2b9e18`.
Sales proposal inspected: `dde45fa5b84850e05473007629858d858abb156f`.
Neither prototype's application objects establish authenticated A2A interoperability.

## Intent and confirmed decision

Preserve exact identity, money, state versions and authority when Market and Sales
exchange work. Reuse the existing models and deterministic services; do not add an
unused conversion layer before there is an agreed consumer.

The operator confirmed Supabase PostgreSQL for durable business state, with a
disposable local database for tests. Business state, execution checkpoints and
traces remain separate. No production import is selected by this decision.

The operator subsequently selected **the documented Market contract with a fixture
Sales peer for now**. This unblocks fixture-based implementation of downstream
software tasks. It does not establish agreement with the real Sales implementation
or supply live policy.

## Compatibility decisions required by #11

| Boundary | Existing Market | Sales prototype | Proposed resolution for peer review |
| --- | --- | --- | --- |
| Envelope | Schema version `"1"`, stable request/correlation IDs, simulation artifacts | Separate unversioned Lead/Mandate objects | Agree a versioned business envelope inside real A2A artifacts; simulation remains explicit |
| Card | Set, number, language, printing, finish, raw/graded category and grade/company | Required name/set_code/number, en/ja, printing | Preserve full Market identity; display name must come from trusted catalog data. Never invent missing finish or grading facts |
| Lead identity | Listing ID, seller ID, snapshot version, quantity and separate costs | Lead/conversation/listing/seller IDs | Assign stable lead and conversation identity in deterministic services; retain snapshot and quantity/cost references |
| Evidence | Typed source, basis, transaction, exact card/condition, time/currency/amount | One to twenty evidence-reference strings | Agree resolvable evidence references and their scope; identify identity/photos separately from resale evidence |
| Questions-only | Missing condition/resale evidence can yield questions-only; unknown card identity requires review; no price ceiling | No ceiling, but Lead still requires card, condition and evidence | Define permitted unknowns without fabricating facts; ambiguous identity still blocks automatic contact |
| Money | Strict decimal strings, internal Decimal, normalized two-decimal JSON | Positive integer SGD minor units for ceiling | Use the decimal-string boundary requested by #11; keep any legacy conversion explicit and exact |
| Policy version | Opaque string such as `policy-1` | Positive integer | Agree a canonical opaque reference or a trusted reversible binding; do not parse a numeric suffix |
| State versions | Separate listing snapshot, assessment and conversation versions | One state_version and an outbound-round counter | Preserve separate meanings; define authoritative version ownership rather than alias counters |
| Negotiation limits | max_reassessments | max_rounds | Configure distinct reassessment and contact-round limits; neither supplies a default for the other |
| Reassessment | Strict typed Changes (identity, condition, price, quantity, delivery, fees) | String-valued extracted material_facts and unclassified messages | Validate and classify facts before applying Changes; prose and partial identity require review |
| Stock/outcomes | OwnedUnit, inspection chronology, cost and reconciled Outcome | No stock/outcome schema in PR #23 | Agree authoritative service references under #11/#16; Market consumes read-only views |

For any legacy SGD codec, `"80.00"` ↔ `8000` is exact. Floats, booleans,
fractional cents, unsupported currencies and nonpositive price authority must be
rejected. `null` must remain questions-only. Negative analytical profit is not a
valid mandate ceiling. A codec alone cannot solve the other identity/version gaps.

## Ownership and authority

- Market owns evidence qualification, exact matching, deterministic valuation and
  its bounded soft-exposure requests.
- Shared services own current policy, atomic budget holds, contact suppression,
  approvals, stock reservations and settlement. Market must not create duplicates.
- Sales owns seller conversations, conditional message proposals and its module
  implementation. This proposal does not change those modules or their ownership.
- Only the operator sets live policy or grants exact commitment approval. Neither
  peer's output or completed A2A task establishes approval, ownership or payment.

Missing live settings remain invalid. The current Market Policy already requires
cards/conditions, capital, per-item ceiling, profit, costs and soft exposure, but
has no agreed holding-limit, live-policy provenance or contact-round contract.
Those require explicit schema decisions and operator values rather than defaults.

## Acceptance required before completing #32

1. Record agreement on the rows above and the shared module/transaction boundary.
2. Implement the agreed Market boundary without changing Sales-owned modules.
3. Add round-trip/rejection fixtures covering full identity, missing condition,
   questions-only, evidence provenance, exact money, versions and stale authority.
4. Verify the agreed fixture peer first; real authenticated A2A remains #38/#12.
5. Keep live policy unset until operator values are supplied and validated.

The verified simulation and this proposal are useful preparation. They do not
complete the real shared-contract task or establish live qualification. The
operator-selected fixture target unblocks durable simulation development.
