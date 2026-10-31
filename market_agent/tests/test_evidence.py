"""Recorded reference responses and deterministic scenario acceptance checks."""

import copy
import json
import threading
import time
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from pydantic import ValidationError

from pokemon_market import evidence as evidence_tools
from pokemon_market.contracts import Evidence, FixtureBundle, MarketError


@pytest.fixture
def reference():
    return {
        "schemaVersion": 1, "mode": "reference", "source": "TCGdex",
        "card": {"id": "base1-4", "name": "Charizard"},
        "fetchedAt": "2026-10-30T03:45:00Z",
        "quotes": [
            {"provider": "cardmarket", "currency": "EUR", "variant": "Reference (see metric)",
             "updatedAt": "2026-10-30T03:00:00Z", "freshness": "current", "prices": {"avg": 123.45, "trend": 125}},
            {"provider": "tcgplayer", "currency": "USD", "variant": "holofoil",
             "updatedAt": "2026-10-27T03:00:00Z", "freshness": "stale", "prices": {"marketPrice": 140.51}},
            {"provider": "tcgplayer", "currency": "USD", "variant": "normal",
             "updatedAt": None, "freshness": "unknown", "prices": {"lowPrice": 100}},
        ],
    }


@contextmanager
def backend(body, *, status=200, headers=None, delay=0):
    paths = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            paths.append(self.path)
            time.sleep(delay)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            for key, value in (headers or {}).items():
                self.send_header(key, str(value))
            self.end_headers()
            try:
                self.wfile.write(body if isinstance(body, bytes) else json.dumps(body).encode())
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", paths
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def scenarios(raw, now):
    b = FixtureBundle.model_validate(raw)
    return evidence_tools.valuation_scenarios(b.listings[0], b.evidence, b.assumptions, b.policy, now)


def test_reference_preserves_original_provider_currency_observation_and_classification(reference, now):
    with backend(reference) as (url, paths):
        snapshot = evidence_tools.load_reference("base1-4", base_url=url, now=now)
    assert paths == ["/api/market/cards/base1-4"]
    assert snapshot.card.id == "base1-4"
    assert (snapshot.mode, snapshot.source) == ("reference", "TCGdex")
    assert snapshot.fetched_at.isoformat() == "2026-10-30T03:45:00+00:00"
    quote = snapshot.quotes[0]
    assert (quote.provider, quote.currency, quote.freshness) == ("cardmarket", "EUR", "current")
    assert quote.updated_at.isoformat() == "2026-10-30T03:00:00+00:00"
    assert quote.prices == {"avg": Decimal("123.45"), "trend": Decimal("125")}
    assert snapshot.quotes[1].freshness == "stale"
    assert snapshot.quotes[2].updated_at is None
    with pytest.raises(ValidationError):
        Evidence.model_validate(snapshot.model_dump())


@pytest.mark.parametrize("url", [
    "https://127.0.0.1:8000", "http://example.com", "http://localhost:8000", "http://127.0.0.1.evil.com",
    "http://0.0.0.0", "http://169.254.169.254", "http://user:secret@127.0.0.1",
    "http://127.0.0.1/path", "http://127.0.0.1?x=1", "http://127.0.0.1#frag", "http://127.0.0.1:99999",
])
def test_reference_rejects_untrusted_base_urls_before_network(url, now):
    with pytest.raises(MarketError, match="untrusted_reference_backend"):
        evidence_tools.load_reference("base1-4", base_url=url, now=now)


@pytest.mark.parametrize("card_id", ["../secret", "base1-4?x=1", "base1-4/foo", "base1-%34", "a" * 81, "", 123])
def test_reference_rejects_unbounded_or_path_injecting_card_ids(card_id, now):
    with pytest.raises(MarketError, match="invalid_card_id"):
        evidence_tools.load_reference(card_id, base_url="http://127.0.0.1:1", now=now)


@pytest.mark.parametrize("mutation,reason", [
    (lambda r: r["card"].update(id="base1-5"), "reference_identity_mismatch"),
    (lambda r: r.update(fetchedAt="2026-10-30T04:00:01Z"), "future_reference"),
    (lambda r: r.update(fetchedAt="2026-10-30T02:59:59Z"), "stale_reference"),
    (lambda r: r["quotes"][0].update(updatedAt="2026-10-30T04:00:01Z"), "future_reference"),
    (lambda r: r["quotes"][1].update(freshness="current"), "invalid_reference_freshness"),
    (lambda r: r["quotes"][2].update(freshness="current"), "invalid_reference_freshness"),
    (lambda r: r.update(mode="completed_sale"), "invalid_reference"),
    (lambda r: r["quotes"][0].update(currency="SGD"), "invalid_reference"),
    (lambda r: r["quotes"][0].update(currency="USD"), "invalid_reference"),
    (lambda r: r["quotes"][0].update(completed=True), "invalid_reference"),
    (lambda r: r["quotes"][0]["prices"].update(marketPrice=100), "invalid_reference"),
    (lambda r: r["quotes"][0]["prices"].update(avg=-1), "invalid_reference"),
    (lambda r: r["quotes"][0]["prices"].update(avg=True), "invalid_reference"),
    (lambda r: r["quotes"][0]["prices"].update(avg="1.00"), "invalid_reference"),
    (lambda r: r["quotes"][0]["prices"].update(avg=1e20), "invalid_reference"),
    (lambda r: r["quotes"][0]["prices"].update(avg=float("nan")), "invalid_reference"),
    (lambda r: r.update(quotes=r["quotes"] * 12), "invalid_reference"),
])
def test_reference_rejects_invalid_identity_timestamps_and_price_authority(reference, now, mutation, reason):
    mutation(reference)
    with backend(reference) as (url, _):
        with pytest.raises(MarketError, match=reason):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)


def test_reference_does_not_follow_redirects(reference, now):
    with backend(reference, status=302, headers={"Location": "http://169.254.169.254/"}) as (url, paths):
        with pytest.raises(MarketError, match="reference_unavailable"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)
    assert paths == ["/api/market/cards/base1-4"]


@pytest.mark.parametrize("body,headers", [
    (b"{}", {"Content-Length": 1048577}), (b" " * 1048577, {}), (b"{broken", {}),
    (b'{"schemaVersion":1,"schemaVersion":1}', {}),
])
def test_reference_rejects_oversized_or_malformed_json(body, headers, now):
    with backend(body, headers=headers) as (url, _):
        with pytest.raises(MarketError, match="invalid_reference"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)


def test_reference_times_out_without_leaking_connection_details(reference, now, monkeypatch):
    monkeypatch.setattr(evidence_tools, "REFERENCE_TIMEOUT_SECONDS", 0.05)
    with backend(reference, delay=0.15) as (url, _):
        with pytest.raises(MarketError, match="^reference_timeout$"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)


def test_min_median_max_scenarios_preserve_conservative_authority_and_money_strings(raw, now):
    raw["evidence"].append(dict(raw["evidence"][0], id="e3", transaction_id="t3", gross_amount="160.00"))
    result = scenarios(raw, now)
    data = result.model_dump(mode="json")
    assert result.status == "available" and result.method == "observed_sales"
    assert data["conservative"] == {"gross_resale": "120.00", "net_resale": "105.00", "economic_ceiling": "80.00"}
    assert data["base"] == {"gross_resale": "130.00", "net_resale": "115.00", "economic_ceiling": "90.00"}
    assert data["upside"] == {"gross_resale": "160.00", "net_resale": "145.00", "economic_ceiling": "120.00"}
    assert data["assessment"]["item_ceiling"] == "80.00"
    assert result.evidence_ids == ("e1", "e2", "e3")
    assert result.rounding == "ROUND_FLOOR"


def test_even_median_rounds_down_half_cent_including_negative_economics(raw, now):
    raw["evidence"][0]["gross_amount"] = "30.01"
    raw["evidence"][1]["gross_amount"] = "30.02"
    data = scenarios(raw, now).model_dump(mode="json")
    assert data["base"] == {"gross_resale": "30.01", "net_resale": "15.01", "economic_ceiling": "-9.99"}
    assert data["assessment"]["decision"] == "rejected"
    assert data["assessment"]["item_ceiling"] is None


@pytest.mark.parametrize("field,value", [
    ("basis", "reference"), ("basis", "asking"), ("currency", "USD"), ("currency", "EUR"),
    ("completed", False), ("condition", "damaged"),
    ("observed_at", "2026-10-30T04:00:01Z"), ("observed_at", "2026-10-23T03:59:59Z"),
])
def test_ineligible_observations_never_become_scenarios(raw, now, field, value):
    raw["evidence"][0][field] = value
    result = scenarios(raw, now)
    assert result.status == "unavailable"
    assert result.conservative is None and result.base is None and result.upside is None
    assert result.assessment.item_ceiling is None
    assert result.excluded_evidence_ids == ("e1",)


def test_exact_identity_excludes_reference_from_other_card(raw, now):
    raw["evidence"][0]["card"]["language"] = "ja"
    assert scenarios(raw, now).status == "unavailable"


@pytest.mark.parametrize("field,value", [("card", None), ("currency", "USD"), ("condition", None), ("condition_reviewed", False), ("quantity", 2)])
def test_listing_gates_are_identical_to_assessment(raw, now, field, value):
    raw["listings"][0][field] = value
    result = scenarios(raw, now)
    assert result.status == "unavailable" and result.assessment.item_ceiling is None


def test_distinct_transactions_only_and_deterministic_order(raw, now):
    raw["evidence"].append(dict(raw["evidence"][0], id="e3"))
    result = scenarios(raw, now)
    assert result.evidence_ids == ("e1", "e2")
    assert result.duplicate_evidence_ids == ("e3",)
    assert result.base.gross_resale == Decimal("125.00")
    raw["evidence"].reverse()
    reordered = scenarios(raw, now)
    assert reordered.evidence_ids == result.evidence_ids
    assert reordered.base == result.base
    raw["evidence"] = [raw["evidence"][0], raw["evidence"][2]]
    assert scenarios(raw, now).status == "unavailable"


def test_conflicting_transaction_blocks_all_scenarios(raw, now):
    raw["evidence"][1]["transaction_id"] = "t1"
    result = scenarios(raw, now)
    assert result.status == "unavailable" and result.assessment.reasons == ("conflicting_transaction",)
    assert result.upside is None


def reviewed(raw):
    return dict(id="a1", policy_version="policy-1", card=copy.deepcopy(raw["policy"]["allowed_cards"][0]),
                condition="near_mint", gross_amount="140.00", currency="SGD",
                reviewed_at="2026-10-29T04:00:00Z", expires_at="2026-10-31T04:00:00Z")


def test_reviewed_assumption_has_one_value_and_explicit_metadata(raw, now):
    raw["evidence"] = []
    raw["assumptions"] = [reviewed(raw)]
    result = scenarios(raw, now)
    assert result.status == "available" and result.method == "reviewed_assumption"
    assert result.conservative == result.base == result.upside
    assert result.base.model_dump(mode="json") == {"gross_resale": "140.00", "net_resale": "125.00", "economic_ceiling": "100.00"}
    assert result.assessment.assumption.id == "a1"
    raw["policy"]["allow_assumptions"] = False
    assert scenarios(raw, now).status == "unavailable"


@pytest.mark.parametrize("field,value", [("currency", "USD"), ("policy_version", "old"), ("expires_at", "2026-10-30T04:00:00Z"), ("reviewed_at", "2026-10-30T04:00:01Z")])
def test_assumption_identity_policy_currency_and_freshness_are_required(raw, now, field, value):
    raw["evidence"] = []
    a = reviewed(raw)
    a[field] = value
    raw["assumptions"] = [a]
    assert scenarios(raw, now).status == "unavailable"


def test_assumptions_cannot_raise_sales_scenarios(raw, now):
    raw["assumptions"] = [reviewed(raw)]
    assert scenarios(raw, now).upside.gross_resale == Decimal("130.00")


def test_reference_snapshot_cannot_be_supplied_as_a_sale(raw, now, reference):
    b = FixtureBundle.model_validate(raw)
    snapshot = evidence_tools.ReferenceSnapshot.model_validate(reference)
    with pytest.raises(MarketError, match="invalid_evidence"):
        evidence_tools.valuation_scenarios(b.listings[0], (snapshot,), (), b.policy, now)


def test_naive_clocks_fail_closed(raw, now):
    with pytest.raises(MarketError, match="naive_clock"):
        scenarios(raw, now.replace(tzinfo=None))
    with pytest.raises(MarketError, match="naive_clock"):
        evidence_tools.load_reference("base1-4", base_url="http://127.0.0.1:1", now=now.replace(tzinfo=None))


def test_reference_rejects_numeric_timestamps(reference, now):
    reference["fetchedAt"] = 1793331900
    with backend(reference) as (url, _):
        with pytest.raises(MarketError, match="invalid_reference"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)


def test_reference_rejects_truncated_content_length(reference, now):
    body = json.dumps(reference).encode()
    with backend(body, headers={"Content-Length": len(body) + 10}) as (url, _):
        with pytest.raises(MarketError, match="invalid_reference"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)


def test_reference_rejects_deeply_nested_json(now):
    with backend(b"[" * 10000 + b"]" * 10000) as (url, _):
        with pytest.raises(MarketError, match="invalid_reference"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)


def test_reference_rejects_port_zero(now):
    with pytest.raises(MarketError, match="untrusted_reference_backend"):
        evidence_tools.load_reference("base1-4", base_url="http://127.0.0.1:0", now=now)


def test_reference_rejects_unrepresentable_decimal_exponents(now):
    with backend(b'{"value":1e99999999999999999999999999999999999}') as (url, _):
        with pytest.raises(MarketError, match="invalid_reference"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)


def test_reference_accepts_fetch_and_observation_during_bounded_transport(reference, now):
    reference["fetchedAt"] = (now + timedelta(milliseconds=20)).isoformat()
    reference["quotes"][0]["updatedAt"] = (now + timedelta(milliseconds=10)).isoformat()
    with backend(reference, delay=0.05) as (url, _):
        snapshot = evidence_tools.load_reference("base1-4", base_url=url, now=now)
    assert snapshot.fetched_at == now + timedelta(milliseconds=20)
    assert snapshot.quotes[0].updated_at == now + timedelta(milliseconds=10)


def test_reference_rejects_transport_exceeding_eight_seconds(reference, now, monkeypatch):
    from types import SimpleNamespace

    readings = iter([100.0, 100.0, 100.0, 108.01])
    monkeypatch.setattr(evidence_tools, "time", SimpleNamespace(monotonic=lambda: next(readings)))
    with backend(reference) as (url, _):
        with pytest.raises(MarketError, match="reference_timeout"):
            evidence_tools.load_reference("base1-4", base_url=url, now=now)
