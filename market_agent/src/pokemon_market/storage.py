"""Private PostgreSQL state for simulated Market work; no live financial authority."""

from datetime import datetime, timezone
from threading import RLock
from typing import Literal

import psycopg
from psycopg.types.json import Jsonb
from pydantic import Field

from .contracts import (
    Artifact,
    Assessment,
    Contract,
    FixtureBundle,
    InventoryBundle,
    Listing,
    Mandate,
    MarketError,
    Text,
    Version,
)
from .session import MarketSession


class _State(Contract):
    schema_version: Literal[1] = 1
    listings: dict[Text, Listing]
    assessments: dict[Text, Assessment] = Field(default_factory=dict)
    mandates: dict[Text, Mandate] = Field(default_factory=dict)
    requests: dict[Text, tuple[str, Artifact | str]] = Field(default_factory=dict)
    conversation: dict[Text, Version] = Field(default_factory=dict)
    rounds: dict[Text, Version] = Field(default_factory=dict)
    dirty: set[Text] = Field(default_factory=set)

    @classmethod
    def capture(cls, session):
        state = cls(**{
            name: getattr(session, "_" + name)
            for name in cls.model_fields if name != "schema_version"
        })
        return cls.model_validate_json(state.model_dump_json())

    def restore(self, session):
        listing_ids = set(session._listings)
        if (
            set(self.listings) != listing_ids
            or any(key != value.id for key, value in self.listings.items())
            or any(key != value.listing_id for key, value in self.assessments.items())
            or not set(self.assessments) <= listing_ids
            or any(
                key != value.id or value.listing_id not in listing_ids
                for key, value in self.mandates.items()
            )
            or not (set(self.conversation) | set(self.rounds) | self.dirty) <= listing_ids
        ):
            raise MarketError("invalid_stored_state")
        for name in type(self).model_fields:
            if name != "schema_version":
                setattr(session, "_" + name, getattr(self, name))


class PostgresMarketStore:
    def __init__(self, dsn):
        self._dsn = dsn

    @property
    def dsn(self):
        """Server-side connection configuration; never include in operator responses."""
        return self._dsn

    def _connect(self):
        try:
            return psycopg.connect(self._dsn, connect_timeout=5)
        except psycopg.Error:
            raise MarketError("storage_unavailable") from None

    def setup(self):
        """Explicit, idempotent migration; call only on the chosen development DB."""
        with self._connect() as connection:
            connection.execute("""
                CREATE SCHEMA IF NOT EXISTS market_private;
                REVOKE ALL ON SCHEMA market_private FROM PUBLIC;
                CREATE TABLE IF NOT EXISTS market_private.sessions (
                    session_id text PRIMARY KEY,
                    bundle jsonb NOT NULL,
                    inventory jsonb NOT NULL,
                    state jsonb NOT NULL
                );
                REVOKE ALL ON ALL TABLES IN SCHEMA market_private FROM PUBLIC;
                ALTER DEFAULT PRIVILEGES IN SCHEMA market_private
                    REVOKE ALL ON TABLES FROM PUBLIC;
                DO $$ BEGIN
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                        REVOKE ALL ON SCHEMA market_private FROM anon;
                        REVOKE ALL ON ALL TABLES IN SCHEMA market_private FROM anon;
                    END IF;
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                        REVOKE ALL ON SCHEMA market_private FROM authenticated;
                        REVOKE ALL ON ALL TABLES IN SCHEMA market_private FROM authenticated;
                    END IF;
                END $$;
            """)

    def create(self, bundle, inventory=None):
        bundle = FixtureBundle.model_validate_json(bundle.model_dump_json())
        inventory = (
            InventoryBundle.model_validate_json(inventory.model_dump_json())
            if inventory is not None else InventoryBundle(units=(), outcomes=())
        )
        session = MarketSession(
            bundle, inventory=inventory, clock=lambda: bundle.policy.created_at
        )
        seed = bundle.model_dump(mode="json")
        stock = inventory.model_dump(mode="json")
        state = _State.capture(session).model_dump(mode="json")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO market_private.sessions (session_id,bundle,inventory,state) "
                "VALUES (%s,%s,%s,%s) ON CONFLICT (session_id) DO NOTHING",
                (bundle.session_id, Jsonb(seed), Jsonb(stock), Jsonb(state)),
            )
            row = connection.execute(
                "SELECT bundle,inventory FROM market_private.sessions "
                "WHERE session_id=%s FOR UPDATE",
                (bundle.session_id,),
            ).fetchone()
            if row != (seed, stock):
                raise MarketError("session_conflict")

    def session(self, session_id, *, clock=None):
        return PostgresMarketSession(
            self, session_id, clock=clock or (lambda: datetime.now(timezone.utc))
        )


class PostgresMarketSession:
    """Hydrate each operation under one workspace row lock; never retain stale state."""

    def __init__(self, store, session_id, *, clock):
        self._store = store
        self._session_id = session_id
        self.clock = clock
        self._lock = RLock()

    def _call(self, action):
        failure = None
        with self._lock, self._store._connect() as connection:
            row = connection.execute(
                "SELECT bundle,inventory,state FROM market_private.sessions "
                "WHERE session_id=%s FOR UPDATE",
                (self._session_id,),
            ).fetchone()
            if row is None:
                raise MarketError("record_not_found")
            session = MarketSession(
                FixtureBundle.model_validate(row[0]),
                inventory=InventoryBundle.model_validate(row[1]),
                clock=self.clock,
            )
            if session.bundle.session_id != self._session_id:
                raise MarketError("invalid_stored_state")
            _State.model_validate(row[2]).restore(session)
            try:
                result = action(session)
            except MarketError as error:
                # Expected failures can revoke stale authority and cache their result.
                failure = error
            updated = _State.capture(session).model_dump(mode="json")
            if updated != row[2]:
                connection.execute(
                    "UPDATE market_private.sessions SET state=%s WHERE session_id=%s",
                    (Jsonb(updated), self._session_id),
                )
        if failure is not None:
            raise failure
        return result

    @property
    def bundle(self):
        return self._call(lambda session: session.bundle)

    @property
    def inventory(self):
        return self._call(lambda session: session.inventory)

    @property
    def reserved_exposure(self):
        return self._call(lambda session: session.reserved_exposure)

    def handle(self, request):
        return self._call(lambda session: session.handle(request))

    def read_listing(self, listing_id):
        return self._call(lambda session: session.read_listing(listing_id))

    def read_evidence(self, evidence_ids):
        return self._call(lambda session: session.read_evidence(evidence_ids))

    def ingest_listing(self, listing):
        return self._call(lambda session: session.ingest_listing(listing))

    def current_mandate(self, mandate_id):
        return self._call(lambda session: session.current_mandate(mandate_id))

    def read_owned_unit(self, unit_id):
        return self._call(lambda session: session.read_owned_unit(unit_id))

    def inventory_summary(self):
        return self._call(lambda session: session.inventory_summary())

    def snapshot(self):
        def read(session):
            exposure = session.reserved_exposure
            return {
                "session_id": session.bundle.session_id,
                "mode": "simulation",
                "policy": session.bundle.policy.model_dump(mode="json"),
                "existing_soft_exposure": format(
                    session.bundle.existing_soft_exposure, ".2f"
                ),
                "reserved_exposure": format(exposure, ".2f"),
                "conversation_versions": dict(session._conversation),
                "listings": [
                    item.model_dump(mode="json") for item in session._listings.values()
                ],
                "assessments": [
                    item.model_dump(mode="json") for item in session._assessments.values()
                ],
                "mandates": [
                    item.model_dump(mode="json") for item in session._mandates.values()
                ],
                "inventory": session.inventory_summary().model_dump(mode="json"),
            }

        return self._call(read)
