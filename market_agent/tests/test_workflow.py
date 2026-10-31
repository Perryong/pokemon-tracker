import json
import os
from datetime import timedelta
from uuid import uuid4

import pytest

from pokemon_market.contracts import MarketError
from pokemon_market.workflow import WorkflowService
from pokemon_market.storage import PostgresMarketStore


@pytest.fixture
def workflow(bundle, now):
    dsn = os.environ.get('MARKET_TEST_DSN')
    if not dsn:
        pytest.skip('MARKET_TEST_DSN required for disposable PostgreSQL tests')
    store = PostgresMarketStore(dsn)
    store.setup()
    workspace = 'workflow-' + uuid4().hex
    seed = bundle.model_copy(update={'session_id': workspace})
    store.create(seed)
    clock = [now]
    service = WorkflowService(store, workspace, clock=lambda: clock[0])
    return service, clock


def test_assessment_is_durable_idempotent_and_explicitly_simulated(workflow):
    service, _ = workflow
    first = service.assess('listing-1')
    second = service.assess('listing-1')
    assert first == second
    state = service.state()
    assert state['mode'] == 'simulation' and state['peer'] == 'fixture'
    assert state['live_ready'] is False
    assert len(state['mandates']) == 1
    assert state['mandates'][0]['ceiling'] == '80.00'
    restarted = WorkflowService(service.store, service.workspace, clock=service.clock)
    assert restarted.state()['mandates'] == state['mandates']


def test_schedule_single_catch_up_and_pause_survive_restart(workflow):
    service, clock = workflow
    service.set_schedule(['09:00'], 'Asia/Singapore')
    clock[0] = clock[0] + timedelta(days=3)
    assert service.run_due() == 1
    assert service.run_due() == 0
    service.set_paused(True)
    clock[0] += timedelta(days=1)
    restarted = WorkflowService(service.store, service.workspace, clock=service.clock)
    assert restarted.state()['paused'] is True
    assert restarted.run_due() == 0


@pytest.mark.parametrize('times,zone', [(['25:00'], 'Asia/Singapore'), (['9:00'],'Asia/Singapore'), (['09:00'],'UTC'), (['09:00','09:00'],'Asia/Singapore')])
def test_invalid_schedule_rejected(workflow, times, zone):
    service, _ = workflow
    with pytest.raises(MarketError):
        service.set_schedule(times, zone)


def test_paused_manual_work_is_denied_and_does_not_create_run(workflow):
    service, _ = workflow
    service.set_paused(True)
    with pytest.raises(MarketError, match='paused'):
        service.assess('listing-1')
    assert service.state()['runs'] == []


def test_state_never_discloses_connection_information(workflow):
    service, _ = workflow
    state = json.dumps(service.state())
    assert service.store.dsn not in state
    assert 'postgresql://' not in state


def test_scenarios_are_bound_to_the_recorded_assessment(workflow):
    service, _ = workflow
    result = service.assess('listing-1')
    assert result['scenarios']['conservative']['economic_ceiling'] == '80.00'
    current = service.state()['assessments'][0]
    assert current['scenarios'] == result['scenarios']


def test_expired_worker_lease_replays_exact_request_without_extra_exposure(workflow):
    import hashlib
    import psycopg
    from psycopg.rows import dict_row

    service, clock = workflow
    job = 'manual-' + hashlib.sha256(b'listing-1:1:policy-1').hexdigest()[:32]
    service._claim(job, 'listing-1', clock[0])
    first = service._result('listing-1', job)
    with psycopg.connect(service.store.dsn, row_factory=dict_row) as conn:
        original = conn.execute('SELECT request FROM market_private.runs WHERE workspace=%s AND id=%s', (service.workspace, job)).fetchone()['request']
    exposure = service.session.reserved_exposure
    clock[0] += timedelta(seconds=121)
    restarted = WorkflowService(service.store, service.workspace, clock=service.clock)
    replay = restarted.assess('listing-1', job_id=job)
    assert replay['mandate']['id'] == first['mandate']['id']
    assert restarted.session.reserved_exposure == exposure
    assert len(restarted.state()['mandates']) == 1
    with psycopg.connect(service.store.dsn, row_factory=dict_row) as conn:
        assert conn.execute('SELECT request FROM market_private.runs WHERE workspace=%s AND id=%s', (service.workspace, job)).fetchone()['request'] == original


def test_active_lease_blocks_concurrent_worker(workflow):
    service, clock = workflow
    service._claim('same-job', 'listing-1', clock[0])
    second = WorkflowService(service.store, service.workspace, clock=service.clock)
    with pytest.raises(MarketError, match='run_in_progress'):
        second.assess('listing-1', job_id='same-job')
    assert service.state()['mandates'] == []


def test_manual_assessment_renews_after_expiry_without_duplicate_exposure(workflow):
    service, clock = workflow
    first = service.assess('listing-1')
    clock[0] += timedelta(minutes=16)
    renewed = service.assess('listing-1')
    assert renewed['assessment']['version'] == 2
    assert renewed['mandate']['id'] != first['mandate']['id']
    assert renewed['mandate']['status'] == 'active'
    assert service.assess('listing-1') == renewed
    assert str(service.session.reserved_exposure) == '85.00'


def test_transient_peer_retry_reuses_request_and_mandate_and_is_bounded(workflow):
    service, _ = workflow
    calls = []
    def unavailable(artifact):
        calls.append(artifact.mandate.id)
        raise MarketError('fixture_peer_unavailable')
    service.peer = unavailable
    with pytest.raises(MarketError, match='fixture_peer_unavailable'):
        service.assess('listing-1')
    service.peer = lambda artifact: calls.append(artifact.mandate.id)
    recovered = service.assess('listing-1')
    assert calls == [recovered['mandate']['id']] * 2
    assert len(service.state()['mandates']) == 1
    assert str(service.session.reserved_exposure) == '85.00'

    service.peer = unavailable
    for _ in range(3):
        with pytest.raises(MarketError, match='fixture_peer_unavailable'):
            service.assess('listing-1', job_id='bounded-retry')
    with pytest.raises(MarketError, match='run_failed'):
        service.assess('listing-1', job_id='bounded-retry')


def test_worker_recovers_expired_manual_lease_without_a_schedule(workflow):
    service, clock = workflow
    service._claim('interrupted-manual', 'listing-1', clock[0])
    service._result('listing-1', 'interrupted-manual')
    clock[0] += timedelta(seconds=121)
    restarted = WorkflowService(service.store, service.workspace, clock=service.clock)
    assert restarted.run_due() == 1
    assert restarted.state()['runs'][0]['status'] == 'completed'
    assert len(restarted.state()['mandates']) == 1


def test_concurrent_material_change_cannot_relabel_scenarios_or_active_authority(workflow):
    service, _ = workflow
    def change_listing(_artifact):
        listing = service.session.read_listing('listing-1')
        service.session.ingest_listing(listing.model_copy(update={'version': listing.version + 1, 'fees': __import__('decimal').Decimal('50.00')}))
    service.peer = change_listing
    result = service.assess('listing-1')
    assert result['mandate']['status'] == 'revoked'
    assert 'scenarios' not in result


def test_scenario_metadata_references_the_exact_persisted_assessment(workflow):
    service, _ = workflow
    result = service.assess('listing-1')
    assert result['scenarios']['assessment'] == result['assessment']


def test_operator_view_bounds_inactive_history_without_hiding_active_mandates(workflow, monkeypatch):
    service, _ = workflow
    service.assess('listing-1')
    original = service.session.snapshot()
    current = original['mandates'][0]
    history = [dict(current, id='expired-' + str(i), status='expired') for i in range(1001)]
    monkeypatch.setattr(service.session, 'snapshot', lambda: dict(original, mandates=history + [current]))
    state = service.state()
    assert len(state['mandates']) == 1000
    assert state['mandates'][0] == current
    assert len(service.store.session(service.workspace, clock=service.clock).snapshot()['mandates']) == 1


def test_pause_between_graph_and_peer_suspends_work_until_resume(workflow, monkeypatch):
    import pokemon_market.workflow as module

    service, _ = workflow
    original = module.run_agent
    dispatched = []
    service.peer = lambda result: dispatched.append(result.mandate.id)
    def pause_after_graph(*args, **kwargs):
        result = original(*args, **kwargs)
        service.set_paused(True)
        return result
    monkeypatch.setattr(module, 'run_agent', pause_after_graph)
    with pytest.raises(MarketError, match='paused'):
        service.assess('listing-1')
    assert dispatched == []
    assert service.state()['runs'][0]['status'] == 'queued'
    assert service.run_due() == 0
    monkeypatch.setattr(module, 'run_agent', original)
    service.set_paused(False)
    assert service.run_due() == 1
    assert len(dispatched) == 1
    assert len(service.state()['mandates']) == 1


def test_inspection_uses_persisted_scope_and_current_listing_identity(workflow):
    service, clock = workflow
    listing = service.session.read_listing('listing-1')
    service.session.ingest_listing(listing.model_copy(update={'version': 2, 'condition': 'damaged', 'condition_reviewed': False}))
    state = service.state()
    assert state['captured_at'] == clock[0].isoformat()
    assert state['scope']['policy_version'] == 'policy-1'
    assert state['scope']['allowed_cards'][0]['number'] == '001'
    assert state['scope']['allowed_conditions'] == ['near_mint']
    assert state['scope']['max_evidence_age_seconds'] == 604800
    assert state['listings'][0] == {
        'id': 'listing-1', 'version': 2, 'card': listing.card.model_dump(mode='json'),
        'condition': 'damaged', 'condition_reviewed': False,
    }
    assert 'seller_id' not in state['listings'][0]


def test_next_schedule_matches_latest_catch_up_then_future_slot_and_pause(workflow):
    service, clock = workflow
    assert service.state()['next_scheduled_at'] is None
    service.set_schedule(['09:00', '18:00'], 'Asia/Singapore')
    assert service.state()['next_scheduled_at'] == clock[0].replace(hour=1).isoformat()
    assert service.run_due() == 1
    assert service.state()['next_scheduled_at'] == clock[0].replace(hour=10).isoformat()
    service.set_paused(True)
    assert service.state()['next_scheduled_at'] is None
    service.set_paused(False)
    assert service.state()['next_scheduled_at'] == clock[0].replace(hour=10).isoformat()


@pytest.mark.parametrize(('hour', 'minute', 'slot', 'next_hour', 'next_minute', 'day_offset'), [
    (4, 0, '12:00', 4, 0, 1),
    (15, 59, '00:05', 16, 5, 0),
])
def test_next_schedule_handles_exact_slot_and_singapore_midnight(workflow, hour, minute, slot, next_hour, next_minute, day_offset):
    service, clock = workflow
    clock[0] = clock[0].replace(hour=hour, minute=minute)
    service.set_schedule([slot], 'Asia/Singapore')
    assert service.state()['next_scheduled_at'] <= clock[0].isoformat()
    service.run_due()
    expected = (clock[0] + timedelta(days=day_offset)).replace(hour=next_hour, minute=next_minute)
    assert service.state()['next_scheduled_at'] == expected.isoformat()


def test_connection_status_requires_recorded_dispatch_not_a_completed_graph(workflow):
    service, clock = workflow
    service.assess('listing-1')
    assert service.state()['sales_connection'] == {'configured': False, 'last_dispatch': None}
    def unavailable(_artifact):
        raise MarketError('fixture_peer_unavailable')
    service.peer = unavailable
    clock[0] += timedelta(seconds=1)
    with pytest.raises(MarketError, match='fixture_peer_unavailable'):
        service.assess('listing-1', job_id='peer-attempt')
    assert service.state()['sales_connection'] == {
        'configured': True, 'last_dispatch': {'status': 'failed', 'at': clock[0].isoformat()},
    }
    clock[0] += timedelta(seconds=1)
    service.peer = lambda _artifact: None
    service.assess('listing-1', job_id='peer-attempt')
    assert service.state()['sales_connection']['last_dispatch'] == {'status': 'succeeded', 'at': clock[0].isoformat()}


def test_failed_dispatch_history_survives_retry_and_pre_dispatch_failure(workflow, monkeypatch):
    service, clock = workflow
    service.peer = lambda _artifact: None
    service.assess('listing-1', job_id='older-success')
    clock[0] += timedelta(seconds=1)
    def unavailable(_artifact):
        raise MarketError('fixture_peer_unavailable')
    service.peer = unavailable
    with pytest.raises(MarketError, match='fixture_peer_unavailable'):
        service.assess('listing-1', job_id='later-failure')
    failure = {'status': 'failed', 'at': clock[0].isoformat()}
    assert service.state()['sales_connection']['last_dispatch'] == failure
    clock[0] += timedelta(seconds=1)
    def fail_before_dispatch(*_args):
        assert service.state()['sales_connection']['last_dispatch'] == failure
        raise MarketError('expired_request')
    monkeypatch.setattr(service, '_result', fail_before_dispatch)
    with pytest.raises(MarketError, match='expired_request'):
        service.assess('listing-1', job_id='later-failure')
    restarted = WorkflowService(service.store, service.workspace, clock=service.clock)
    assert restarted.state()['sales_connection']['last_dispatch'] == failure
