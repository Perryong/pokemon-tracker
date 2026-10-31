"""Durable, single-workspace fixture discovery. No live marketplace connector."""

import hashlib
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from langgraph.checkpoint.postgres import PostgresSaver

from .contracts import MarketError, Request
from .controlled import ControlledModel
from .harness import run_agent


def _schedule_slots(times, now):
    local = now.astimezone(ZoneInfo('Asia/Singapore'))
    slots = [local.replace(hour=int(time[:2]), minute=int(time[3:]), second=0, microsecond=0) for time in times]
    latest = max((slot if slot <= local else slot - timedelta(days=1) for slot in slots), default=None)
    upcoming = min((slot if slot > local else slot + timedelta(days=1) for slot in slots), default=None)
    return (latest.astimezone(timezone.utc) if latest else None,
            upcoming.astimezone(timezone.utc) if upcoming else None)


class WorkflowService:
    def __init__(self, store, workspace, *, clock=None, peer=None):
        self.store = store
        self.workspace = workspace
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.peer = peer
        self.session = store.session(workspace, clock=self.clock)
        self.session.snapshot()  # Refuse an unknown workspace before creating jobs.
        with psycopg.connect(store.dsn) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS market_private.workflows (
                workspace text PRIMARY KEY REFERENCES market_private.sessions(session_id),
                schedule jsonb NOT NULL, paused boolean NOT NULL DEFAULT false,
                last_slot timestamptz)
            """)
            conn.execute("""CREATE TABLE IF NOT EXISTS market_private.runs (
                workspace text NOT NULL REFERENCES market_private.sessions(session_id),
                id text NOT NULL, listing_id text, scheduled_for timestamptz NOT NULL,
                status text NOT NULL, lease_until timestamptz, owner text,
                completed_at timestamptz, error text, request jsonb, result jsonb, attempts integer NOT NULL DEFAULT 0,
                PRIMARY KEY(workspace,id))
            """)
            conn.execute("ALTER TABLE market_private.runs ADD COLUMN IF NOT EXISTS attempts integer NOT NULL DEFAULT 0")
            conn.execute("INSERT INTO market_private.workflows(workspace,schedule) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                         (workspace, Jsonb({'times': [], 'timezone': 'Asia/Singapore'})))
            conn.execute("CREATE SCHEMA IF NOT EXISTS market_checkpoints")
            conn.execute("REVOKE ALL ON SCHEMA market_checkpoints FROM PUBLIC")
        with self._checkpoint_connection() as conn:
            PostgresSaver(conn).setup()

    def _checkpoint_connection(self):
        return psycopg.connect(self.store.dsn, autocommit=True, row_factory=dict_row,
                              prepare_threshold=0, options='-c search_path=market_checkpoints')

    def state(self):
        now = self.clock()
        snapshot = self.session.snapshot()
        with psycopg.connect(self.store.dsn, row_factory=dict_row) as conn:
            control = conn.execute('SELECT schedule,paused,last_slot FROM market_private.workflows WHERE workspace=%s', (self.workspace,)).fetchone()
            runs = conn.execute('SELECT id,status,scheduled_for,completed_at,error,result FROM market_private.runs WHERE workspace=%s ORDER BY scheduled_for DESC,id LIMIT 100', (self.workspace,)).fetchall()
        scenarios = {}
        dispatches = []
        for run in runs:
            result = run.pop('result')
            if run['completed_at'] and run['error'] == 'fixture_peer_unavailable':
                dispatches.append({'status': 'failed', 'at': run['completed_at']})
            elif run['completed_at'] and run['status'] == 'completed' and result and result.get('peer_dispatched') is True:
                dispatches.append({'status': 'succeeded', 'at': run['completed_at']})
            elif result and result.get('last_dispatch'):
                dispatch = result['last_dispatch']
                dispatches.append(dict(dispatch, at=datetime.fromisoformat(dispatch['at'])))
            if result and result.get('assessment') and result.get('scenarios'):
                scenarios.setdefault(result['assessment']['id'], result['scenarios'])
            for key in ('scheduled_for', 'completed_at'):
                if run[key] is not None:
                    run[key] = run[key].isoformat()
        for assessment in snapshot['assessments']:
            if assessment['id'] in scenarios:
                assessment['scenarios'] = scenarios[assessment['id']]
        # Keep the operator payload bounded; durable history is never deleted.
        mandates = sorted(snapshot['mandates'], key=lambda item: (item['status'] == 'active', item['expires_at']), reverse=True)[:1000]
        latest, upcoming = _schedule_slots(control['schedule']['times'], now)
        next_slot = latest if latest and (control['last_slot'] is None or latest > control['last_slot']) else upcoming
        last_dispatch = max(dispatches, key=lambda item: item['at'], default=None)
        if last_dispatch:
            last_dispatch['at'] = last_dispatch['at'].isoformat()
        policy = snapshot['policy']
        return dict(mode='simulation', peer='fixture', live_ready=False,
                    captured_at=now.isoformat(),
                    scope=dict(policy_version=policy['version'], allowed_cards=policy['allowed_cards'],
                               allowed_conditions=policy['allowed_conditions'], max_evidence_age_seconds=policy['max_evidence_age_seconds']),
                    next_scheduled_at=next_slot.isoformat() if next_slot and not control['paused'] else None,
                    sales_connection=dict(configured=self.peer is not None, last_dispatch=last_dispatch),
                    paused=control['paused'], schedule=control['schedule'], runs=runs,
                    assessments=snapshot['assessments'], mandates=mandates,
                    inventory=snapshot['inventory'],
                    listings=[{key: x[key] for key in ('id', 'version', 'card', 'condition', 'condition_reviewed')} for x in snapshot['listings']],
                    blocked_reasons=['Live marketplace connector, real Sales peer and operator live policy are not configured.'])

    def set_schedule(self, times, zone):
        if zone != 'Asia/Singapore' or not isinstance(times, list) or not 1 <= len(times) <= 8:
            raise MarketError('invalid_schedule')
        if any(not isinstance(t, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', t) for t in times):
            raise MarketError('invalid_schedule')
        if len(set(times)) != len(times):
            raise MarketError('invalid_schedule')
        with psycopg.connect(self.store.dsn) as conn:
            conn.execute('UPDATE market_private.workflows SET schedule=%s WHERE workspace=%s',
                         (Jsonb({'times': sorted(times), 'timezone': zone}), self.workspace))

    def set_paused(self, paused):
        if type(paused) is not bool:
            raise MarketError('invalid_pause')
        with psycopg.connect(self.store.dsn) as conn:
            conn.execute('UPDATE market_private.workflows SET paused=%s WHERE workspace=%s', (paused, self.workspace))

    def _claim(self, job_id, listing_id, scheduled_for):
        owner = uuid4().hex
        now = self.clock()
        with psycopg.connect(self.store.dsn, row_factory=dict_row) as conn:
            control = conn.execute('SELECT paused FROM market_private.workflows WHERE workspace=%s FOR UPDATE', (self.workspace,)).fetchone()
            if control['paused']:
                raise MarketError('paused')
            conn.execute("INSERT INTO market_private.runs(workspace,id,listing_id,scheduled_for,status) VALUES (%s,%s,%s,%s,'queued') ON CONFLICT DO NOTHING",
                         (self.workspace, job_id, listing_id, scheduled_for))
            row = conn.execute('SELECT * FROM market_private.runs WHERE workspace=%s AND id=%s FOR UPDATE', (self.workspace, job_id)).fetchone()
            if row['status'] == 'completed':
                return None
            if row['status'] == 'running' and row['lease_until'] > now:
                raise MarketError('run_in_progress')
            if row['status'] == 'failed' and (row['error'] != 'fixture_peer_unavailable' or row['attempts'] >= 3):
                raise MarketError('run_failed')
            # Retry clears the current error, so retain the prior dispatch outcome.
            result = row['result']
            if row['error'] == 'fixture_peer_unavailable' and row['completed_at']:
                result = dict(result or {}, last_dispatch={'status': 'failed', 'at': row['completed_at'].isoformat()})
            conn.execute("UPDATE market_private.runs SET status='running',owner=%s,lease_until=%s,error=NULL,result=%s,attempts=attempts+1 WHERE workspace=%s AND id=%s",
                         (owner, now + timedelta(seconds=120), Jsonb(result) if result is not None else None, self.workspace, job_id))
        return owner

    def _result(self, listing_id, request_id):
        with psycopg.connect(self.store.dsn, row_factory=dict_row) as conn:
            persisted = conn.execute('SELECT request FROM market_private.runs WHERE workspace=%s AND id=%s', (self.workspace, request_id)).fetchone()['request']
        if persisted is not None:
            request = Request.model_validate(persisted)
        else:
            request = self._new_request(listing_id, request_id)
            with psycopg.connect(self.store.dsn) as conn:
                conn.execute('UPDATE market_private.runs SET request=%s WHERE workspace=%s AND id=%s AND request IS NULL',
                             (Jsonb(request.model_dump(mode='json')), self.workspace, request_id))
        # Business idempotency remains authoritative even if a worker dies after a
        # tool succeeds but before its execution checkpoint or job receipt commits.
        listing_input = self.session.read_listing(listing_id)
        bundle_input = self.session.bundle
        scenario_time = self.clock()
        with self._checkpoint_connection() as conn:
            result = run_agent(self.session, ControlledModel(), request,
                               checkpointer=PostgresSaver(conn), thread_id=self.workspace + ':' + request_id)
        peer_dispatched = False
        if result.mandate and self.peer:
            if self.state()['paused']:
                raise MarketError('paused')
            self.peer(result)
            peer_dispatched = True
        from .evidence import valuation_scenarios

        output = result.model_dump(mode='json')
        if peer_dispatched:
            output['peer_dispatched'] = True
        if result.mandate:
            output['mandate'] = self.session.current_mandate(result.mandate.id).model_dump(mode='json')
        if result.assessment and self.session.read_listing(listing_id) == listing_input:
            scenarios = valuation_scenarios(listing_input, bundle_input.evidence,
                                             bundle_input.assumptions, bundle_input.policy, scenario_time)
            comparison = {'id', 'version', 'expires_at'}
            if scenarios.assessment.model_dump(exclude=comparison) == result.assessment.model_dump(exclude=comparison):
                output['scenarios'] = scenarios.model_copy(update={'assessment': result.assessment}).model_dump(mode='json')
        return output

    def _new_request(self, listing_id, request_id):
        snapshot = self.session.snapshot()
        listing = next((x for x in snapshot['listings'] if x['id'] == listing_id), None)
        if listing is None:
            raise MarketError('record_not_found')
        assessment = next((x for x in snapshot['assessments'] if x['listing_id'] == listing_id), None)
        # Cached request identity is stable across worker retries and restarts.
        cached = self.session.bundle
        return Request(request_id=request_id, operation='assess_opportunity',
                          correlation_id=listing_id, policy_version=cached.policy.version,
                          assessment_version=assessment['version'] if assessment else 0,
                          conversation_version=snapshot.get('conversation_versions', {}).get(listing_id, 0),
                          expires_at=self.clock() + timedelta(minutes=15),
                          evidence_ids=tuple(e.id for e in cached.evidence))

    def assess(self, listing_id, *, job_id=None):
        listing = self.session.read_listing(listing_id)
        if job_id is None:
            assessment = next((a for a in self.session.snapshot()['assessments'] if a['listing_id'] == listing_id), None)
            generation = 0 if assessment is None else assessment['version'] - int(datetime.fromisoformat(assessment['expires_at'].replace('Z', '+00:00')) > self.clock())
            key = f'{listing_id}:{listing.version}:{self.session.bundle.policy.version}:{generation}'
            job_id = 'manual-' + hashlib.sha256(key.encode()).hexdigest()[:32]
        owner = self._claim(job_id, listing_id, self.clock())
        if owner is None:
            with psycopg.connect(self.store.dsn, row_factory=dict_row) as conn:
                result = conn.execute('SELECT result FROM market_private.runs WHERE workspace=%s AND id=%s', (self.workspace, job_id)).fetchone()['result']
            if result and result.get('mandate'):
                result['mandate'] = self.session.current_mandate(result['mandate']['id']).model_dump(mode='json')
            return result
        try:
            result = self._result(listing_id, job_id)
        except Exception as exc:
            code = exc.code if isinstance(exc, MarketError) else 'run_failed'
            with psycopg.connect(self.store.dsn) as conn:
                conn.execute("UPDATE market_private.runs SET status=%s,error=%s,completed_at=%s,lease_until=NULL WHERE workspace=%s AND id=%s AND owner=%s",
                             ('queued' if code == 'paused' else 'failed', code, None if code == 'paused' else self.clock(), self.workspace, job_id, owner))
            raise MarketError(code) from None
        with psycopg.connect(self.store.dsn, row_factory=dict_row) as conn:
            recorded = conn.execute("UPDATE market_private.runs SET status='completed',completed_at=%s,lease_until=NULL,result=COALESCE(result,'{}'::jsonb) || %s WHERE workspace=%s AND id=%s AND owner=%s RETURNING result",
                                    (self.clock(), Jsonb(result), self.workspace, job_id, owner)).fetchone()
        return recorded['result'] if recorded else result

    def run_due(self):
        now = self.clock()
        with psycopg.connect(self.store.dsn, row_factory=dict_row) as conn:
            control = conn.execute('SELECT * FROM market_private.workflows WHERE workspace=%s FOR UPDATE', (self.workspace,)).fetchone()
            if control['paused']:
                return 0
            slot, _ = _schedule_slots(control['schedule']['times'], now)
            if slot is not None and (control['last_slot'] is None or slot > control['last_slot']):
                for listing in self.session.snapshot()['listings']:
                    key = 'schedule-' + hashlib.sha256((slot.isoformat() + listing['id']).encode()).hexdigest()[:32]
                    conn.execute("INSERT INTO market_private.runs(workspace,id,listing_id,scheduled_for,status) VALUES (%s,%s,%s,%s,'queued') ON CONFLICT DO NOTHING",
                                 (self.workspace, key, listing['id'], slot))
                conn.execute('UPDATE market_private.workflows SET last_slot=%s WHERE workspace=%s', (slot, self.workspace))
            pending = conn.execute("SELECT id,listing_id FROM market_private.runs WHERE workspace=%s AND (status='queued' OR (status='running' AND lease_until<=%s) OR (status='failed' AND error='fixture_peer_unavailable' AND attempts<3)) ORDER BY scheduled_for LIMIT 100", (self.workspace, now)).fetchall()
        count = 0
        for job in pending:
            try:
                self.assess(job['listing_id'], job_id=job['id'])
                count += 1
            except MarketError as exc:
                if exc.code not in ('paused', 'run_in_progress', 'run_failed'):
                    raise
        return count
