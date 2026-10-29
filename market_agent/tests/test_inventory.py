import json
from decimal import Decimal
from pathlib import Path
import pytest
from pydantic import ValidationError
from pokemon_market.contracts import InventoryBundle, MarketError, Request
from pokemon_market.inventory import summarize_inventory
from pokemon_market.session import MarketSession


@pytest.fixture
def stock_raw():
    return json.loads(
        (
            Path(__file__).parents[1] / "src/pokemon_market/fixtures/inventory.json"
        ).read_text()
    )


def summary(data, now):
    b = InventoryBundle.model_validate(data)
    return summarize_inventory(b.units, b.outcomes, now)


def test_summary(stock_raw, now):
    s = summary(stock_raw, now)
    assert s.units[0].age_days == 10 and s.units[0].sale_eligible
    assert s.unsold_cost_basis == Decimal("85")
    assert {o.id: o.realized_profit for o in s.outcomes} == {
        "sale": Decimal("20"),
        "refund": Decimal("-15"),
        "pending": None,
    }
    assert s.realized_profit == Decimal("5") and s.pending_outcomes == ("pending",)


@pytest.mark.parametrize(
    "patch",
    [
        {"received_at": None, "inspected_at": None},
        {"inspection_passed": False},
        {"status": "reserved"},
        {"returned_at": "2026-10-29T04:00:00Z"},
    ],
)
def test_unavailable(stock_raw, now, patch):
    stock_raw["units"][0].update(patch)
    assert not summary(stock_raw, now).units[0].sale_eligible


def test_pending_cost_not_zero(stock_raw, now):
    stock_raw["outcomes"][0]["seller_costs"] = None
    assert summary(stock_raw, now).outcomes[0].realized_profit is None


def test_duplicate_outcomes(stock_raw):
    stock_raw["outcomes"].append(stock_raw["outcomes"][0])
    with pytest.raises(ValidationError):
        InventoryBundle.model_validate(stock_raw)


def test_future_acquisition(stock_raw, now):
    stock_raw["units"][0].update(
        acquired_at="2026-11-01T00:00:00Z", received_at=None, inspected_at=None
    )
    with pytest.raises(MarketError, match="future_inventory"):
        summary(stock_raw, now)


def test_bad_chronology(stock_raw):
    stock_raw["units"][0]["received_at"] = "2026-10-19T00:00:00Z"
    with pytest.raises(ValidationError):
        InventoryBundle.model_validate(stock_raw)


def test_stock_scope_and_resale(bundle, stock_raw, now, qualified_request):
    s = MarketSession(
        bundle, clock=lambda: now, inventory=InventoryBundle.model_validate(stock_raw)
    )
    data = qualified_request.model_dump(mode="json") | {
        "operation": "prepare_resale",
        "correlation_id": "available",
    }
    out = s.handle(Request.model_validate(data))
    assert out.inventory.units[0].sale_eligible and out.mandate is None
    assert out.assessment.item_ceiling == Decimal(
        "85"
    )  # Owned unit has no proposed acquisition fees.
    with pytest.raises(MarketError, match="stock_unavailable"):
        s.handle(
            Request.model_validate(
                data | {"request_id": "returned", "correlation_id": "returned"}
            )
        )
    with pytest.raises(MarketError, match="record_not_found"):
        s.read_owned_unit("other")
    assert s.reserved_exposure == 0


def test_owned_unit_insufficient_evidence(bundle, stock_raw, now, qualified_request):
    s = MarketSession(
        bundle, clock=lambda: now, inventory=InventoryBundle.model_validate(stock_raw)
    )
    data = qualified_request.model_dump(mode="json") | {
        "operation": "assess_owned_unit",
        "correlation_id": "available",
        "evidence_ids": [],
    }
    assert s.handle(Request.model_validate(data)).assessment.item_ceiling is None


def test_empty(now):
    assert summarize_inventory((), (), now).unsold_cost_basis == 0


def test_refunded_return_keeps_stock_basis_without_expensing_twice(stock_raw, now):
    stock_raw["outcomes"][1]["acquisition_recovery"] = "0.00"
    s = summary(stock_raw, now)
    assert s.unsold_cost_basis == Decimal("170")
    assert s.outcomes[1].realized_profit == Decimal("-15")
    assert s.outcomes[1].cash_result == Decimal("-100")


def test_fulfilled_available_unit_needs_return_evidence(stock_raw):
    stock_raw["units"][1]["status"] = "available"
    with pytest.raises(ValidationError):
        InventoryBundle.model_validate(stock_raw)
