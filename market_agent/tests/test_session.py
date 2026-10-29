from datetime import timedelta
from decimal import Decimal
import pytest
from pokemon_market.contracts import FixtureBundle, Listing, MarketError, Request
from pokemon_market.session import MarketSession

def request(base, **updates):
    return Request.model_validate(base.model_dump(mode='json') | updates)

def issue(s, r):
    a = s.handle(r)
    return s.handle(request(r, request_id=r.request_id+'-mandate', operation='issue_mandate', assessment_version=a.assessment.version))

def test_price_and_replay(session, qualified_request):
    out = issue(session, qualified_request)
    assert out.mandate.ceiling == Decimal('80') and session.reserved_exposure == Decimal('85')
    m = request(qualified_request,request_id='request-1-mandate',operation='issue_mandate',assessment_version=1)
    assert session.handle(m) == out
    assert session.handle(request(m,request_id='new')).mandate.id == out.mandate.id
    assert session.reserved_exposure == Decimal('85')

def test_payload_conflict(session, qualified_request):
    session.handle(qualified_request)
    with pytest.raises(MarketError,match='request_conflict'):
        session.handle(request(qualified_request, evidence_ids=['e1']))

@pytest.mark.parametrize('capital,baseline,ceiling', [('84.00','0.00','79.00'),('100.00','20.00','75.00')])
def test_headroom(raw, now, qualified_request, capital, baseline, ceiling):
    raw['policy']['available_capital']=capital; raw['existing_soft_exposure']=baseline
    s=MarketSession(FixtureBundle.model_validate(raw),clock=lambda:now)
    assert issue(s,qualified_request).mandate.ceiling == Decimal(ceiling)

def test_no_headroom(raw, now, qualified_request):
    raw['policy']['available_capital']='5.00'
    s=MarketSession(FixtureBundle.model_validate(raw),clock=lambda:now)
    out=issue(s,qualified_request)
    assert out.mandate is None and out.assessment.decision=='rejected'
    assert s.reserved_exposure==0

def test_questions_only(raw, now, qualified_request):
    raw['listings'][0]['condition']=None
    s=MarketSession(FixtureBundle.model_validate(raw),clock=lambda:now)
    assert issue(s,qualified_request).mandate.ceiling is None
    assert s.reserved_exposure==0

def test_reassessment_and_historical_replay(session, qualified_request):
    old=issue(session,qualified_request)
    r=request(qualified_request,request_id='change',operation='reassess_opportunity',assessment_version=1,changes={'quantity':2})
    out=session.handle(r)
    assert out.assessment.decision=='review'
    assert session.current_mandate(old.mandate.id).status=='revoked'
    assert session.reserved_exposure==0
    assert session.handle(r)==out
    replay=session.handle(request(qualified_request,request_id='request-1-mandate',operation='issue_mandate',assessment_version=1))
    assert replay==old and session.current_mandate(replay.mandate.id).status=='revoked'
    assert session.reserved_exposure==0

def test_stale_change_does_not_mutate(session, qualified_request):
    out=issue(session,qualified_request)
    with pytest.raises(MarketError,match='stale_state'):
        session.handle(request(qualified_request,request_id='stale',operation='reassess_opportunity',changes={'quantity':2}))
    assert session.current_mandate(out.mandate.id).status=='active'

def test_changed_condition_needs_review(session, qualified_request):
    issue(session,qualified_request)
    a=session.handle(request(qualified_request,request_id='change',operation='reassess_opportunity',assessment_version=1,changes={'condition':'near_mint'}))
    assert a.assessment.decision=='questions_only'

def test_failed_reassessment_still_revokes(session, qualified_request, monkeypatch):
    import pokemon_market.session as module
    old=issue(session,qualified_request)
    def failure(*args,**kwargs): raise MarketError('evidence_unavailable')
    monkeypatch.setattr(module,'assess',failure)
    r=request(qualified_request,request_id='change',operation='reassess_opportunity',assessment_version=1,changes={'price':'70.00'})
    for _ in range(2):
        with pytest.raises(MarketError,match='evidence_unavailable'): session.handle(r)
    assert session.current_mandate(old.mandate.id).status=='revoked'
    assert session.reserved_exposure==0

def test_expiry_releases_once(bundle, now, qualified_request):
    clock=[now]; s=MarketSession(bundle,clock=lambda:clock[0]); m=issue(s,qualified_request).mandate
    clock[0]=m.expires_at
    assert s.current_mandate(m.id).status=='expired'
    assert s.reserved_exposure==0 and s.reserved_exposure==0
    with pytest.raises(MarketError,match='expired_request'):
        s.handle(request(qualified_request,request_id='late'))

@pytest.mark.parametrize('changes,code', [({'policy_version':'old'},'stale_policy'),({'correlation_id':'other'},'record_not_found'),({'evidence_ids':['other']},'record_not_found')])
def test_scope(session, qualified_request, changes, code):
    with pytest.raises(MarketError,match=code): session.handle(request(qualified_request,**changes))

def test_reassessment_limit(session, qualified_request):
    issue(session,qualified_request)
    for i in range(1,4):
        session.handle(request(qualified_request,request_id=f'change-{i}',operation='reassess_opportunity',
                               assessment_version=i,conversation_version=i-1,changes={'price':'70.00'}))
    with pytest.raises(MarketError,match='reassessment_limit'):
        session.handle(request(qualified_request,request_id='change-4',operation='reassess_opportunity',
                               assessment_version=4,conversation_version=3,changes={'price':'70.00'}))

def test_two_opportunities(raw, now, qualified_request):
    raw['listings'].append(dict(raw['listings'][0],id='listing-2',seller_id='seller-2'))
    s=MarketSession(FixtureBundle.model_validate(raw),clock=lambda:now)
    issue(s,qualified_request)
    second=issue(s,request(qualified_request,request_id='second',correlation_id='listing-2'))
    assert second.mandate.ceiling==Decimal('60')
    assert s.reserved_exposure==Decimal('150')

def test_snapshot_change_revokes(session, qualified_request):
    old=issue(session,qualified_request)
    updated=Listing.model_validate(session.read_listing('listing-1').model_dump(mode='json')|{'version':2,'quantity':2})
    session.ingest_listing(updated)
    assert session.current_mandate(old.mandate.id).status=='revoked'
    a=session.handle(request(qualified_request,request_id='snapshot',assessment_version=1))
    assert a.assessment.decision=='review'

def test_foreign_mandate(raw, now, qualified_request):
    raw['listings'].append(dict(raw['listings'][0],id='listing-2',seller_id='seller-2'))
    s=MarketSession(FixtureBundle.model_validate(raw),clock=lambda:now)
    m=issue(s,qualified_request).mandate
    issue(s,request(qualified_request,request_id='second',correlation_id='listing-2'))
    with pytest.raises(MarketError,match='mandate_scope'):
        s.handle(request(qualified_request,request_id='handoff',operation='negotiate_acquisition',correlation_id='listing-2',assessment_version=1,mandate_id=m.id))
