import json
from datetime import datetime, timezone
from pathlib import Path
import pytest


@pytest.fixture
def now():
    return datetime(2026, 10, 30, 4, tzinfo=timezone.utc)


@pytest.fixture
def raw():
    return json.loads(
        (
            Path(__file__).parents[1] / "src/pokemon_market/fixtures/qualified.json"
        ).read_text()
    )


@pytest.fixture
def bundle(raw):
    from pokemon_market.contracts import FixtureBundle

    return FixtureBundle.model_validate(raw)


@pytest.fixture
def qualified_request(now):
    from pokemon_market.contracts import Request

    return Request(
        request_id="request-1",
        operation="assess_opportunity",
        correlation_id="listing-1",
        policy_version="policy-1",
        assessment_version=0,
        conversation_version=0,
        expires_at="2026-10-30T04:15:00Z",
        evidence_ids=["e1", "e2"],
    )


@pytest.fixture
def session(bundle, now):
    from pokemon_market.session import MarketSession

    return MarketSession(bundle, clock=lambda: now)
