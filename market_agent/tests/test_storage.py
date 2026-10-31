"""Real disposable PostgreSQL acceptance tests; never point at production."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest
from pokemon_market.contracts import FixtureBundle, Listing, MarketError, Request


def request(base, **updates):
    return Request.model_validate(base.model_dump(mode="json") | updates)


def issue(session, base):
    assessment = session.handle(base).assessment
    return session.handle(request(base, request_id=base.request_id + "-mandate",
                                  operation="issue_mandate", assessment_version=assessment.version))


@pytest.fixture
def dsn():
    value = os.environ.get("MARKET_TEST_DSN")
    if not value:
        pytest.skip("set MARKET_TEST_DSN to a disposable PostgreSQL database")
    return value


@pytest.fixture
def store(dsn):
    from pokemon_market.storage import PostgresMarketStore

    result = PostgresMarketStore(dsn)
    result.setup()
    return result


@pytest.fixture
def seed(bundle):
    return FixtureBundle.model_validate(bundle.model_dump(mode="json") | {"session_id": uuid4().hex})


def test_restart_replays_results_and_rejects_conflicting_requests(seed, now, qualified_request, dsn):
    from pokemon_market.storage import PostgresMarketStore

    store = PostgresMarketStore(dsn)
    store.setup()
    store.create(seed)
    assert store.dsn == dsn
    first = issue(store.session(seed.session_id, clock=lambda: now), qualified_request)
    restarted = PostgresMarketStore(dsn).session(seed.session_id, clock=lambda: now)
    assert restarted.handle(request(qualified_request, request_id="request-1-mandate",
                                     operation="issue_mandate", assessment_version=1)) == first
    assert restarted.reserved_exposure == Decimal("85.00")
    with pytest.raises(MarketError, match="request_conflict"):
        restarted.handle(request(qualified_request, evidence_ids=["e1"]))
    assert restarted.current_mandate(first.mandate.id).status == "active"
    assert dsn not in json.dumps(restarted.snapshot())


def test_seed_identity_is_immutable_and_create_does_not_reset_state(store, seed, now, qualified_request):
    store.create(seed)
    session = store.session(seed.session_id, clock=lambda: now)
    issue(session, qualified_request)
    store.create(seed)
    assert session.reserved_exposure == Decimal("85.00")
    changed = FixtureBundle.model_validate(seed.model_dump(mode="json") | {"existing_soft_exposure": "1.00"})
    with pytest.raises(MarketError, match="session_conflict"):
        store.create(changed)
    with pytest.raises(MarketError, match="record_not_found"):
        store.session("missing").read_listing("listing-1")


def test_concurrent_instances_share_exposure_and_idempotency(store, seed, now, qualified_request, dsn):
    from pokemon_market.storage import PostgresMarketStore

    data = seed.model_dump(mode="json")
    data["listings"].append(dict(data["listings"][0], id="listing-2", seller_id="seller-2"))
    store.create(FixtureBundle.model_validate(data))

    def run(number):
        session = PostgresMarketStore(dsn).session(seed.session_id, clock=lambda: now)
        return issue(session, request(qualified_request, request_id=f"r-{number}", correlation_id=f"listing-{number}"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, [1, 2]))
    assert sorted(m.mandate.ceiling for m in results) == [Decimal("60"), Decimal("80")]
    assert store.session(seed.session_id, clock=lambda: now).reserved_exposure == Decimal("150")
    with ThreadPoolExecutor(max_workers=2) as pool:
        replay = list(pool.map(run, [1, 1]))
    assert replay[0] == replay[1] == results[0]


def test_fresh_reads_observe_listing_revocation_and_expiry(store, seed, now, qualified_request):
    store.create(seed)
    reader = store.session(seed.session_id, clock=lambda: now)
    writer = store.session(seed.session_id, clock=lambda: now)
    mandate = issue(writer, qualified_request).mandate
    listing = Listing.model_validate(writer.read_listing("listing-1").model_dump(mode="json") | {"version": 2, "quantity": 2})
    writer.ingest_listing(listing)
    assert reader.read_listing("listing-1").quantity == 2
    assert reader.current_mandate(mandate.id).status == "revoked"
    assert reader.reserved_exposure == 0
    snapshot = reader.snapshot()
    assert snapshot["listings"][0]["quantity"] == 2
    assert snapshot["mandates"][0]["status"] == "revoked"
    assert snapshot["inventory"]["units"] == []

    another = FixtureBundle.model_validate(seed.model_dump(mode="json") | {"session_id": uuid4().hex})
    store.create(another)
    mandate = issue(store.session(another.session_id, clock=lambda: now), qualified_request).mandate
    late = store.session(another.session_id, clock=lambda: mandate.expires_at)
    assert late.current_mandate(mandate.id).status == "expired"
    assert late.reserved_exposure == 0
    assert store.session(another.session_id, clock=lambda: now).current_mandate(mandate.id).status == "expired"


def test_expected_failures_commit_revocation_and_cache_failure(store, seed, now, qualified_request, monkeypatch):
    import pokemon_market.session as module

    store.create(seed)
    session = store.session(seed.session_id, clock=lambda: now)
    mandate = issue(session, qualified_request).mandate
    change = request(qualified_request, request_id="change", operation="reassess_opportunity",
                     assessment_version=1, changes={"price": "70.00"})
    original = module.assess

    def unavailable(*args, **kwargs):
        raise MarketError("evidence_unavailable")

    monkeypatch.setattr(module, "assess", unavailable)
    with pytest.raises(MarketError, match="evidence_unavailable"):
        session.handle(change)
    monkeypatch.setattr(module, "assess", original)
    restarted = store.session(seed.session_id, clock=lambda: now)
    with pytest.raises(MarketError, match="evidence_unavailable"):
        restarted.handle(change)
    assert restarted.snapshot()["conversation_versions"] == {"listing-1": 1}
    assert restarted.read_listing("listing-1").asking_price == Decimal("70.00")
    assert restarted.current_mandate(mandate.id).status == "revoked"
    assert restarted.reserved_exposure == 0


def test_unexpected_failures_rollback_mutation_and_request_cache(store, seed, now, qualified_request, monkeypatch):
    import pokemon_market.session as module

    store.create(seed)
    session = store.session(seed.session_id, clock=lambda: now)
    mandate = issue(session, qualified_request).mandate
    change = request(qualified_request, request_id="change", operation="reassess_opportunity",
                     assessment_version=1, changes={"price": "70.00"})
    original = module.assess

    def broken(*args, **kwargs):
        raise RuntimeError("calculation failed")

    monkeypatch.setattr(module, "assess", broken)
    with pytest.raises(RuntimeError, match="calculation failed"):
        session.handle(change)
    assert session.current_mandate(mandate.id).status == "active"
    assert session.read_listing("listing-1").asking_price == Decimal("75.00")
    monkeypatch.setattr(module, "assess", original)
    assert session.handle(change).assessment.version == 2


def test_private_schema_has_no_anonymous_grants(store, dsn):
    with psycopg.connect(dsn) as conn:
        schema = conn.execute("SELECT nspacl FROM pg_namespace WHERE nspname = 'market_private'").fetchone()[0]
        table = conn.execute("SELECT relacl FROM pg_class WHERE oid='market_private.sessions'::regclass").fetchone()[0]
    assert not any(grant.startswith("=") for grant in (schema or []))
    assert not any(grant.startswith("=") for grant in (table or []))


def test_checkpoint_graph_is_separate_from_business_state(store, seed, now, qualified_request, dsn):
    from langgraph.checkpoint.postgres import PostgresSaver
    from pokemon_market.controlled import ControlledModel
    from pokemon_market.harness import run_agent

    store.create(seed)
    with PostgresSaver.from_conn_string(dsn) as checkpoints:
        checkpoints.setup()
        result = run_agent(store.session(seed.session_id, clock=lambda: now), ControlledModel(),
                           qualified_request, checkpointer=checkpoints)
        config = {"configurable": {"thread_id": seed.session_id}}
        assert checkpoints.get_tuple(config) is not None
        repeated = run_agent(store.session(seed.session_id, clock=lambda: now), ControlledModel(),
                             request(qualified_request, request_id="next-run", assessment_version=1),
                             checkpointer=checkpoints)
        assert repeated.request_id != result.request_id
        assert repeated.mandate.id == result.mandate.id
    assert result.mandate.ceiling == Decimal("80")
    assert store.session(seed.session_id, clock=lambda: now).reserved_exposure == Decimal("85")


def test_exhausted_reassessment_revocation_survives_restart(store, seed, now, qualified_request):
    data = seed.model_dump(mode="json")
    data["policy"]["max_reassessments"] = 1
    store.create(FixtureBundle.model_validate(data))
    session = store.session(seed.session_id, clock=lambda: now)
    issue(session, qualified_request)
    session.handle(request(qualified_request, request_id="round-1", operation="reassess_opportunity",
                           assessment_version=1, changes={"price": "70.00"}))
    current = request(qualified_request, request_id="current", operation="issue_mandate",
                      assessment_version=2, conversation_version=1)
    mandate = session.handle(current).mandate
    exhausted = request(current, request_id="over-limit", operation="reassess_opportunity", changes={"quantity": 2})
    with pytest.raises(MarketError, match="reassessment_limit"):
        session.handle(exhausted)
    restarted = store.session(seed.session_id, clock=lambda: now)
    with pytest.raises(MarketError, match="reassessment_limit"):
        restarted.handle(exhausted)
    assert restarted.current_mandate(mandate.id).status == "revoked"
    assert restarted.reserved_exposure == 0
    assert restarted.read_listing("listing-1").quantity == 2


def test_database_write_failure_cannot_leave_mutated_memory(store, seed, now, qualified_request, dsn):
    from psycopg import sql

    store.create(seed)
    session = store.session(seed.session_id, clock=lambda: now)
    mandate = issue(session, qualified_request).mandate
    constraint = sql.Identifier("test_" + uuid4().hex)
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL("ALTER TABLE market_private.sessions ADD CONSTRAINT {} "
                             "CHECK (session_id <> {} OR state #>> '{{listings,listing-1,asking_price}}' = '75.00') NOT VALID")
                     .format(constraint, sql.Literal(seed.session_id)))
    change = request(qualified_request, request_id="write-failure", operation="reassess_opportunity",
                     assessment_version=1, changes={"price": "70.00"})
    try:
        with pytest.raises(psycopg.errors.CheckViolation):
            session.handle(change)
        assert session.read_listing("listing-1").asking_price == Decimal("75.00")
        assert session.current_mandate(mandate.id).status == "active"
    finally:
        with psycopg.connect(dsn) as conn:
            conn.execute(sql.SQL("ALTER TABLE market_private.sessions DROP CONSTRAINT {}").format(constraint))
    assert session.handle(change).assessment.version == 2


def test_inventory_seed_survives_recovery_and_conflicts_are_rejected(store, seed, now):
    from pathlib import Path
    from pokemon_market.contracts import InventoryBundle

    inventory = InventoryBundle.model_validate_json(
        (Path(__file__).parents[1] / "src/pokemon_market/fixtures/inventory.json").read_text())
    store.create(seed, inventory)
    recovered = store.session(seed.session_id, clock=lambda: now)
    assert recovered.inventory_summary().unsold_cost_basis == Decimal("85.00")
    assert recovered.read_owned_unit(inventory.units[0].id).id == inventory.units[0].id
    assert recovered.read_evidence(("e1",))[0].id == "e1"
    with pytest.raises(MarketError, match="session_conflict"):
        store.create(seed)
    json.dumps(recovered.snapshot())


def test_invalid_stored_state_fails_closed(store, seed, now, qualified_request, dsn):
    from pydantic import ValidationError

    store.create(seed)
    with psycopg.connect(dsn) as conn:
        conn.execute("UPDATE market_private.sessions SET state=jsonb_set(state, '{rounds}', %s) WHERE session_id=%s",
                     (psycopg.types.json.Jsonb({"listing-1": -1}), seed.session_id))
    with pytest.raises(ValidationError):
        store.session(seed.session_id, clock=lambda: now).handle(qualified_request)


def test_bad_connection_never_exposes_dsn():
    from pokemon_market.storage import PostgresMarketStore

    with pytest.raises(MarketError, match="storage_unavailable") as failure:
        PostgresMarketStore("SECRET_DSN_SENTINEL").setup()
    assert "SECRET_DSN_SENTINEL" not in str(failure.value)


def test_setup_revokes_supabase_anonymous_roles(store, dsn):
    from psycopg import sql

    created = []
    try:
        with psycopg.connect(dsn) as conn:
            for role in ("anon", "authenticated"):
                if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
                    conn.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
                    created.append(role)
                conn.execute(sql.SQL("GRANT USAGE ON SCHEMA market_private TO {}").format(sql.Identifier(role)))
                conn.execute(sql.SQL("GRANT SELECT ON market_private.sessions TO {}").format(sql.Identifier(role)))
        store.setup()
        with psycopg.connect(dsn) as conn:
            for role in ("anon", "authenticated"):
                assert conn.execute("SELECT has_schema_privilege(%s,'market_private','USAGE')", (role,)).fetchone() == (False,)
                assert conn.execute("SELECT has_table_privilege(%s,'market_private.sessions','SELECT')", (role,)).fetchone() == (False,)
    finally:
        with psycopg.connect(dsn) as conn:
            for role in created:
                conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
