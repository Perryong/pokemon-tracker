from copy import deepcopy
from decimal import Decimal
import pytest
from pokemon_market.contracts import FixtureBundle, MarketError
from pokemon_market.valuation import assess

def evaluate(raw, now):
    b = FixtureBundle.model_validate(raw)
    return assess(b.listings[0], b.evidence, b.assumptions, b.policy, now)

def assumption(raw, amount='140.00'):
    return dict(id='a1',policy_version='policy-1',card=raw['policy']['allowed_cards'][0],
                condition='near_mint',gross_amount=amount,currency='SGD',
                reviewed_at='2026-10-29T04:00:00Z',expires_at='2026-10-31T04:00:00Z')

def test_exact_economics(raw, now):
    a = evaluate(raw, now)
    assert (a.decision, a.gross_resale, a.net_resale, a.item_ceiling) == ('qualified', Decimal('120'), Decimal('105'), Decimal('80'))
    assert a.acquisition_costs == Decimal('5')
    assert len(a.evidence) == 2

def test_lowest_sale(raw, now):
    raw['evidence'][1]['gross_amount'] = '110.00'
    assert evaluate(raw, now).item_ceiling == Decimal('70')

@pytest.mark.parametrize('field,value', [('language','ja'),('finish','reverse'),('printing','promo'),('number','002'),('category','graded')])
def test_exact_identity(raw, now, field, value):
    raw['listings'][0]['card'][field] = value
    if field == 'category': raw['listings'][0]['card'].update(grade='10',grading_company='PSA')
    a = evaluate(raw, now)
    assert a.decision == 'review' and a.item_ceiling is None

@pytest.mark.parametrize('field,value', [('card',None),('quantity',2),('currency','USD')])
def test_unsupported_listing(raw, now, field, value):
    raw['listings'][0][field] = value
    assert evaluate(raw, now).decision == 'review'

def test_condition_unknown(raw, now):
    raw['listings'][0]['condition'] = None
    assert evaluate(raw, now).decision == 'questions_only'
    raw['policy']['allow_questions'] = False
    assert evaluate(raw, now).decision == 'review'

def test_disallowed_condition(raw, now):
    raw['listings'][0]['condition'] = 'damaged'
    assert evaluate(raw, now).decision == 'rejected'

@pytest.mark.parametrize('field,value', [('basis','asking'),('basis','reference'),('currency','USD'),('completed',False),('observed_at','2026-10-31T04:00:00Z'),('observed_at','2026-10-22T04:00:00Z')])
def test_ineligible_evidence(raw, now, field, value):
    raw['evidence'][0][field] = value
    a = evaluate(raw, now)
    assert a.decision == 'questions_only' and a.item_ceiling is None

def test_exact_age_boundary(raw, now):
    raw['evidence'][0]['observed_at'] = '2026-10-23T04:00:00Z'
    assert evaluate(raw, now).decision == 'qualified'

def test_duplicate_transaction_not_sample(raw, now):
    raw['evidence'][1] = dict(raw['evidence'][0], id='e2')
    assert evaluate(raw, now).decision == 'questions_only'

def test_conflicting_transaction(raw, now):
    raw['evidence'][1]['transaction_id'] = 't1'
    assert evaluate(raw, now).decision == 'review'

def test_reviewed_assumption_fallback(raw, now):
    raw['evidence'] = []; raw['assumptions'] = [assumption(raw)]
    a = evaluate(raw, now)
    assert a.item_ceiling == Decimal('100') and a.assumption.id == 'a1'
    assert 'reviewed_assumption' in a.reasons
    raw['policy']['allow_assumptions'] = False
    assert evaluate(raw, now).item_ceiling is None

@pytest.mark.parametrize('field,value', [('expires_at','2026-10-30T04:00:00Z'),('policy_version','old'),('reviewed_at','2026-10-30T05:00:00Z')])
def test_unusable_assumption(raw, now, field, value):
    raw['evidence'] = []; a = assumption(raw); a[field] = value; raw['assumptions'] = [a]
    assert evaluate(raw, now).item_ceiling is None

def test_conflicting_assumptions(raw, now):
    raw['evidence'] = []; raw['assumptions'] = [assumption(raw),dict(assumption(raw, '150.00'),id='a2')]
    assert evaluate(raw, now).decision == 'review'

def test_assumption_cannot_raise_observed_ceiling(raw, now):
    raw['assumptions'] = [assumption(raw)]
    assert evaluate(raw, now).item_ceiling == Decimal('80')

def test_unprofitable(raw, now):
    raw['policy']['required_profit'] = '101.00'
    assert evaluate(raw, now).decision == 'rejected'

def test_policy_cannot_be_future(raw, now):
    raw['policy']['created_at'] = '2026-11-01T00:00:00Z'
    with pytest.raises(MarketError, match='future_policy'): evaluate(raw, now)
