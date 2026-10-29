"""Evidence qualification and decimal economics, with no issuance authority."""

from datetime import datetime, timedelta
from .contracts import (
    Assessment,
    Evidence,
    Listing,
    MarketError,
    Policy,
    ReviewedAssumption,
)


def assess(
    listing: Listing,
    evidence: tuple[Evidence, ...],
    assumptions: tuple[ReviewedAssumption, ...],
    policy: Policy,
    now: datetime,
) -> Assessment:
    if now.tzinfo is None:
        raise MarketError("naive_clock")
    if policy.created_at > now:
        raise MarketError("future_policy")
    acquisition = listing.delivery + listing.fees + listing.other_costs
    selling = policy.selling_fees + policy.selling_delivery + policy.selling_other
    expiry = now + timedelta(seconds=policy.mandate_seconds)
    base = dict(
        id=f"assessment-{listing.id}",
        listing_id=listing.id,
        card=listing.card,
        condition=listing.condition,
        evidence=evidence,
        acquisition_costs=acquisition,
        selling_costs=selling,
        required_profit=policy.required_profit,
        expires_at=expiry,
    )

    def result(decision, reason, **values):
        return Assessment(**(base | values), decision=decision, reasons=(reason,))

    def questions(reason):
        return result(
            "questions_only" if policy.allow_questions else "review",
            reason,
            pending_questions=(
                "Confirm condition and provide comparable resale evidence.",
            ),
        )

    if listing.quantity != 1 or listing.card not in policy.allowed_cards:
        return result("review", "identity_or_bundle")
    if listing.currency != "SGD":
        return result("review", "unsupported_currency")
    if listing.condition and listing.condition not in policy.allowed_conditions:
        return result("rejected", "condition_disallowed")
    if not listing.condition or not listing.condition_reviewed:
        return questions("condition_unverified")
    eligible = {}
    excluded = []
    for e in evidence:
        age = (now - e.observed_at).total_seconds()
        if not (
            e.card == listing.card
            and e.condition == listing.condition
            and e.currency == "SGD"
            and e.basis == "completed_sale"
            and e.completed
            and 0 <= age <= policy.max_evidence_age_seconds
        ):
            excluded.append(e.id)
            continue
        key = (e.source, e.transaction_id)
        if key in eligible:
            old = eligible[key].model_dump(exclude={"id"})
            if e.model_dump(exclude={"id"}) != old:
                return result("review", "conflicting_transaction")
        else:
            eligible[key] = e
    assumption = None
    if len(eligible) >= policy.minimum_observed_sales:
        gross = min(e.gross_amount for e in eligible.values())
        # Authority cannot outlive the evidence used to qualify it.
        expiry = min(
            expiry,
            *(
                e.observed_at + timedelta(seconds=policy.max_evidence_age_seconds)
                for e in eligible.values()
            ),
        )
        reason = "observed_sales"
    else:
        allowed = [
            a
            for a in assumptions
            if policy.allow_assumptions
            and a.card == listing.card
            and a.condition == listing.condition
            and a.policy_version == policy.version
            and a.currency == "SGD"
            and a.reviewed_at <= now < a.expires_at
        ]
        if len(allowed) > 1:
            return result("review", "conflicting_assumptions")
        if not allowed:
            return questions("insufficient_evidence")
        assumption = allowed[0]
        gross = assumption.gross_amount
        expiry = min(expiry, assumption.expires_at)
        reason = "reviewed_assumption"
    net = gross - selling
    ceiling = net - policy.required_profit - acquisition
    values = dict(
        gross_resale=gross,
        net_resale=net,
        economic_ceiling=ceiling,
        assumption=assumption,
        expires_at=expiry,
    )
    if ceiling <= 0:
        return result("rejected", "unprofitable", **values)
    a = result("qualified", reason, item_ceiling=ceiling, **values)
    return a.model_copy(
        update={
            "reasons": a.reasons + tuple(f"excluded_evidence:{i}" for i in excluded)
        }
    )
