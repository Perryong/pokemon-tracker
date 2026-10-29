"""Read-only synthetic inventory and cash outcomes, never stock mutations."""
from datetime import datetime
from decimal import Decimal
from .contracts import (InventoryBundle, InventorySummary, MarketError, Outcome,
                        OutcomeSummary, OwnedUnit, UnitSummary)

def summarize_inventory(units: tuple[OwnedUnit,...], outcomes: tuple[Outcome,...], now: datetime) -> InventorySummary:
    # Revalidate callers as well as packaged fixtures before reporting financial facts.
    data = InventoryBundle.model_validate_json(InventoryBundle(units=units,outcomes=outcomes).model_dump_json())
    if now.tzinfo is None: raise MarketError('naive_clock')
    result=[]; total=Decimal('0'); unsold=Decimal('0'); pending=[]; unit_rows=[]
    by_unit={o.unit_id:o for o in data.outcomes}
    for u in data.units:
        dates=(u.acquired_at,u.received_at,u.inspected_at,u.returned_at)
        if any(d and d>now for d in dates): raise MarketError('future_inventory')
        eligible=bool(u.status=='available' and u.received_at and u.inspected_at and u.inspection_passed
                      and (u.returned_at is None or u.inspected_at>u.returned_at))
        outcome=by_unit.get(u.id)
        recovery=outcome.acquisition_recovery if outcome and outcome.acquisition_recovery is not None else Decimal('0')
        basis=u.acquisition_cost-recovery
        if u.status not in ('fulfilled','settled'): unsold+=basis
        unit_rows.append(UnitSummary(id=u.id,status=u.status,age_days=(now-u.acquired_at).days,
                                     sale_eligible=eligible,cost_basis=basis))
    for o in data.outcomes:
        fields=(o.proceeds,o.refunds,o.acquisition_cost,o.acquisition_recovery,o.seller_costs)
        profit=None; cash=None
        if o.fulfilled and o.settled and o.reconciled and all(x is not None for x in fields):
            cash=o.proceeds-o.refunds-o.acquisition_cost+o.acquisition_recovery-o.seller_costs
            profit=cash
            unit=next(u for u in data.units if u.id==o.unit_id)
            # Returned stock retains its basis; cash outlay is not a second realized loss.
            if unit.returned_at and unit.status not in ('fulfilled','settled'):
                profit+=unit.acquisition_cost-o.acquisition_recovery
            total+=profit
        else: pending.append(o.id)
        result.append(OutcomeSummary(id=o.id,unit_id=o.unit_id,realized_profit=profit,cash_result=cash))
    return InventorySummary(units=tuple(unit_rows),outcomes=tuple(result),unsold_cost_basis=unsold,
                            realized_profit=total,pending_outcomes=tuple(pending))
