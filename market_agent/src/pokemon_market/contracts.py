"""Strict synthetic inputs and service-owned outputs; no live authority."""

import re
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    AwareDatetime,
    BeforeValidator,
    PlainSerializer,
    StrictBool,
    model_validator,
)

Text = Annotated[str, Field(strict=True, min_length=1, max_length=300, pattern=r"\S")]
Positive = Annotated[int, Field(strict=True, gt=0)]
Version = Annotated[int, Field(strict=True, ge=0)]
Currency = Annotated[str, Field(strict=True, pattern=r"^[A-Z]{3}$")]


def parse_money(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,12}(?:\.\d{1,2})?", value):
        raise ValueError(
            "money must be a nonnegative decimal string with at most two fractional digits"
        )
    return Decimal(value)


Money = Annotated[
    Decimal, BeforeValidator(parse_money), PlainSerializer(lambda v: format(v, ".2f"))
]
Amount = Annotated[
    Decimal, Field(allow_inf_nan=False), PlainSerializer(lambda v: format(v, ".2f"))
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MarketError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class CardIdentity(Contract):
    set: Text
    number: Text
    language: Text
    printing: Text
    finish: Text
    category: Literal["raw", "graded"]
    grading_company: Text | None = None
    grade: Text | None = None

    @model_validator(mode="after")
    def grading(self):
        if self.category == "graded" and not (self.grade and self.grading_company):
            raise ValueError("graded card requires grading company and grade")
        if self.category == "raw" and (self.grade or self.grading_company):
            raise ValueError("raw card cannot have grading facts")
        return self


class Listing(Contract):
    id: Text
    seller_id: Text
    version: Positive
    card: CardIdentity | None
    quantity: Positive
    condition: Text | None
    condition_reviewed: StrictBool
    description: Annotated[str, Field(max_length=4000)]
    asking_price: Money
    currency: Currency
    delivery: Money
    fees: Money
    other_costs: Money


class Evidence(Contract):
    id: Text
    transaction_id: Text
    source: Text
    basis: Literal["completed_sale", "asking", "reference"]
    card: CardIdentity
    condition: Text
    observed_at: AwareDatetime
    currency: Currency
    gross_amount: Money
    completed: StrictBool


class ReviewedAssumption(Contract):
    id: Text
    policy_version: Text
    card: CardIdentity
    condition: Text
    gross_amount: Money
    currency: Currency
    reviewed_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def chronological(self):
        if self.expires_at <= self.reviewed_at:
            raise ValueError("invalid assumption interval")
        return self


class Policy(Contract):
    id: Text
    version: Text
    created_at: AwareDatetime
    allowed_cards: Annotated[
        tuple[CardIdentity, ...], Field(min_length=1, max_length=100)
    ]
    allowed_conditions: Annotated[tuple[Text, ...], Field(min_length=1, max_length=20)]
    minimum_observed_sales: Positive
    max_evidence_age_seconds: Positive
    allow_assumptions: StrictBool
    allow_questions: StrictBool
    required_profit: Money
    selling_fees: Money
    selling_delivery: Money
    selling_other: Money
    per_item_limit: Money
    available_capital: Money
    soft_exposure_cap: Money
    mandate_seconds: Annotated[int, Field(strict=True, gt=0, le=86400)]
    max_reassessments: Annotated[int, Field(strict=True, gt=0, le=20)]


class FixtureBundle(Contract):
    session_id: Text
    listings: Annotated[tuple[Listing, ...], Field(max_length=100)]
    evidence: Annotated[tuple[Evidence, ...], Field(max_length=1000)]
    assumptions: Annotated[tuple[ReviewedAssumption, ...], Field(max_length=100)]
    policy: Policy
    existing_soft_exposure: Money

    @model_validator(mode="after")
    def unique_records(self):
        for records in (self.listings, self.evidence, self.assumptions):
            if len({r.id for r in records}) != len(records):
                raise ValueError("duplicate record ID")
        if self.existing_soft_exposure > min(
            self.policy.available_capital, self.policy.soft_exposure_cap
        ):
            raise ValueError("inconsistent exposure baseline")
        return self


class Changes(Contract):
    identity: CardIdentity | None = None
    condition: Text | None = None
    price: Money | None = None
    quantity: Positive | None = None
    delivery: Money | None = None
    fees: Money | None = None


class Request(Contract):
    schema_version: Literal["1"] = "1"
    request_id: Text
    operation: Literal[
        "assess_opportunity",
        "issue_mandate",
        "reassess_opportunity",
        "assess_owned_unit",
        "prepare_resale",
        "negotiate_acquisition",
    ]
    correlation_id: Text
    policy_version: Text
    assessment_version: Version
    conversation_version: Version
    expires_at: AwareDatetime
    evidence_ids: Annotated[tuple[Text, ...], Field(max_length=1000)] = ()
    mandate_id: Text | None = None
    changes: Changes | None = None

    @model_validator(mode="after")
    def operation_fields(self):
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("duplicate evidence reference")
        if self.operation == "reassess_opportunity":
            if self.changes is None or not self.changes.model_fields_set:
                raise ValueError("changes required")
            if any(
                getattr(self.changes, k) is None for k in self.changes.model_fields_set
            ):
                raise ValueError("null changes are ambiguous")
        elif self.changes is not None:
            raise ValueError("changes require reassessment")
        if self.operation == "negotiate_acquisition" and not self.mandate_id:
            raise ValueError("mandate required")
        if (
            self.operation not in ("negotiate_acquisition", "reassess_opportunity")
            and self.mandate_id
        ):
            raise ValueError("unexpected mandate reference")
        return self


class Assessment(Contract):
    id: Text
    version: Version = 0
    listing_id: Text
    decision: Literal["qualified", "questions_only", "review", "rejected"]
    reasons: tuple[str, ...]
    card: CardIdentity | None
    condition: str | None
    evidence: tuple[Evidence, ...] = ()
    assumption: ReviewedAssumption | None = None
    gross_resale: Amount | None = None
    net_resale: Amount | None = None
    economic_ceiling: Amount | None = None
    item_ceiling: Amount | None = None
    acquisition_costs: Amount
    selling_costs: Amount
    required_profit: Amount
    expires_at: AwareDatetime
    pending_questions: tuple[str, ...] = ()


class Mandate(Contract):
    mode: Literal["simulation"] = "simulation"
    id: Text
    listing_id: Text
    assessment_version: Positive
    conversation_version: Version
    policy_version: Text
    status: Literal["active", "revoked", "expired"]
    expires_at: AwareDatetime
    ceiling: Amount | None
    exposure: Amount


class OwnedUnit(Contract):
    id: Text
    card: CardIdentity
    condition: Text
    acquired_at: AwareDatetime
    received_at: AwareDatetime | None
    inspected_at: AwareDatetime | None
    inspection_passed: StrictBool
    returned_at: AwareDatetime | None
    status: Literal[
        "awaiting_receipt",
        "quarantined",
        "available",
        "reserved",
        "fulfilled",
        "settled",
        "returned",
    ]
    acquisition_cost: Money

    @model_validator(mode="after")
    def chronology(self):
        if self.received_at and self.received_at < self.acquired_at:
            raise ValueError("receipt before acquisition")
        if self.inspected_at and (
            not self.received_at or self.inspected_at < self.received_at
        ):
            raise ValueError("inspection before receipt")
        if self.returned_at and (
            not self.received_at or self.returned_at < self.received_at
        ):
            raise ValueError("return before receipt")
        return self


class Outcome(Contract):
    id: Text
    unit_id: Text
    fulfilled: StrictBool
    settled: StrictBool
    reconciled: StrictBool
    proceeds: Money | None
    refunds: Money | None
    acquisition_cost: Money | None
    acquisition_recovery: Money | None
    seller_costs: Money | None


class InventoryBundle(Contract):
    units: Annotated[tuple[OwnedUnit, ...], Field(max_length=1000)]
    outcomes: Annotated[tuple[Outcome, ...], Field(max_length=1000)]

    @model_validator(mode="after")
    def consistent(self):
        units = {u.id: u for u in self.units}
        if len(units) != len(self.units) or len({o.id for o in self.outcomes}) != len(
            self.outcomes
        ):
            raise ValueError("duplicate inventory record")
        # shortcut: one lifecycle per unit; use an authoritative ledger for resale/return cycles.
        if len({o.unit_id for o in self.outcomes}) != len(self.outcomes):
            raise ValueError("one reconciled lifecycle per unit in this slice")
        for o in self.outcomes:
            if o.unit_id not in units:
                raise ValueError("unknown outcome unit")
            if (
                o.fulfilled
                and units[o.unit_id].status not in ("fulfilled", "settled")
                and not units[o.unit_id].returned_at
            ):
                raise ValueError("fulfilled stock requires physical return evidence")
            if (
                o.acquisition_cost is not None
                and o.acquisition_cost != units[o.unit_id].acquisition_cost
            ):
                raise ValueError("inconsistent acquisition cost")
            if (
                o.proceeds is not None
                and o.refunds is not None
                and o.refunds > o.proceeds
            ):
                raise ValueError("refund exceeds receipts")
            if (
                o.acquisition_recovery is not None
                and o.acquisition_recovery > units[o.unit_id].acquisition_cost
            ):
                raise ValueError("recovery exceeds cost")
        return self


class UnitSummary(Contract):
    id: Text
    status: Text
    age_days: Version
    sale_eligible: bool
    cost_basis: Amount


class OutcomeSummary(Contract):
    id: Text
    unit_id: Text
    realized_profit: Amount | None
    cash_result: Amount | None


class InventorySummary(Contract):
    units: tuple[UnitSummary, ...]
    outcomes: tuple[OutcomeSummary, ...]
    unsold_cost_basis: Amount
    realized_profit: Amount
    pending_outcomes: tuple[str, ...]


class Artifact(Contract):
    mode: Literal["simulation"] = "simulation"
    schema_version: Literal["1"] = "1"
    request_id: Text
    operation: Text
    correlation_id: Text
    assessment: Assessment | None = None
    mandate: Mandate | None = None
    inventory: InventorySummary | None = None
